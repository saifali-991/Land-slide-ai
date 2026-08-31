"""Current weather endpoints (Open-Meteo based)."""
from fastapi import APIRouter, HTTPException

from services import geo_service
from services.weather_service import WeatherServiceError, fetch_current_weather

router = APIRouter(tags=["weather"])


@router.get("/weather/{state}")
def state_weather(state: str):
    """Current weather + recent rainfall + soil moisture at a state capital."""
    s = geo_service.get_state(state)
    if s is None:
        raise HTTPException(status_code=404,
                            detail=f"Unknown state '{state}'. See GET /api/states.")
    try:
        wx = fetch_current_weather(s["lat"], s["lon"])
    except WeatherServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"state": s["name"], "capital": s["capital"], "lat": s["lat"], "lon": s["lon"], **wx}
