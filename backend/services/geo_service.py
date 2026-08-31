"""Static geographical reference data and spatial helpers for the NER.

PROTOTYPE SIMPLIFICATIONS (see docs/DISCLAIMER.md):
- Soil/geology, land-cover, drainage and road-cutting susceptibility use
  curated state-level baselines + distance-to-known-road-corridor proxies,
  not real GeoTIFF rasters.
- "Historical landslides" uses an embedded list of known recurring landslide
  locations compiled from public GSI/news reporting (indicative only).
Replace with real DEM / soil / land-cover / GSI datasets in production.
"""
from math import asin, atan2, cos, degrees, exp, radians, sin, sqrt

# ---------------------------------------------------------------------------
# The 8 North Eastern Region states: capital coordinates + curated static
# susceptibility baselines (0-100, higher = more landslide-prone).
# bbox = (min_lat, max_lat, min_lon, max_lon) for coarse point->state lookup.
# ---------------------------------------------------------------------------
STATES = [
    {"id": "assam", "name": "Assam", "capital": "Dispur (Guwahati)", "lat": 26.1445, "lon": 91.7362,
     "bbox": (24.0, 28.0, 89.7, 96.2), "avg_elevation_m": 70,
     "geology": "Alluvial plains with sandstone-shale hills (Barail / Naga hills)", "geology_score": 58,
     "land_cover": "Agriculture, tea estates, urban clusters, forest patches", "land_cover_score": 55,
     "annual_rainfall_mm": 2800, "drainage_score": 42, "road_cutting_score": 55,
     "historical_note": "Guwahati hill slopes, Dima Hasao (Haflong), Karimganj and Cachar are repeatedly affected."},
    {"id": "arunachal-pradesh", "name": "Arunachal Pradesh", "capital": "Itanagar", "lat": 27.0844, "lon": 93.6053,
     "bbox": (26.6, 29.6, 91.5, 97.5), "avg_elevation_m": 1600,
     "geology": "Folded Himalayan schists, gneiss and younger sedimentary belts", "geology_score": 72,
     "land_cover": "Dense forest, shifting cultivation (jhum) slopes, alpine zones", "land_cover_score": 58,
     "annual_rainfall_mm": 3000, "drainage_score": 50, "road_cutting_score": 68,
     "historical_note": "NH-415 (Itanagar-Naharlagun), Tawang and Bomdila corridors see frequent slope failures."},
    {"id": "manipur", "name": "Manipur", "capital": "Imphal", "lat": 24.8170, "lon": 93.9368,
     "bbox": (23.8, 25.8, 92.9, 94.8), "avg_elevation_m": 800,
     "geology": "Disang and Barail shales/sandstones - weak, weathered rocks", "geology_score": 70,
     "land_cover": "Hill forests, jhum cultivation, valley agriculture", "land_cover_score": 58,
     "annual_rainfall_mm": 1500, "drainage_score": 48, "road_cutting_score": 66,
     "historical_note": "Imphal-Jiribam NH-37 and Moreh road cuttings are chronic landslide zones."},
    {"id": "meghalaya", "name": "Meghalaya", "capital": "Shillong", "lat": 25.5788, "lon": 91.8933,
     "bbox": (25.0, 26.2, 89.8, 92.9), "avg_elevation_m": 1200,
     "geology": "Precambrian gneiss/shale plateau with limestone and coal belts", "geology_score": 66,
     "land_cover": "Forest, large-scale quarrying, urban slope cutting, grasslands", "land_cover_score": 62,
     "annual_rainfall_mm": 11000, "drainage_score": 58, "road_cutting_score": 72,
     "historical_note": "Shillong, Sohra (Cherrapunji - among the wettest places on Earth) and Jaintia Hills are high-risk."},
    {"id": "mizoram", "name": "Mizoram", "capital": "Aizawl", "lat": 23.7271, "lon": 92.7176,
     "bbox": (21.9, 24.5, 92.2, 93.5), "avg_elevation_m": 1000,
     "geology": "Young folded Bhuban/Boka Bil sandstone-shale - highly unstable", "geology_score": 80,
     "land_cover": "Steep jhum-cultivated ridges, secondary forest, expanding towns", "land_cover_score": 70,
     "annual_rainfall_mm": 2500, "drainage_score": 55, "road_cutting_score": 75,
     "historical_note": "Aizawl is one of India's most landslide-prone capitals (NH-306, Aizawl-Lunglei routes)."},
    {"id": "nagaland", "name": "Nagaland", "capital": "Kohima", "lat": 25.6751, "lon": 94.1100,
     "bbox": (25.2, 27.1, 93.5, 95.2), "avg_elevation_m": 1100,
     "geology": "Disang-Barail flysch: alternating weak shale and sandstone", "geology_score": 74,
     "land_cover": "Jhum cultivation on steep slopes, forest, roadside settlements", "land_cover_score": 66,
     "annual_rainfall_mm": 2000, "drainage_score": 50, "road_cutting_score": 72,
     "historical_note": "NH-2 (Kohima-Dimapur) and Mokokchung routes suffer recurrent landslides."},
    {"id": "sikkim", "name": "Sikkim", "capital": "Gangtok", "lat": 27.3389, "lon": 88.6065,
     "bbox": (27.0, 28.2, 88.0, 89.0), "avg_elevation_m": 2000,
     "geology": "Daling/Darjeeling gneiss-schist with deep weathering; steep Himalayan slopes", "geology_score": 78,
     "land_cover": "Forest, terrace farming, hydel projects, steep road cuttings", "land_cover_score": 62,
     "annual_rainfall_mm": 3500, "drainage_score": 52, "road_cutting_score": 74,
     "historical_note": "Gangtok, Namchi and North Sikkim (Mangan/Chungthang) highways are frequently blocked."},
    {"id": "tripura", "name": "Tripura", "capital": "Agartala", "lat": 23.8315, "lon": 91.2868,
     "bbox": (22.9, 24.6, 91.1, 92.4), "avg_elevation_m": 80,
     "geology": "Dupi Tila / Tipam sandstone-clay hills - erosion and slump prone", "geology_score": 64,
     "land_cover": "Hill forests, rubber/bamboo plantations, rural settlements", "land_cover_score": 56,
     "annual_rainfall_mm": 2200, "drainage_score": 46, "road_cutting_score": 60,
     "historical_note": "Agartala hill slopes and NH-8 toward Udaipur see seasonal slides."},
]

