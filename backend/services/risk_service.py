"""Rule-based landslide risk engine (prototype, fully configurable).

Combines live environmental data (Open-Meteo) with curated static
susceptibility factors into a 0-100 risk score, explains WHY each factor
contributed, and maps the score to LOW / MODERATE / HIGH / CRITICAL.

NOTE: weights and thresholds are conceptual starting points, configurable via
environment variables (see utils/config.py). They are NOT scientifically
validated - see docs/DISCLAIMER.md. The trained ML model (ml/) is used by
/api/risk/predict for comparison.
"""
from datetime import datetime, timezone

from services import geo_service
from services.weather_service import get_live_conditions
from utils.config import (
    DISCLAIMER,
    THRESHOLD_CRITICAL,
    THRESHOLD_HIGH,
    THRESHOLD_MODERATE,
    WEIGHTS,
    classify_score,
)

FACTOR_LABELS = {
    "rainfall": "Rainfall",
    "slope": "Slope",
    "soil_moisture": "Soil Moisture",
    "elevation": "Elevation",
    "soil_geology": "Soil / Geology",
    "land_cover": "Land Cover",
    "historical": "Historical Landslides",
    "drainage": "Drainage",
    "road_cutting": "Road Cutting",
}

_LEVEL_RECOMMENDATIONS = {
    "LOW": [
        "No significant landslide warning right now. Normal activities can continue.",
        "During monsoon, keep following weather updates for your area.",
    ],
    "MODERATE": [
        "Stay alert around steep slopes, road cuttings and stream banks.",
        "Avoid digging, cutting or loading slopes during and after rain.",
        "Report fresh cracks or tilting trees/poles to local authorities.",
    ],
    "HIGH": [
        "Avoid unnecessary travel through hilly and landslide-prone routes.",
        "Park vehicles away from steep cuttings and the base of slopes.",
        "Follow local authority advisories and be ready to move if advised.",
    ],
    "CRITICAL": [
        "Avoid all travel through vulnerable slopes and road-cut sections.",
        "Move away from steep slopes, cliff bases and blocked drains.",
        "Follow official evacuation / shelter instructions from authorities immediately.",
    ],
}


def _norm(value, cap: float) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(1.0, float(value) / cap))


def _elevation_score(elev_m) -> float | None:
    """Piecewise-linear terrain exposure score (0-100)."""
    if elev_m is None:
        return None
    points = [(0, 15), (100, 25), (500, 45), (1000, 60), (2000, 80), (3000, 92), (4000, 98)]
    e = max(0.0, float(elev_m))
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if e <= x1:
            return round(y0 + (y1 - y0) * (e - x0) / (x1 - x0), 1)
    return points[-1][1]


def _sm_label(sm: float) -> str:
    if sm < 0.15:
        return "dry"
    if sm < 0.28:
        return "moist"
    if sm < 0.38:
        return "wet"
    return "near-saturated"


def _rainfall_score(conditions: dict):
    """Rainfall factor: blend of current intensity + 24h/72h accumulation."""
    current = conditions.get("precipitation_mm") or 0.0
    r24 = conditions.get("rain_24h_mm") or 0.0
    r72 = conditions.get("rain_72h_mm") or 0.0
    score = 100.0 * (0.35 * _norm(current, 15) + 0.40 * _norm(r24, 80) + 0.25 * _norm(r72, 180))
    return round(score, 1), {"current": round(current, 2), "24h": round(r24, 2), "72h": round(r72, 2)}


