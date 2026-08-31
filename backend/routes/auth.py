"""Authentication routes: register, login, profile (JWT-based)."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from models import schemas
from models.db_models import User, get_db
from utils.security import create_access_token, decode_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


def _user_out(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email,
            "role": user.role, "created_at": user.created_at}


def get_current_user(authorization: str | None = Header(default=None),
                     db: Session = Depends(get_db)) -> User:
    """Dependency: requires a valid Bearer token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    try:
        payload = decode_token(authorization.split(" ", 1)[1].strip())
    except Exception:
        raise HTTPException(status_code=401,
                            detail="Session expired or invalid. Please log in again.")
    user = db.query(User).filter(User.id == int(payload.get("sub", 0))).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists.")
    return user


def get_optional_user(authorization: str | None = Header(default=None),
                      db: Session = Depends(get_db)) -> User | None:
    """Dependency: anonymous OK; attaches the user when a valid token is sent."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        payload = decode_token(authorization.split(" ", 1)[1].strip())
        return db.query(User).filter(User.id == int(payload.get("sub", 0))).first()
    except Exception:
        return None


@router.post("/auth/register", response_model=schemas.TokenOut, status_code=201)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    user = User(name=body.name.strip(), email=email,
                password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.id, user.email, user.role),
            "token_type": "bearer", "user": _user_out(user)}


@router.post("/auth/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"access_token": create_access_token(user.id, user.email, user.role),
            "token_type": "bearer", "user": _user_out(user)}


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"user": _user_out(user)}


@router.patch("/auth/me")
def update_profile(body: schemas.ProfileUpdateIn, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    if body.name:
        user.name = body.name.strip()
    if body.password:
        user.password_hash = hash_password(body.password)
    db.commit()
    return {"user": _user_out(user)}
