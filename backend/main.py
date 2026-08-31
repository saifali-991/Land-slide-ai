"""NER Landslide AI — FastAPI application entry point.

Run (from the backend/ directory):
    python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

Interactive API docs: http://127.0.0.1:8000/docs
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.db_models import init_db
from routes import alerts, auth, dashboard, history, locations, risk, states, weather
from utils.config import APP_NAME, APP_VERSION, CORS_ORIGINS, DESCRIPTION, ENV
from utils.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()  # create tables if missing (SQLite default / portable DDL)
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, description=DESCRIPTION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)  # added last => runs first (outermost)

API_PREFIX = "/api"
for router in (states.router, weather.router, dashboard.router, risk.router,
               history.router, auth.router, alerts.router, locations.router):
    app.include_router(router, prefix=API_PREFIX)


@app.get("/", tags=["health"])
def health_check():
    """Backend health check."""
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "env": ENV,
        "time": datetime.now(timezone.utc).isoformat(),
        "docs": "/docs",
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
