# 🚀 Deploying NER Landslide AI to Render

This project deploys to Render as **two services**:

| Service | Type | What it is |
|---|---|---|
| `ner-landslide-api` | Web Service (Python) | FastAPI backend (`backend/`) |
| `ner-landslide-frontend` | Static Site | Vite build of `frontend/` → `dist/` |

A ready-made Blueprint is included at the repo root: [`render.yaml`](../render.yaml).
It wires both services (env vars, build/start commands, SPA rewrite) automatically.

---

## Step 0 — Prerequisites

- A **GitHub account** (Render pulls your code from GitHub/GitLab/Bitbucket).
- The trained ML model `ml/models/landslide_model.joblib` **must be committed** to git —
  the backend loads it from the repo at startup (it is tiny, ~2 KB, and not gitignored).
- `backend/requirements.txt` already includes the ML runtime deps
  (`numpy`, `scikit-learn`, `joblib`) needed to serve `/api/risk/predict`.

## Step 1 — Push the repo to GitHub

```bash
git init -b main                # skip if already a git repo
git add .
git commit -m "NER Landslide AI - initial commit"
```

Then create an **empty** repository on https://github.com/new (name e.g. `NER-Landslide-AI`,
no README/.gitignore — the repo already has them) and push:

```bash
git remote add origin https://github.com/<your-username>/NER-Landslide-AI.git
git push -u origin main
```

## Step 2 — Deploy via the Blueprint (recommended)

1. Go to https://dashboard.render.com → **New +** → **Blueprint**.
2. Connect your GitHub account if asked, then pick the `NER-Landslide-AI` repo.
3. Render detects `render.yaml` and shows both services. Click **Apply**.
4. Wait for both deploys to finish (first build installs Python + Node deps, ~3–5 min).

> Prefer manual setup? See [Manual setup](#manual-setup-no-blueprint) below for the
> exact settings to enter for each service.

## Step 3 — Point the two services at each other

The blueprint guesses the default URLs. **If Render used different URLs**
(e.g. it appended a random suffix because the name was taken), fix them once:

1. Open your **backend** service → copy its URL from the top of the page
   (e.g. `https://ner-landslide-api.onrender.com`).
2. Open your **frontend** static site → **Environment** → set
   `VITE_API_BASE_URL` = that backend URL → save (Render redeploys automatically).
3. Open your **frontend** URL → copy it → open the **backend** service →
   **Environment** → set `NER_CORS_ORIGINS` = your frontend URL → save.

## Step 4 — Verify

| Check | Expected |
|---|---|
| `https://<backend-url>/` | `{"status": "ok", ...}` |
| `https://<backend-url>/docs` | Swagger UI |
| `https://<frontend-url>/` | Dashboard with live state cards & map |
| Frontend → click any state | Live risk analysis (weather + factors) |
| Register/Login on the frontend | JWT auth works against the backend |

---

## Manual setup (no Blueprint)

### Service 1 — Backend (Web Service)

| Setting | Value |
|---|---|
| Type | **Web Service** |
| Root Directory | `backend` |
| Runtime | **Python 3** |
| Build Command | `pip install --upgrade pip && pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"` |
| Health Check Path | `/` |

Environment variables:

| Key | Value |
|---|---|
| `NER_ENV` | `production` |
| `NER_SECRET_KEY` | long random string (Render "Generate" button, or `python -c "import secrets; print(secrets.token_urlsafe(48))"`) |
| `NER_CORS_ORIGINS` | your frontend URL, e.g. `https://ner-landslide-frontend.onrender.com` |

> `--proxy-headers` is important: Render's proxy forwards requests, and without it the
> per-IP rate limiter would count **all** visitors as one IP.

### Service 2 — Frontend (Static Site)

| Setting | Value |
|---|---|
| Type | **Static Site** |
| Root Directory | `frontend` |
| Build Command | `npm ci && npm run build` |
| Publish Directory | `dist` |

Environment variables:

| Key | Value |
|---|---|
| `VITE_API_BASE_URL` | your backend URL, e.g. `https://ner-landslide-api.onrender.com` |

**Rewrite rule** (Settings → Redirects/Rewrites) so React Router works on refresh:

| Type | Source | Destination |
|---|---|---|
| Rewrite | `/*` | `/index.html` |

---

## ⚠️ Free-tier caveats (important)

- **Cold starts** — free Web Services sleep after ~15 minutes without traffic and take
  ~30–60 s to wake on the next request. The first click after a break feels slow; the
  frontend already retries/loads indicators, just wait a moment. (Static sites never sleep.)
- **Ephemeral database** — the backend defaults to SQLite, and free-tier disks are
  **wiped on every deploy/restart**: registered users, saved locations and history reset.
  For persistent data create a **Render PostgreSQL** database and set the env var:
  ```
  NER_DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
  ```
  Tables are created automatically on startup (SQLAlchemy `init_db()`); the reference
  DDL is in `database/schemas/db_schema.sql`.
- **512 MB RAM** — the backend + scikit-learn fits comfortably; keep **1 worker**
  (the start command above already does this). The in-memory rate limiter and caches
  are per-process, which is fine for a single instance.

## 🔄 Updating the deployment

Every `git push` to the connected branch auto-deploys both services.
The ML model only changes when you retrain and commit the new `.joblib` file:

```bash
python ml/datasets/generate_synthetic_dataset.py
python ml/training/train_model.py
git add ml/models/landslide_model.joblib
git commit -m "Retrain landslide model" && git push
```
