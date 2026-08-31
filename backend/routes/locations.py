"""Saved locations ('My Locations') with latest risk snapshots."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import schemas
from models.db_models import SavedLocation, get_db
from routes.auth import get_current_user
from routes.risk import _store_check
from services import risk_service
from services.alert_service import notify_saved_location_change
from services.weather_service import WeatherServiceError

router = APIRouter(tags=["locations"])


@router.get("/locations")
def my_locations(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (db.query(SavedLocation).filter_by(user_id=user.id)
            .order_by(SavedLocation.created_at.desc()).all())
    return {"count": len(rows), "locations": [{
        "id": l.id, "name": l.name, "state_name": l.state_name,
        "lat": l.lat, "lon": l.lon, "notes": l.notes,
        "last_risk_score": l.last_risk_score, "last_risk_level": l.last_risk_level,
        "last_checked_at": l.last_checked_at, "created_at": l.created_at} for l in rows]}


@router.post("/locations", status_code=201)
def add_location(body: schemas.LocationIn, user=Depends(get_current_user),
                 db: Session = Depends(get_db)):
    loc = SavedLocation(user_id=user.id, name=body.name.strip(), state_name=body.state or "",
                        lat=body.lat, lon=body.lon, notes=body.notes)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return {"message": "Location saved.", "id": loc.id}


@router.delete("/locations/{location_id}")
def delete_location(location_id: int, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    loc = db.query(SavedLocation).filter_by(id=location_id, user_id=user.id).first()
    if loc is None:
        raise HTTPException(status_code=404, detail="Saved location not found.")
    db.delete(loc)
    db.commit()
    return {"message": f"'{loc.name}' removed."}


@router.post("/locations/{location_id}/check")
def check_location(location_id: int, user=Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """Re-run the risk analysis for a saved location, update its snapshot and
    fire a change notification when risk rises (e.g. MODERATE -> HIGH)."""
    loc = db.query(SavedLocation).filter_by(id=location_id, user_id=user.id).first()
    if loc is None:
        raise HTTPException(status_code=404, detail="Saved location not found.")
    try:
        analysis = risk_service.evaluate(loc.lat, loc.lon, name=loc.name,
                                         state_hint=loc.state_name or None)
    except WeatherServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    _store_check(db, user, analysis)
    alert = notify_saved_location_change(db, user, loc, analysis)
    return {"analysis": analysis,
            "notification": ({"id": alert.id, "title": alert.title, "message": alert.message}
                             if alert else None)}
