# ⛰️ NER Landslide AI

**AI-Based Early Warning and Landslide Risk Monitoring System for the North Eastern Region of India**

Monitors all 8 NER states — **Assam, Arunachal Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura** —
combining static terrain susceptibility with **live weather** into an explainable 0–100 landslide risk score.

> ⚠️ **Prototype decision-support tool.** Scores are *not* scientifically validated predictions.
> HIGH/CRITICAL means *“elevated landslide risk detected based on available data”* — never that a
> landslide is certain. Always follow official NDMA/SDMA/GSI/IMD and local-authority advisories.

---

## ✨ Features

- **Live dashboard** — weather + risk snapshot for all 8 states, auto-refresh every 5 minutes
- **Interactive map** (Leaflet + OpenStreetMap) — state markers, hotspot markers, click-to-analyze
- **Location analysis** — click anywhere → live weather, terrain slope, 9 weighted factors,
  *why* the level was assigned, and safety recommendations
- **Risk classification** — 🟢 LOW (0–24) · 🟡 MODERATE (25–49) · 🟠 HIGH (50–74) · 🔴 CRITICAL (75–100)
  (thresholds configurable via env vars)
- **Early-warning alerts** — broadcast feed for HIGH/CRITICAL + per-user in-app notifications when a
  saved location's risk rises (e.g. MODERATE → HIGH); email/SMS hooks ready for a provider
- **User accounts** — JWT auth (register/login/logout/profile), saved “My Locations”, previous risk
  checks, notification preferences
- **Historical observations** — every analysis is stored (rainfall, soil moisture, slope, score,
  level) and surfaced as trends/charts
- **ML module** — full pipeline (synthetic dataset generator → preprocessing → training →
  prediction) with Logistic Regression, Random Forest, Gradient Boosting, optional XGBoost;
  evaluated on accuracy/precision/recall/F1/ROC-AUC/confusion matrix; served at `/api/risk/predict`
- **Security** — PBKDF2 password hashing, JWT, input validation (Pydantic), CORS allow-list,
  per-IP rate limiting, secrets via environment variables

## 🧱 Tech stack

| Layer | Tech |
|---|---|
| Frontend | React 18 · Vite · React Leaflet · Leaflet · CSS |
| Backend | Python · FastAPI · Pydantic · Requests · SQLAlchemy |
| Weather/Terrain | Open-Meteo (no API key) · Copernicus DEM via elevation API |
| ML | pandas · NumPy · scikit-learn · joblib (XGBoost optional) |
| Database | SQLite by default · PostgreSQL-ready (`NER_DATABASE_URL`) |
| Auth | JWT (PyJWT) + salted PBKDF2 password hashing |
| Maps | Leaflet + OpenStreetMap |

## 🚀 Quick start

### 1) Backend (port 8000)
```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
# Swagger UI: http://127.0.0.1:8000/docs
```

### 2) Train the ML model (optional but recommended)
```powershell
pip install -r ml/requirements.txt
python ml/datasets/generate_synthetic_dataset.py
python ml/training/train_model.py
# → ml/models/landslide_model.joblib (auto-loaded by the backend)
```

### 3) Frontend (port 5173)
```powershell
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

Windows helper scripts: `run_backend.bat`, `run_frontend.bat`, `start_all.bat`.

## 🔧 Configuration

Copy `.env.example` → `.env` and set at minimum `NER_SECRET_KEY` for anything beyond local dev.
Risk weights (`NER_W_*`), thresholds (`NER_THRESHOLD_*`), CORS, rate limit and database URL are
all environment-configurable — see `backend/utils/config.py`.

## 📡 Key API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Health check |
| GET | `/api/states` | The 8 NER states + coordinates |
| GET | `/api/weather/{state}` | Current weather at a state capital |
| GET | `/api/dashboard` | Live weather + risk for all 8 states |
| POST | `/api/risk/analyze` | Analyze any lat/lon (score, level, factors, explanation) |
| POST | `/api/risk/predict` | Trained ML model output (+ rule-based comparison) |
| GET | `/api/history/{location}` | Historical observations (state or "lat,lon") |
| POST | `/api/auth/register` · `/api/auth/login` | JWT authentication |
| POST | `/api/alerts/subscribe` | Notification preferences (auth) |
| GET/POST/DELETE | `/api/locations...` | Saved locations CRUD (auth) |

Full list with request/response shapes: `docs/API.md` · Swagger: `/docs`.

## 📁 Project structure

```
NER-Landslide-AI/
├── backend/          # FastAPI app (routes/, services/, models/, utils/)
├── frontend/         # React + Vite (components/, pages/, services/)
├── ml/               # datasets/ preprocessing/ training/ models/ prediction/
├── database/         # schemas/ + local SQLite file
├── docs/             # API.md · ARCHITECTURE.md · DISCLAIMER.md
└── README.md
```

## ⚖️ Risk model (prototype rule engine)

| Factor | Weight |
|---|---|
| Rainfall (current + 24h + 72h) | 30% |
| Slope (DEM-derived estimate) | 20% |
| Soil moisture (0–1 cm) | 15% |
| Elevation | 10% |
| Soil / Geology | 10% |
| Land cover | 5% |
| Historical landslides | 5% |
| Drainage | 3% |
| Road cutting | 2% |

Weights are **conceptual starting points**, configurable, and **not field-validated** — see
`docs/DISCLAIMER.md` for the full safety/limitations statement.

## 🗺️ Roadmap

Satellite imagery · full DEM raster analysis · rainfall radar · advanced ML + time-series
forecasting · district-level monitoring · susceptibility maps · community reporting · mobile app ·
government alert integration.