# Generic baseline for pinned points OUTSIDE the 8 NER states (users can click
# anywhere in India on the map). Indicative neutral values — curated
# susceptibility data covers the NER only.
OUTSIDE_NER_STATE = {
    "id": "outside-ner",
    "name": "Outside NER",
    "capital": "Selected point",
    "avg_elevation_m": 300,
    "geology": "Region outside North Eastern India — generic national baseline (no curated data)",
    "geology_score": 50,
    "land_cover": "Generic mixed land cover (no curated data for this region)",
    "land_cover_score": 50,
    "annual_rainfall_mm": 1500,
    "drainage_score": 40,
    "road_cutting_score": 35,
    "historical_note": (
        "This point lies outside the 8 NER states — curated susceptibility baselines "
        "cover NER only; generic national values are used here."
    ),
}

# ---------------------------------------------------------------------------
# Known recurring landslide locations (indicative; compiled from public GSI /
# NIDM reports and news archives). severity: 0-100 susceptibility weight.
# ---------------------------------------------------------------------------
HOTSPOTS = {
    "Assam": [("Kamakhya Hills, Guwahati", 26.1664, 91.7057, 80), ("Haflong, Dima Hasao", 25.1796, 93.0183, 85),
              ("Karimganj town slopes", 24.8700, 92.3500, 72), ("Diphu, Karbi Anglong", 25.8383, 93.4297, 65),
              ("Dhemaji foothills", 27.4833, 94.5833, 58)],
    "Arunachal Pradesh": [("Itanagar NH-415 slopes", 27.0844, 93.6053, 76), ("Tawang route", 27.5850, 91.8680, 80),
                          ("Bomdila", 27.2600, 92.4170, 78), ("Pasighat", 28.0670, 95.3270, 68),
                          ("Ziro plateau edge", 27.5400, 93.8300, 60)],
    "Manipur": [("Imphal-Jiribam NH-37 cuttings", 24.7000, 93.8500, 75), ("Senapati hills", 25.2700, 93.9700, 70),
                ("Moreh road section", 24.2500, 94.2930, 72), ("Ukhrul slopes", 25.0500, 94.3600, 66)],
    "Meghalaya": [("Shillong urban slopes", 25.5788, 91.8933, 82), ("Sohra (Cherrapunji)", 25.3000, 91.6900, 78),
                  ("Jowai, Jaintia Hills", 25.4500, 92.2000, 70), ("Tura, Garo Hills", 25.5100, 90.2100, 72)],
    "Mizoram": [("Aizawl city slopes", 23.7271, 92.7176, 88), ("Lunglei", 22.8800, 92.7330, 80),
                ("Champhai", 23.4700, 93.3300, 72), ("Kolasib NH-306", 24.2200, 92.6800, 70)],
    "Nagaland": [("Kohima slopes", 25.6751, 94.1100, 80), ("NH-2 Dimapur-Kohima", 25.9000, 93.7270, 70),
                 ("Mokokchung", 26.3200, 94.5200, 72), ("Phek district", 25.6700, 94.5000, 68)],
    "Sikkim": [("Gangtok slopes", 27.3389, 88.6065, 82), ("Namchi", 27.1700, 88.3600, 74),
               ("Mangan, North Sikkim", 27.5100, 88.5300, 80), ("Chungthang", 27.6000, 88.6400, 82)],
    "Tripura": [("Agartala hill slopes", 23.8315, 91.2868, 66), ("Udaipur, Gomati", 23.5310, 91.4820, 60),
                ("Dharmanagar", 24.3730, 92.1680, 62), ("Ambassa, Dhalai", 23.7300, 91.8500, 65)],
}

