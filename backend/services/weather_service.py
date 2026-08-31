"""Live weather + terrain service built on Open-Meteo (free, no API key).

- Current conditions: temperature, humidity, precipitation, wind, weather code
- Recent rainfall: 24h / 72h accumulation from hourly precipitation
- Soil moisture: top layer (0-1 cm) from hourly data
- Elevation + slope: Open-Meteo elevation API sampled at 5 points

Responses are cached in-memory with a TTL to protect the public API and keep
the dashboard snappy. Data source + timestamps are returned to the UI.
"""
import math
import time
from datetime import datetime, timezone

import requests

from utils.config import WEATHER_API_TIMEOUT, WEATHER_CACHE_TTL_SECONDS

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

_cache: dict[tuple, tuple[float, dict]] = {}


class WeatherServiceError(RuntimeError):
    """Raised when the upstream weather/elevation service cannot be reached."""


_RETRY_STATUS = {429, 500, 502, 503, 504}


def _get_upstream(url: str, params: dict, attempts: int = 3):
    """GET with short retries. Open-Meteo occasionally rate-limits or briefly
    fails shared datacenter egress IPs (e.g. Render free tier); a small backoff
    turns those transient blips into successful responses instead of 503s."""
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            resp = requests.get(url, params=params, timeout=WEATHER_API_TIMEOUT)
            if resp.status_code in _RETRY_STATUS and attempt < attempts - 1:
                time.sleep(0.8 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < attempts - 1:
                time.sleep(0.8 * (attempt + 1))
    raise WeatherServiceError(f"Upstream unavailable after {attempts} attempts: {last_exc}")


def _cache_get(key):
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < WEATHER_CACHE_TTL_SECONDS:
        return hit[1]
    return None


def _cache_put(key, value):
    _cache[key] = (time.monotonic(), value)
    if len(_cache) > 800:  # rudimentary cleanup
        cutoff = time.monotonic() - WEATHER_CACHE_TTL_SECONDS
        for k in [k for k, (t, _) in _cache.items() if t < cutoff]:
            _cache.pop(k, None)


def fetch_current_weather(lat: float, lon: float) -> dict:
    """Current conditions + recent rainfall accumulation + soil moisture."""
    key = ("wx", round(lat, 3), round(lon, 3))
    cached = _cache_get(key)
    if cached:
        return cached

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
            "rain,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
        ),
        "hourly": "precipitation,soil_moisture_0_to_1cm",
        "past_days": "3",
        "forecast_days": "1",
        "timezone": "auto",
    }
    try:
        resp = _get_upstream(FORECAST_URL, params)
        data = resp.json()
    except WeatherServiceError:
        raise
    except Exception as exc:
        raise WeatherServiceError(f"Weather service unavailable: {exc}") from exc

    try:
        cur, hourly = data["current"], data["hourly"]
        times = [datetime.fromisoformat(t) for t in hourly["time"]]
        now = datetime.fromisoformat(cur["time"])
        precip = hourly["precipitation"]
        soil = hourly.get("soil_moisture_0_to_1cm", [])

        past_idx = [i for i, t in enumerate(times) if t <= now]
        last = past_idx[-1] if past_idx else len(times) - 1

        def rain_sum(hours: int) -> float:
            start = max(0, last - hours + 1)
            return round(sum(p or 0.0 for p in precip[start: last + 1]), 2)

        soil_now = next((soil[i] for i in range(min(last, len(soil) - 1), -1, -1)
                         if i >= 0 and soil[i] is not None), None)

        result = {
            "latitude": lat, "longitude": lon,
            "temperature_c": cur.get("temperature_2m"),
            "apparent_temperature_c": cur.get("apparent_temperature"),
            "relative_humidity_pct": cur.get("relative_humidity_2m"),
            "precipitation_mm": cur.get("precipitation"),
            "weather_code": cur.get("weather_code"),
            "weather_condition": WEATHER_CODES.get(cur.get("weather_code"), "Unknown"),
            "cloud_cover_pct": cur.get("cloud_cover"),
            "wind_speed_kmph": cur.get("wind_speed_10m"),
            "wind_direction_deg": cur.get("wind_direction_10m"),
            "wind_gusts_kmph": cur.get("wind_gusts_10m"),
            "rain_1h_mm": rain_sum(1), "rain_24h_mm": rain_sum(24), "rain_72h_mm": rain_sum(72),
            "soil_moisture_m3m3": round(soil_now, 4) if soil_now is not None else None,
            "timezone": data.get("timezone"),
            "observed_at": cur.get("time"),
            "source": "Open-Meteo (https://open-meteo.com)",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise WeatherServiceError(f"Unexpected weather payload: {exc}") from exc

    _cache_put(key, result)
    return result


def fetch_elevation_and_slope(lat: float, lon: float) -> dict:
    """Elevation at the point + estimated slope from a 5-point sample (~220 m).

    Coarse terrain proxy suitable for a prototype; replace with a real DEM
    (SRTM/Copernicus raster + GDAL) for production-grade slope analysis.
    """
    key = ("dem", round(lat, 4), round(lon, 4))
    cached = _cache_get(key)
    if cached:
        return cached

    d = 0.001  # ~110 m per step
    params = {
        "latitude": ",".join(f"{v:.6f}" for v in [lat, lat + d, lat - d, lat, lat]),
        "longitude": ",".join(f"{v:.6f}" for v in [lon, lon, lon, lon + d, lon - d]),
    }
    try:
        resp = _get_upstream(ELEVATION_URL, params)
        center, north, south, east, west = (resp.json().get("elevation", []) + [None] * 5)[:5]
    except WeatherServiceError:
        raise
    except Exception as exc:
        raise WeatherServiceError(f"Elevation service unavailable: {exc}") from exc

    slope_deg = None
    if None not in (center, north, south, east, west):
        dy = 2 * d * 110_540.0
        dx = 2 * d * 111_320.0 * math.cos(math.radians(lat))
        dzdx, dzdy = (east - west) / dx, (north - south) / dy
        slope_deg = round(min(70.0, math.degrees(math.atan(math.hypot(dzdx, dzdy)))), 2)

    result = {
        "elevation_m": center,
        "slope_deg": slope_deg,
        "slope_basis": "5-point elevation sample (~220 m grid)",
        "terrain_source": "Open-Meteo elevation API (Copernicus DEM GLO-90)",
    }
    _cache_put(key, result)
    return result


def get_live_conditions(lat: float, lon: float) -> dict:
    """Combined weather + terrain snapshot used by the risk engine."""
    merged = dict(fetch_current_weather(lat, lon))
    terrain = fetch_elevation_and_slope(lat, lon)
    merged["elevation_m"] = terrain["elevation_m"]
    merged["slope_deg"] = terrain["slope_deg"]
    merged["terrain_source"] = terrain["terrain_source"]
    return merged

