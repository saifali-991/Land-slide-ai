"""Pydantic request schemas with input validation.

All user input is validated and length/Range-bounded before it reaches
services or the database.
"""
from datetime import datetime

from pydantic import BaseModel, Field

# Accept anywhere in India — points outside the 8 NER states fall back to a
# generic baseline (see services/geo_service.py OUTSIDE_NER_STATE).
IN_LAT = Field(ge=5.0, le=38.0, description="Latitude within India")
IN_LON = Field(ge=66.0, le=98.5, description="Longitude within India")
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="public", pattern="^(public|authority|researcher)$")


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AnalyzeIn(BaseModel):
    lat: float = IN_LAT
    lon: float = IN_LON
    state: str | None = Field(default=None, max_length=80)
    name: str | None = Field(default=None, max_length=160)
    save: bool = False


class PredictIn(BaseModel):
    lat: float = IN_LAT
    lon: float = IN_LON
    state: str | None = Field(default=None, max_length=80)


class LocationIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    lat: float = IN_LAT
    lon: float = IN_LON
    state: str | None = Field(default=None, max_length=80)
    notes: str = Field(default="", max_length=1000)


class AlertPreferenceIn(BaseModel):
    in_app: bool = True
    email: bool = False
    email_address: str | None = Field(default=None, pattern=EMAIL_PATTERN, max_length=255)
    sms: bool = False
    min_level: str = Field(default="HIGH", pattern="^(MODERATE|HIGH|CRITICAL)$")


class MarkReadIn(BaseModel):
    ids: list[int] | None = None
