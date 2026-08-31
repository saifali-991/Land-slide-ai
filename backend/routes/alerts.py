"""Alert subscription + in-app notifications (+ public broadcast feed)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import schemas
from models.db_models import Alert, NotificationPreference, get_db
from routes.auth import get_current_user

router = APIRouter(tags=["alerts"])


@router.post("/alerts/subscribe")
def subscribe(body: schemas.AlertPreferenceIn, user=Depends(get_current_user),
              db: Session = Depends(get_db)):
    """Configure how the user wants to be notified (in-app / email / SMS stub)."""
    pref = db.query(NotificationPreference).filter_by(user_id=user.id).first()
    if pref is None:
        pref = NotificationPreference(user_id=user.id)
        db.add(pref)
    pref.in_app = body.in_app
    pref.email = body.email
    pref.email_address = body.email_address if body.email else None
    pref.sms = body.sms
    pref.min_level = body.min_level
    db.commit()
    db.refresh(pref)
    return {"message": "Notification preferences saved.",
            "preferences": {"in_app": pref.in_app, "email": pref.email,
                            "email_address": pref.email_address, "sms": pref.sms,
                            "min_level": pref.min_level}}


@router.get("/alerts/preferences")
def get_preferences(user=Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.query(NotificationPreference).filter_by(user_id=user.id).first()
    if pref is None:
        return {"in_app": True, "email": False, "email_address": None,
                "sms": False, "min_level": "HIGH"}
    return {"in_app": pref.in_app, "email": pref.email, "email_address": pref.email_address,
            "sms": pref.sms, "min_level": pref.min_level}


@router.get("/alerts/notifications")
def my_notifications(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (db.query(Alert).filter(Alert.user_id == user.id)
            .order_by(Alert.created_at.desc()).limit(50).all())
    return {"unread": sum(1 for a in rows if not a.is_read),
            "notifications": [{
                "id": a.id, "title": a.title, "message": a.message,
                "risk_level": a.risk_level, "risk_score": a.risk_score,
                "location_name": a.location_name, "is_read": a.is_read,
                "created_at": a.created_at} for a in rows]}


@router.post("/alerts/notifications/read")
def mark_read(body: schemas.MarkReadIn, user=Depends(get_current_user),
              db: Session = Depends(get_db)):
    q = db.query(Alert).filter(Alert.user_id == user.id, Alert.is_read.is_(False))
    if body.ids:
        q = q.filter(Alert.id.in_(body.ids))
    marked = q.update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"marked_read": marked}


@router.get("/alerts/latest")
def latest_broadcasts(db: Session = Depends(get_db)):
    """Public feed of recent HIGH/CRITICAL broadcast alerts (no login needed)."""
    rows = (db.query(Alert).filter(Alert.user_id.is_(None))
            .order_by(Alert.created_at.desc()).limit(10).all())
    return {"alerts": [{
        "id": a.id, "title": a.title, "message": a.message, "risk_level": a.risk_level,
        "risk_score": a.risk_score, "state_name": a.state_name,
        "location_name": a.location_name, "created_at": a.created_at} for a in rows]}
