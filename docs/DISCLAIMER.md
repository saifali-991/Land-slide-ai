# ⚠️ Disclaimer & Safety Design — NER Landslide AI

## What this system is

NER Landslide AI is a **prototype risk-monitoring and decision-support tool**. It combines
publicly available weather data, coarse terrain estimates and curated static susceptibility
baselines into an indicative 0–100 landslide risk score for locations in the North Eastern
Region of India.

## What this system is NOT

- It is **not** an early-warning system certified by any government agency.
- It does **not** predict that a landslide will occur at a specific place or time.
- It does **not** replace GSI surveys, IMD nowcasts, NDMA/SDMA warnings, physical sensors,
  or the judgement of local authorities.
- The risk weights, thresholds and the ML model are **not scientifically validated** against a
  real landslide inventory. The bundled ML model is trained on **synthetic** data for pipeline
  demonstration only.

## How the UI communicates risk

- A HIGH or CRITICAL indicator is always phrased as *“elevated landslide risk detected based on
  available data”* — never as a certainty.
- Every analysis carries the disclaimer and pointers to official advisories.
- Notifications explicitly tell users to follow official disaster-management instructions.

## Data limitations (prototype)

| Input | Source | Limitation |
|---|---|---|
| Weather, rainfall, soil moisture | Open-Meteo | Model data, not rain gauges; soil moisture is top-layer (0–1 cm) |
| Elevation / slope | Open-Meteo elevation API (Copernicus DEM GLO-90, 5-point sample) | Very coarse (~220 m grid) slope proxy |
| Soil / geology, land cover, drainage, road cutting | Curated state-level baselines + corridor proximity proxy | Not real rasters; no district-level resolution |
| Historical landslides | Embedded indicative hotspot list (public GSI/news reporting) | Not an authoritative inventory |

## Before any operational use

1. Replace synthetic ML training data with a real, geo-referenced landslide inventory
   (e.g. GSI, NASA cooperative landslide reporting) and re-validate.
2. Calibrate thresholds against historical events; publish precision/recall and
   false-alarm/missed-event analysis — not just accuracy.
3. Use real DEM + soil + land-cover rasters (SRTM/Copernicus, NBSS&LUP, ISRO Bhuvan).
4. Obtain official alerting integration and legal review.
5. Follow the security checklist in `README.md` (HTTPS, secrets, PostgreSQL, etc.).

## Emergency guidance for users

If you are in an area with elevated risk: avoid steep slopes, road cuttings and stream banks
during/after heavy rain, follow instructions from local authorities, and in an emergency contact
your State Disaster Management Authority or local administration immediately.