# Sample points along highway corridors with chronic road-slope cutting
# (proximity proxy for the "road cutting" factor).
CORRIDOR_POINTS = [
    (26.180, 91.744), (26.090, 91.780), (25.950, 91.860), (25.800, 91.920), (25.670, 91.900), (25.578, 91.893),
    (25.560, 91.880), (25.420, 91.720), (25.300, 91.690),
    (25.675, 94.110), (25.590, 93.990), (25.480, 93.870), (25.900, 93.727),
    (27.339, 88.607), (27.240, 88.530), (27.170, 88.360), (27.510, 88.530),
    (23.727, 92.718), (23.590, 92.740), (23.200, 92.850), (22.880, 92.733),
    (27.084, 93.605), (27.020, 93.620), (26.950, 93.500), (27.590, 91.868), (27.260, 92.417),
    (24.817, 93.937), (24.700, 93.850), (24.550, 93.700), (24.250, 94.293),
    (23.832, 91.287), (23.700, 91.400), (23.531, 91.482),
]

# ---------------------------------------------------------------------------
# Spatial helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    h = (sin(radians(lat2 - lat1) / 2) ** 2
         + cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lon2 - lon1) / 2) ** 2)
    return 2 * 6371.0088 * asin(min(1.0, sqrt(h)))


def get_state(state_id_or_name: str):
    q = (state_id_or_name or "").strip().lower()
    for s in STATES:
        if q and q in (s["id"], s["name"].lower()):
            return s
    return None


def state_for_point(lat: float, lon: float) -> dict:
    """Coarse bbox lookup (smaller states first). Points elsewhere in India
    resolve to the generic OUTSIDE_NER_STATE baseline."""
    priority = ["sikkim", "tripura", "mizoram", "manipur", "nagaland",
                "meghalaya", "arunachal-pradesh", "assam"]
    by_id = {s["id"]: s for s in STATES}
    for sid in priority:
        s = by_id[sid]
        min_lat, max_lat, min_lon, max_lon = s["bbox"]
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return s
    return OUTSIDE_NER_STATE


def historical_score(lat: float, lon: float, state_name: str):
    """Score 0-100 from proximity/severity of known recurrent landslide spots."""
    spots = HOTSPOTS.get(state_name, [])
    best, nearest_name, nearest_km = 0.0, None, None
    for name, hlat, hlon, severity in spots:
        km = _haversine_km(lat, lon, hlat, hlon)
        if nearest_km is None or km < nearest_km:
            nearest_name, nearest_km = name, km
        best = max(best, severity * exp(-km / 20.0))  # influence decays ~20 km
    state = get_state(state_name)
    baseline = (state["geology_score"] + state["land_cover_score"]) / 2 if state else 50.0
    return round(min(100.0, max(best, baseline * 0.5)), 1), nearest_name, (
        round(nearest_km, 1) if nearest_km is not None else None)


def road_cutting_score(lat: float, lon: float):
    """Proxy score: proximity to highway corridors with chronic slope cutting."""
    if not CORRIDOR_POINTS:
        return 20.0, None
    km = min(_haversine_km(lat, lon, p[0], p[1]) for p in CORRIDOR_POINTS)
    if km <= 1.5:
        score = 88.0
    elif km <= 4.0:
        score = 68.0
    elif km <= 8.0:
        score = 48.0
    elif km <= 15.0:
        score = 32.0
    else:
        score = 18.0
    return score, round(km, 2)


def static_factors(lat: float, lon: float, state: dict | None = None) -> dict:
    """Curated static susceptibility factors for a point (prototype)."""
    s = state or state_for_point(lat, lon)
    hist, nearest_spot, spot_km = historical_score(lat, lon, s["name"])
    road, road_km = road_cutting_score(lat, lon)
    return {
        "state": s,
        "elevation_baseline_m": s["avg_elevation_m"],
        "geology": s["geology"],
        "geology_score": s["geology_score"],
        "land_cover": s["land_cover"],
        "land_cover_score": s["land_cover_score"],
        "drainage_score": s["drainage_score"],
        "annual_rainfall_mm": s["annual_rainfall_mm"],
        "historical_score": hist,
        "nearest_hotspot": nearest_spot,
        "nearest_hotspot_km": spot_km,
        "road_cutting_score": road,
        "nearest_road_corridor_km": road_km,
        "susceptibility_note": s["historical_note"],
    }


