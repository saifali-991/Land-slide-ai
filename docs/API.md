# API Reference — NER Landslide AI

Base URL: `http://127.0.0.1:8000` · Interactive docs: **`/docs`** (Swagger) · `/redoc`

Authentication: `Authorization: Bearer <token>` (obtain via register/login).
**Public (no token):** `/`, `/api/states*`, `/api/weather/*`, `/api/dashboard`, `/api/risk/*`,
`/api/history/*`, `/api/alerts/latest`. **Auth required:** everything under `/api/auth/me`,
`/api/locations*`, `/api/alerts/{subscribe,preferences,notifications}`.

---

## GET `/` — health check
```json
{"status": "ok", "service": "NER Landslide AI API", "version": "1.0.0", "env": "development", "time": "...", "docs": "/docs"}
```

## GET `/api/states` — the 8 NER states
```json
{"count": 8, "states": [{"id": "assam", "name": "Assam", "capital": "Dispur (Guwahati)",
  "lat": 26.1445, "lon": 91.7362, "avg_elevation_m": 70, "geology": "...", "land_cover": "...",
  "annual_rainfall_mm": 2800, "historical_note": "...", "known_hotspots": ["..."]}]}
```

## GET `/api/states/{state_id}` — full static profile (bbox, scores, hotspot coordinates)

## GET `/api/weather/{state}` — current weather at the capital
```json
{"state": "Meghalaya", "capital": "Shillong", "lat": 25.5788, "lon": 91.8933,
 "temperature_c": 21.4, "relative_humidity_pct": 78, "precipitation_mm": 1.2,
 "weather_condition": "Moderate rain", "wind_speed_kmph": 12.6,
 "rain_1h_mm": 1.2, "rain_24h_mm": 34.5, "rain_72h_mm": 88.1,
 "soil_moisture_m3m3": 0.34, "observed_at": "...", "source": "Open-Meteo (https://open-meteo.com)", "fetched_at": "..."}
```
→ `503` when the upstream weather service is unreachable.

## GET `/api/dashboard` — live snapshot for all 8 states
```json
{"generated_at": "...",
 "summary": {"states_monitored": 8, "counts": {"LOW": 3, "MODERATE": 3, "HIGH": 2, "CRITICAL": 0},
              "weather_source": "Open-Meteo (https://open-meteo.com)"},
 "states": [{"id": "...", "name": "...", "capital": "...", "lat": ..., "lon": ...,
              "weather": {"temperature_c": ..., "relative_humidity_pct": ..., "precipitation_mm": ...,
                           "rain_24h_mm": ..., "wind_speed_kmph": ..., "soil_moisture_m3m3": ...,
                           "weather_condition": "...", "observed_at": "..."},
              "risk": {"score": 62.3, "level": "HIGH"}, "top_contributors": ["Rainfall", "Slope"],
              "updated_at": "..."}]}
```
Also persists deduplicated history rows (≥30 min apart) and HIGH/CRITICAL broadcast alerts
(deduplicated ≥3 h apart per state+level).

## POST `/api/risk/analyze` — analyze any location
Request:
```json
{"lat": 25.58, "lon": 91.89, "state": "meghalaya", "name": "Shillong", "save": false}
```
`state` optional (auto-detected from coordinates) · `save: true` stores the location for the
logged-in user. Response includes:
- `location` {name, state, state_id, lat, lon, susceptibility_note}
- `weather` (full live conditions incl. elevation, slope, sources, timestamps)
- `risk` {score (0–100), level, thresholds, model_type}
- `factors[]` — each {factor, label, score, detail, weight, contribution} sorted by contribution
- `top_contributors`, `trigger_notes`, `explanation` (plain-language WHY)
- `recommendations[]`, `warning` (title + message, HIGH/CRITICAL only), `disclaimer`
- `check_id`, `created_at`, `saved_location_id`

## POST `/api/risk/predict` — trained ML model
Request: `{"lat": ..., "lon": ..., "state": null}`
Response: `input_factors`, `ml` {probability_elevated_risk, risk_score, risk_level, model_type,
metrics{accuracy, precision, recall, f1, roc_auc, confusion_matrix}, trained_at} — or `null` when
no model is trained yet — plus `rule_based` comparison, `model_info`, `disclaimer`.

## GET `/api/history/{location}` — historical observations
`location` = state id/name (e.g. `meghalaya`) **or** `"lat,lon"` (match ±0.05°).
```json
{"location": "Meghalaya", "count": 12, "level_counts": {"LOW": 4, "MODERATE": 5, "HIGH": 3, "CRITICAL": 0},
 "latest": {...}, "observations": [{created_at, location_name, state_name, lat, lon, temperature_c,
 humidity_pct, rainfall_24h_mm, rainfall_72h_mm, soil_moisture, elevation_m, slope_deg,
 risk_score, risk_level, observed_landslide, model_type}]}
```
`GET /api/history/me` (auth) — the logged-in user's own checks.

## POST `/api/auth/register` → 201
```json
{"name": "Asha", "email": "asha@example.com", "password": "min-8-chars", "role": "public"}
```
→ `{access_token, token_type: "bearer", user{id, name, email, role, created_at}}`
Roles: `public` | `authority` | `researcher`.

## POST `/api/auth/login` → `{access_token, token_type, user}` · `401` on bad credentials
## GET/PATCH `/api/auth/me` — profile (name/password update)

## Alerts
- `POST /api/alerts/subscribe` (auth) — `{"in_app": true, "email": false, "email_address": null, "sms": false, "min_level": "HIGH"}`
- `GET /api/alerts/preferences` (auth)
- `GET /api/alerts/notifications` (auth) — `{unread, notifications[]}`
- `POST /api/alerts/notifications/read` (auth) — optional `{"ids": [1,2]}`
- `GET /api/alerts/latest` (public) — recent broadcast HIGH/CRITICAL alerts

## Saved locations (auth)
`GET /api/locations` · `POST /api/locations` `{name, lat, lon, state?, notes?}` ·
`DELETE /api/locations/{id}` · `POST /api/locations/{id}/check` (re-analyze → snapshot update →
change notification when risk rises, e.g. MODERATE → HIGH)

## Errors & limits
`400` validation · `401` auth · `404` unknown state/location · `429` rate limited ·
`503` weather service down · `500` internal. Body: `{"detail": "..."}`.
Rate limit: 120 req/min/IP (configurable); `/`, `/docs`, `/openapi.json` exempt.
