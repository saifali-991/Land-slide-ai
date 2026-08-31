"""Main dashboard: live weather + risk for all 8 NER states."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.db_models import RiskCheck, get_db
from services import geo_service, risk_service
from services.alert_service import create_broadcast_alert
from services.weather_service import WeatherServiceError

router = APIRouter(tags=["dashboard"])

_HISTORY_DEDUPE_MINUTES = 30


def _store_dashboard_row(db: Session, analysis: dict) -> None:
    """Persist one history row per state at most every N minutes (trend data)."""
    loc, r, w = analysis["location"], analysis["risk"], analysis["weather"]
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_HISTORY_DEDUPE_MINUTES)
    recent = (db.query(RiskCheck)
              .filter(RiskCheck.state_name == loc["state"],
                      RiskCheck.location_name == loc["name"],
                      RiskCheck.created_at >= cutoff)
              .first())
    if recent:
        return
    db.add(RiskCheck(
        location_name=loc["name"], state_name=loc["state"],
        lat=loc["lat"], lon=loc["lon"],
        temperature_c=w.get("temperature_c"), humidity_pct=w.get("relative_humidity_pct"),
        wind_kmph=w.get("wind_speed_kmph"), rainfall_current_mm=w.get("precipitation_mm"),
        rainfall_24h_mm=w.get("rain_24h_mm"), rainfall_72h_mm=w.get("rain_72h_mm"),
        soil_moisture=w.get("soil_moisture_m3m3"), elevation_m=w.get("elevation_m"),
        slope_deg=w.get("slope_deg"), risk_score=r["score"], risk_level=r["level"],
        factors_json={f["factor"]: f["score"] for f in analysis["factors"]},
        model_type="dashboard_scheduled"))
    db.commit()


def _analyze_state(s: dict) -> dict:
    return risk_service.evaluate(s["lat"], s["lon"], name=s["capital"], state_hint=s["id"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Live weather + landslide risk snapshot for all 8 states (parallel fetch)."""
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            analyses = list(pool.map(_analyze_state, geo_service.STATES))
    except WeatherServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    states_out, counts = [], {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    for s, analysis in zip(geo_service.STATES, analyses):
        create_broadcast_alert(db, analysis)          # early-warning broadcast (deduped)
        _store_dashboard_row(db, analysis)            # history / trend data (deduped)

        level = analysis["risk"]["level"]
        counts[level] = counts.get(level, 0) + 1
        w = analysis["weather"]
        states_out.append({
            "id": s["id"], "name": s["name"], "capital": s["capital"],
            "lat": s["lat"], "lon": s["lon"],
            "weather": {
                "temperature_c": w.get("temperature_c"),
                "relative_humidity_pct": w.get("relative_humidity_pct"),
                "precipitation_mm": w.get("precipitation_mm"),
                "rain_24h_mm": w.get("rain_24h_mm"),
                "wind_speed_kmph": w.get("wind_speed_kmph"),
                "soil_moisture_m3m3": w.get("soil_moisture_m3m3"),
                "weather_condition": w.get("weather_condition"),
                "observed_at": w.get("observed_at"),
            },
            "risk": {"score": analysis["risk"]["score"], "level": level},
            "top_contributors": analysis["top_contributors"],
            "updated_at": w.get("fetched_at"),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "states_monitored": len(states_out),
            "counts": counts,
            "weather_source": "Open-Meteo (https://open-meteo.com)",
        },
        "states": states_out,
    }
