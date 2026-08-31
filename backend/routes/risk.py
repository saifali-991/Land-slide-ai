"""Location risk analysis + ML prediction endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import schemas
from models.db_models import RiskCheck, SavedLocation, get_db
from routes.auth import get_optional_user
from services import ml_service, risk_service
from services.alert_service import create_broadcast_alert, notify_saved_location_change
from services.weather_service import WeatherServiceError

router = APIRouter(tags=["risk"])


def _store_check(db: Session, user, analysis: dict) -> RiskCheck:
    """Persist the observation (historical data for trends / ML / evaluation)."""
    w, loc, r = analysis["weather"], analysis["location"], analysis["risk"]
    row = RiskCheck(
        user_id=user.id if user else None,
        location_name=loc["name"], state_name=loc["state"], lat=loc["lat"], lon=loc["lon"],
        temperature_c=w.get("temperature_c"), humidity_pct=w.get("relative_humidity_pct"),
        wind_kmph=w.get("wind_speed_kmph"), rainfall_current_mm=w.get("precipitation_mm"),
        rainfall_24h_mm=w.get("rain_24h_mm"), rainfall_72h_mm=w.get("rain_72h_mm"),
        soil_moisture=w.get("soil_moisture_m3m3"), elevation_m=w.get("elevation_m"),
        slope_deg=w.get("slope_deg"), risk_score=r["score"], risk_level=r["level"],
        factors_json={f["factor"]: f["score"] for f in analysis["factors"]},
        model_type=r["model_type"],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/risk/analyze")
def analyze_location(body: schemas.AnalyzeIn, user=Depends(get_optional_user),
                     db: Session = Depends(get_db)):
    """Analyze a specific location (lat/lon) -> risk score, level, factors,
    explanation, recommendations. Stores a history row; optionally saves the
    location to the logged-in user's account."""
    try:
        analysis = risk_service.evaluate(body.lat, body.lon, name=body.name,
                                         state_hint=body.state)
    except WeatherServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    row = _store_check(db, user, analysis)
    create_broadcast_alert(db, analysis)

    saved_location_id = None
    if user and body.save:
        existing = (db.query(SavedLocation)
                    .filter(SavedLocation.user_id == user.id,
                            SavedLocation.lat.between(body.lat - 0.01, body.lat + 0.01),
                            SavedLocation.lon.between(body.lon - 0.01, body.lon + 0.01))
                    .first())
        if existing is None:
            loc = SavedLocation(
                user_id=user.id,
                name=body.name or f"{analysis['location']['name']}, {analysis['location']['state']}",
                state_name=analysis["location"]["state"], lat=body.lat, lon=body.lon)
            db.add(loc)
            db.commit()
            db.refresh(loc)
            saved_location_id = loc.id
            notify_saved_location_change(db, user, loc, analysis)
        else:
            saved_location_id = existing.id

    return {"check_id": row.id, "created_at": row.created_at, **analysis,
            "saved_location_id": saved_location_id}


@router.post("/risk/predict")
def predict_location(body: schemas.PredictIn, db: Session = Depends(get_db)):
    """Run the trained ML model on live factors (rule-based fallback included
    for comparison; the model must be validated before operational use)."""
    try:
        analysis = risk_service.evaluate(body.lat, body.lon, state_hint=body.state)
    except WeatherServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    factor_scores = {f["factor"]: f["score"] for f in analysis["factors"]}
    ml_result = None
    if ml_service.model_available():
        try:
            ml_result = ml_service.predict_from_factor_scores(factor_scores)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return {
        "location": analysis["location"],
        "weather": analysis["weather"],
        "input_factors": factor_scores,
        "ml": ml_result,
        "rule_based": {"risk_score": analysis["risk"]["score"],
                       "risk_level": analysis["risk"]["level"]},
        "model_info": ml_service.model_info(),
        "disclaimer": ("ML output is trained on prototype (synthetic) data and must be "
                       "validated with real landslide records before operational use. "
                       "Always follow official disaster-management advisories."),
    }
