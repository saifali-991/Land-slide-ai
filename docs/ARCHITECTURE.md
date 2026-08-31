# Architecture — NER Landslide AI

```
                 ┌────────────────────────────────────────────┐
                 │              USER (browser)                │
                 └──────────────┬─────────────────────────────┘
                                │  React + Vite (SPA)
                 ┌──────────────▼─────────────────────────────┐
                 │  frontend/ (React 18, React Leaflet, CSS)  │
                 │  Dashboard · Map · Analyze · My Locations  │
                 │  History · Alerts · Auth                   │
                 └──────────────┬─────────────────────────────┘
                                │  JSON over HTTP (/api, dev-proxy)
┌───────────────┐  ┌────────────▼─────────────────────────────┐
│  Open-Meteo   │◄─┤           backend/ (FastAPI)              │
│  weather+DEM  │  │  routes/   → HTTP layer (validation)      │
└───────────────┘  │  services/ → business logic               │
                   │    geo_service     static susceptibility  │
                   │    weather_service live wx + terrain      │
                   │    risk_service    rule engine + explain  │
                   │    ml_service      trained model wrapper  │
                   │    alert_service   warnings/notifications │
                   │  models/   → SQLAlchemy ORM + schemas     │
                   │  utils/    → config, JWT/PBKDF2, limiter  │
                   └────────────┬──────────────┬───────────────┘
                                │              │
                 ┌──────────────▼──────┐  ┌────▼──────────────────┐
                 │ SQLite / PostgreSQL │  │ ml/ (offline training)│
                 │ users, locations,   │  │ datasets → preprocess │
                 │ risk_checks, alerts │  │ → train → joblib model│
                 └─────────────────────┘  └───────────────────────┘
                                    (ml/models/landslide_model.joblib
                                     loaded by backend ml_service)
```

## Request flow (location analysis)

1. User clicks the map → frontend sends `POST /api/risk/analyze {lat, lon, ...}`.
2. `geo_service` resolves the state (bbox lookup + nearest-capital fallback) and returns the
   static susceptibility baselines (geology, land cover, drainage, road-cutting proximity,
   historical hotspot influence).
3. `weather_service` calls Open-Meteo: current conditions, 72 h hourly precipitation
   (→ 1 h/24 h/72 h accumulation), top-layer soil moisture, and a 5-point elevation sample
   (→ slope estimate). Responses are cached in-memory (TTL 10 min) to protect the public API.
4. `risk_service.compute_factor_scores` normalizes every input to 0–100 (with sensible
   fallbacks when a value is missing) and `evaluate` applies the configurable weights,
   producing score → level (LOW/MODERATE/HIGH/CRITICAL), per-factor contributions, trigger
   notes, a plain-language explanation, recommendations and (for HIGH/CRITICAL) a warning text.
5. `routes/risk` stores the observation (`risk_checks`), `alert_service` may create a
   broadcast alert (deduplicated), and the response is returned with full explanations.

## Design decisions

- **Rule engine + ML side by side.** The rule engine is deterministic and explainable — every
  contribution is visible. The ML model (bundle of a scikit-learn `Pipeline`) is served at
  `/api/risk/predict` for comparison; the backend falls back gracefully if the model is missing.
- **Configurable everything.** Weights, thresholds, TTLs, CORS, DB URL, secrets — all from
  environment variables (`utils/config.py`), so pilots can tune without code changes.
- **Graceful degradation.** Missing soil moisture → estimated from rainfall; DEM failure →
  state baseline slope; model missing → rule engine; weather down → clean 503.
- **Safety-first messaging.** Warnings say "elevated risk detected", never certainty; every
  response carries the disclaimer (see docs/DISCLAIMER.md).
- **Prototype data honesty.** Static factors and hotspots are curated baselines, clearly marked
  as replaceable with real rasters/inventories.

## Scalability notes

- SQLite → PostgreSQL by setting `NER_DATABASE_URL` (SQLAlchemy ORM is portable; DDL in
  `database/schemas/db_schema.sql`).
- The in-memory caches and rate limiter are per-process; for multi-instance deployments swap
  them for Redis-backed implementations.
- Dashboard parallelizes the 8 state analyses with a ThreadPoolExecutor; add caching (e.g.
  `fastapi-cache`) or a scheduled pre-compute job before scaling users.
