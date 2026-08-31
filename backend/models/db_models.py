"""SQLAlchemy ORM models.

Default database is a local SQLite file (zero setup). Set NER_DATABASE_URL to
a PostgreSQL connection string for production - the models are portable.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from utils.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="public")  # public|authority|researcher
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    locations: Mapped[list["SavedLocation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    preference: Mapped["NotificationPreference | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class SavedLocation(Base):
    __tablename__ = "saved_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    state_name: Mapped[str] = mapped_column(String(80), default="")
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(Text, default="")
    last_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped[User] = relationship(back_populates="locations")


class RiskCheck(Base):
    """Historical environmental + risk observation (trends, ML training data)."""

    __tablename__ = "risk_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    location_name: Mapped[str] = mapped_column(String(160), default="")
    state_name: Mapped[str] = mapped_column(String(80), index=True, default="")
    lat: Mapped[float] = mapped_column(Float, index=True)
    lon: Mapped[float] = mapped_column(Float, index=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_kmph: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_current_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_24h_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_72h_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_moisture: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    slope_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    factors_json: Mapped[dict] = mapped_column(JSON, default=dict)
    model_type: Mapped[str] = mapped_column(String(40), default="rule_based_v1")
    observed_landslide: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # user_id NULL => public broadcast alert; otherwise targeted in-app notification
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    location_name: Mapped[str] = mapped_column(String(160), default="")
    state_name: Mapped[str] = mapped_column(String(80), default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20))
    channels: Mapped[list] = mapped_column(JSON, default=list)  # ["in_app", "email", "sms"]
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    user: Mapped[User | None] = relationship(back_populates="alerts")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    email: Mapped[bool] = mapped_column(Boolean, default=False)
    email_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sms: Mapped[bool] = mapped_column(Boolean, default=False)
    min_level: Mapped[str] = mapped_column(String(20), default="HIGH")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped[User] = relationship(back_populates="preference")


_engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(_engine)

