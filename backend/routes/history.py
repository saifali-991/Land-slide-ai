"""Historical risk observations (trends, comparison, ML input)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.db_models import RiskCheck, get_db
from routes.auth import get_current_user
from services import geo_service

router = APIRouter(tags=["history"])


def _row_out(r: RiskCheck) -> dict:
    return {
        "id": r.id, "created_at": r.created_at, "location_name": r.location_name,
        "state_name": r.state_name, "lat": r.lat, "lon": r.lon,
        "temperature_c": r.temperature_c, "humidity_pct": r.humidity_pct,
        "rainfall_24h_mm": r.rainfall_24h_mm, "rainfall_72h_mm": r.rainfall_72h_mm,
        "soil_moisture": r.soil_moisture, "elevation_m": r.elevation_m,
        "slope_deg": r.slope_deg, "risk_score": r.risk_score, "risk_level": r.risk_level,
        "observed_landslide": r.observed_landslide, "model_type": r.model_type,
    }


@router.get("/history/me")
def my_history(limit: int = 100, user=Depends(get_current_user),
               db: Session = Depends(get_db)):
    """The logged-in user's previous risk checks."""
    rows = (db.query(RiskCheck).filter(RiskCheck.user_id == user.id)
            .order_by(RiskCheck.created_at.desc())
            .limit(max(1, min(limit, 300))).all())
    return {"count": len(rows), "observations": [_row_out(r) for r in rows]}


@router.get("/history/{location}")
def history_for_location(location: str, limit: int = 100,
                         db: Session = Depends(get_db)):
    """`location` may be: a state id/name ('meghalaya', 'Sikkim') or 'lat,lon'."""
    limit = max(1, min(limit, 300))
    q = db.query(RiskCheck)

    if "," in location:
        try:
            lat_s, lon_s = (float(p) for p in location.split(",", 1))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid coordinates. Use 'lat,lon'.")
        q = q.filter(RiskCheck.lat.between(lat_s - 0.05, lat_s + 0.05),
                     RiskCheck.lon.between(lon_s - 0.05, lon_s + 0.05))
        label = f"{lat_s:.4f}, {lon_s:.4f}"
    else:
        s = geo_service.get_state(location)
        if s:
            q = q.filter(RiskCheck.state_name == s["name"])
            label = s["name"]
        else:
            q = q.filter(RiskCheck.location_name.ilike(f"%{location}%"))
            label = location

    rows = q.order_by(RiskCheck.created_at.desc()).limit(limit).all()
    level_counts = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    for r in rows:
        level_counts[r.risk_level] = level_counts.get(r.risk_level, 0) + 1
    return {
        "location": label,
        "count": len(rows),
        "level_counts": level_counts,
        "latest": _row_out(rows[0]) if rows else None,
        "observations": [_row_out(r) for r in rows],
    }
