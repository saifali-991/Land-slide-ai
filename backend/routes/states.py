"""State reference data endpoints (the 8 NER states)."""
from fastapi import APIRouter, HTTPException

from services import geo_service

router = APIRouter(tags=["states"])


@router.get("/states")
def list_states():
    """All 8 NER states with coordinates and curated static context."""
    states = []
    for s in geo_service.STATES:
        states.append({
            "id": s["id"], "name": s["name"], "capital": s["capital"],
            "lat": s["lat"], "lon": s["lon"],
            "avg_elevation_m": s["avg_elevation_m"],
            "geology": s["geology"], "land_cover": s["land_cover"],
            "annual_rainfall_mm": s["annual_rainfall_mm"],
            "historical_note": s["historical_note"],
            "known_hotspots": [h[0] for h in geo_service.HOTSPOTS.get(s["name"], [])],
        })
    return {"count": len(states), "states": states}


@router.get("/states/{state_id}")
def state_detail(state_id: str):
    s = geo_service.get_state(state_id)
    if s is None:
        raise HTTPException(status_code=404,
                            detail=f"Unknown state '{state_id}'. See GET /api/states.")
    return {
        "id": s["id"], "name": s["name"], "capital": s["capital"],
        "lat": s["lat"], "lon": s["lon"], "bbox": s["bbox"],
        "avg_elevation_m": s["avg_elevation_m"],
        "geology": s["geology"], "geology_score": s["geology_score"],
        "land_cover": s["land_cover"], "land_cover_score": s["land_cover_score"],
        "annual_rainfall_mm": s["annual_rainfall_mm"],
        "drainage_score": s["drainage_score"], "road_cutting_score": s["road_cutting_score"],
        "historical_note": s["historical_note"],
        "known_hotspots": [
            {"name": h[0], "lat": h[1], "lon": h[2], "severity": h[3]}
            for h in geo_service.HOTSPOTS.get(s["name"], [])
        ],
    }