def compute_factor_scores(conditions: dict, statics: dict) -> dict:
    """Return {factor: {"score": 0-100, "detail": human explanation}}."""
    state = statics["state"]

    rain_score, rain_vals = _rainfall_score(conditions)
    rainfall = {
        "score": rain_score,
        "detail": (f"Current {rain_vals['current']} mm/h; last 24h {rain_vals['24h']} mm; "
                   f"last 72h {rain_vals['72h']} mm (annual avg here ~{state['annual_rainfall_mm']} mm)"),
    }

    slope_deg = conditions.get("slope_deg")
    if slope_deg is None:
        slope_deg = round(state["road_cutting_score"] / 2.0, 1)  # baseline proxy
        slope_basis = "state baseline (live terrain estimate unavailable)"
    else:
        slope_basis = conditions.get("slope_basis", "DEM estimate")
    slope = {"score": round(min(100.0, slope_deg * 2.8), 1),
             "detail": f"Slope ≈ {slope_deg}° ({slope_basis})"}

    sm = conditions.get("soil_moisture_m3m3")
    if sm is None:
        sm_score = round(min(100.0, 40 + 0.3 * rain_score), 1)
        soil_moisture = {"score": sm_score,
                         "detail": f"Not reported by API — estimated from recent rainfall (score {sm_score}/100)"}
    else:
        sm_score = round(max(0.0, min(100.0, (sm - 0.08) / 0.40 * 100)), 1)
        soil_moisture = {"score": sm_score, "detail": f"Top-soil moisture {sm} m³/m³ ({_sm_label(sm)})"}

    elev_m = conditions.get("elevation_m", statics["elevation_baseline_m"])
    elevation = {"score": _elevation_score(elev_m) or _elevation_score(statics["elevation_baseline_m"]),
                 "detail": f"Elevation ≈ {elev_m} m above sea level"}

    soil_geology = {"score": statics["geology_score"],
                    "detail": f"{statics['geology']} ({state['name']} baseline)"}
    land_cover = {"score": statics["land_cover_score"],
                  "detail": f"{statics['land_cover']} ({state['name']} baseline)"}

    if statics["nearest_hotspot"]:
        hist_detail = (f"Known recurrent landslide zone near {statics['nearest_hotspot']} "
                       f"(~{statics['nearest_hotspot_km']} km away)")
    else:
        hist_detail = f"No recorded hotspot close by; {state['name']} regional baseline used"
    historical = {"score": statics["historical_score"], "detail": hist_detail}

    drainage = {"score": round(min(100.0, 0.55 * statics["drainage_score"]
                                   + 0.30 * rain_score + 0.15 * slope["score"]), 1),
                "detail": "Drainage proxy: state drainage class + recent rainfall + slope"}

    if statics["nearest_road_corridor_km"] is not None:
        road_detail = (f"~{statics['nearest_road_corridor_km']} km from a highway corridor "
                       f"with chronic slope cutting")
    else:
        road_detail = "No road-cutting corridor data nearby"
    road_cutting = {"score": statics["road_cutting_score"], "detail": road_detail}

    return {
        "rainfall": rainfall, "slope": slope, "soil_moisture": soil_moisture,
        "elevation": elevation, "soil_geology": soil_geology, "land_cover": land_cover,
        "historical": historical, "drainage": drainage, "road_cutting": road_cutting,
    }


def _trigger_notes(conditions: dict, factor_scores: dict) -> list[str]:
    """Short human-readable reasons the risk is elevated (for the UI)."""
    notes = []
    r24 = conditions.get("rain_24h_mm") or 0.0
    r72 = conditions.get("rain_72h_mm") or 0.0
    if r24 >= 60:
        notes.append(f"Heavy recent rainfall ({r24} mm in the last 24 hours)")
    elif r72 >= 120:
        notes.append(f"Sustained rainfall ({r72} mm over the last 72 hours)")
    slope_deg = conditions.get("slope_deg")
    if slope_deg is not None and slope_deg >= 25:
        notes.append(f"Steep terrain (~{slope_deg}° slope)")
    sm = conditions.get("soil_moisture_m3m3")
    if sm is not None and sm >= 0.38:
        notes.append(f"Near-saturated soil moisture ({sm} m³/m³)")
    if factor_scores["soil_geology"]["score"] >= 70:
        notes.append("Weak/fragile geological formations in this region")
    if factor_scores["road_cutting"]["score"] >= 60:
        notes.append("Close to road-cut sections prone to slope failure")
    if factor_scores["historical"]["score"] >= 70:
        notes.append("Near known recurrent landslide zones")
    return notes[:4]


