"""Early-warning / notification service.

- Public broadcast alerts when state-level risk is HIGH/CRITICAL (deduplicated
  within a cooldown window so users are not spammed).
- Targeted in-app notifications for a user's saved locations when risk rises
  (e.g. MODERATE -> HIGH) or first reaches their minimum level.
- Email/SMS are stubbed behind one hook: wire an SMTP / Twilio / FCM SDK into
  _send_external() without touching callers. Nothing external is required to
  run the prototype.

Notifications deliberately avoid claiming certainty about landslide events.
"""
import logging
from datetime import datetime, timedelta, timezone

from models.db_models import Alert, NotificationPreference, SavedLocation
from utils.config import LEVEL_SEVERITY

logger = logging.getLogger("alert_service")

BROADCAST_COOLDOWN_MINUTES = 180


def create_broadcast_alert(db, analysis: dict) -> Alert | None:
    """Store a public alert for HIGH/CRITICAL risk at a monitored location."""
    risk = analysis["risk"]
    if risk["level"] not in ("HIGH", "CRITICAL"):
        return None
    loc = analysis["location"]
    state_name = loc.get("state") or ""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=BROADCAST_COOLDOWN_MINUTES)
    recent = (
        db.query(Alert)
        .filter(Alert.user_id.is_(None), Alert.state_name == state_name,
                Alert.risk_level == risk["level"], Alert.created_at >= cutoff)
        .first()
    )
    if recent:  # same state + level already alerted recently
        return None
    warning = analysis.get("warning", {})
    alert = Alert(
        user_id=None,
        title=warning.get("title") or f"{risk['level']} Landslide Risk — {loc.get('name')}",
        message=warning.get("message") or "",
        location_name=loc.get("name") or "",
        state_name=state_name,
        lat=loc.get("lat"),
        lon=loc.get("lon"),
        risk_score=risk["score"],
        risk_level=risk["level"],
        channels=["in_app"],
    )
    db.add(alert)
    db.commit()
    return alert


def create_user_alert(db, user_id: int, title: str, message: str,
                      analysis: dict | None = None, channels: list | None = None) -> Alert:
    alert = Alert(
        user_id=user_id,
        title=title,
        message=message,
        location_name=(analysis or {}).get("location", {}).get("name", ""),
        state_name=(analysis or {}).get("location", {}).get("state", ""),
        lat=(analysis or {}).get("location", {}).get("lat"),
        lon=(analysis or {}).get("location", {}).get("lon"),
        risk_score=(analysis or {}).get("risk", {}).get("score"),
        risk_level=(analysis or {}).get("risk", {}).get("level", ""),
        channels=channels or ["in_app"],
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def notify_saved_location_change(db, user, saved: SavedLocation, analysis: dict) -> Alert | None:
    """Notify when a saved location's risk rises to / past the user's min level."""
    pref = db.query(NotificationPreference).filter_by(user_id=user.id).first()
    if pref is None:
        pref = NotificationPreference(user_id=user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)

    risk = analysis["risk"]
    level, score = risk["level"], risk["score"]
    previous_level = saved.last_risk_level

    severity_now = LEVEL_SEVERITY.get(level, 0)
    severity_prev = LEVEL_SEVERITY.get(previous_level or "LOW", 0)
    min_needed = LEVEL_SEVERITY.get(pref.min_level, 2)

    rose = severity_now > severity_prev
    crossed = severity_now >= min_needed
    first_check = previous_level is None

    alert_out = None
    if pref.in_app and crossed and (first_check or rose):
        title = f"⚠️ Landslide Risk Alert — {saved.name}"
        if not first_check and rose:
            message = (f"Your saved location '{saved.name}' risk changed from "
                       f"{previous_level} to {level} (score {score}/100).\n\n"
                       "This indicates elevated risk based on available data — it is not a "
                       "certainty. Please follow official disaster-management advisories.")
        else:
            message = (f"Your saved location '{saved.name}' is at {level} risk "
                       f"(score {score}/100). Please follow official advisories.")
        alert_out = create_user_alert(db, user.id, title, message, analysis)
        _send_external(user, pref, title, message)

    saved.last_risk_score = score
    saved.last_risk_level = level
    saved.last_checked_at = datetime.now(timezone.utc)
    db.commit()
    return alert_out


def _send_external(user, pref: NotificationPreference, title: str, message: str) -> None:
    """Hook for Email/SMS providers (disabled by default in the prototype)."""
    if pref.email:
        logger.info("[EMAIL -> %s] %s\n%s", pref.email_address or user.email, title, message)
    if pref.sms:
        logger.info("[SMS] %s\n%s", title, message)