def build_warning(location_label: str, state_name: str, score: float, level: str,
                  top_factors: list[str], recommendations: list[str]) -> dict:
    lines = [
        f"⚠️ {level} LANDSLIDE RISK",
        f"Location: {location_label}, {state_name}",
        f"Risk Score: {score}/100",
        "",
        "Main contributing factors:",
        *[f"- {t}" for t in top_factors],
        "",
        "Recommendation:",
        *[f"- {r}" for r in recommendations],
        "",
        ("This is an early-warning indication based on available data — it does NOT mean a "
         "landslide is certain. Always follow official disaster-management advisories."),
    ]
    return {"title": f"{level} Landslide Risk — {location_label}", "message": "\n".join(lines)}


def evaluate(lat: float, lon: float, name: str | None = None,
             state_hint: str | None = None) -> dict:
    """Full analysis pipeline: weather + statics + scoring + explanation."""
    state = geo_service.get_state(state_hint) if state_hint else None
    if state is None:
        state = geo_service.state_for_point(lat, lon)

    statics = geo_service.static_factors(lat, lon, state)
    conditions = get_live_conditions(lat, lon)  # may raise WeatherServiceError
    factor_scores = compute_factor_scores(conditions, statics)

    total_w = sum(WEIGHTS.values()) or 1.0
    contributions = []
    for factor, info in factor_scores.items():
        w = WEIGHTS.get(factor, 0.0)
        contributions.append({
            "factor": factor,
            "label": FACTOR_LABELS[factor],
            "score": info["score"],
            "detail": info["detail"],
            "weight": round(w / total_w * 100.0, 1),
            "contribution": round(info["score"] * w / total_w, 1),
        })
    contributions.sort(key=lambda c: c["contribution"], reverse=True)

    score = round(sum(c["contribution"] for c in contributions), 1)
    level = classify_score(score)
    recommendations = list(_LEVEL_RECOMMENDATIONS[level])
    triggers = _trigger_notes(conditions, factor_scores)
    top_factors = [c["label"] for c in contributions[:3]]
    label = name or state["capital"]

    return {
        "location": {
            "name": label, "state": state["name"], "state_id": state["id"],
            "lat": round(lat, 5), "lon": round(lon, 5),
            "susceptibility_note": statics["susceptibility_note"],
        },
        "weather": {k: conditions.get(k) for k in (
            "temperature_c", "apparent_temperature_c", "relative_humidity_pct",
            "precipitation_mm", "weather_condition", "weather_code", "cloud_cover_pct",
            "wind_speed_kmph", "wind_gusts_kmph", "rain_1h_mm", "rain_24h_mm",
            "rain_72h_mm", "soil_moisture_m3m3", "observed_at", "source", "fetched_at",
            "elevation_m", "slope_deg", "terrain_source")},
        "risk": {
            "score": score,
            "level": level,
            "thresholds": {"moderate": THRESHOLD_MODERATE, "high": THRESHOLD_HIGH,
                           "critical": THRESHOLD_CRITICAL},
            "model_type": "rule_based_v1 (weights configurable — not yet field-validated)",
        },
        "factors": contributions,
        "top_contributors": top_factors,
        "trigger_notes": triggers,
        "explanation": (
            f"Risk is {level} ({score}/100), driven mainly by "
            + ", ".join(f"{c['label']} ({c['contribution']} pts)" for c in contributions[:3])
            + ". " + (("Key conditions: " + "; ".join(triggers) + ".") if triggers else "")
        ),
        "recommendations": recommendations,
        "warning": (build_warning(label, state["name"], score, level,
                                  top_factors, recommendations)
                    if level in ("HIGH", "CRITICAL") else None),
        "disclaimer": DISCLAIMER,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


