export default function WeatherPanel({ weather }) {
  if (!weather) return null
  const rows = [
    ['🌡️ Temperature', weather.temperature_c != null ? `${weather.temperature_c} °C` : '—'],
    ['💧 Humidity', weather.relative_humidity_pct != null ? `${weather.relative_humidity_pct} %` : '—'],
    ['🌧️ Precipitation (now)', weather.precipitation_mm != null ? `${weather.precipitation_mm} mm/h` : '—'],
    ['☔ Rain last 24h', weather.rain_24h_mm != null ? `${weather.rain_24h_mm} mm` : '—'],
    ['☔ Rain last 72h', weather.rain_72h_mm != null ? `${weather.rain_72h_mm} mm` : '—'],
    ['💨 Wind', weather.wind_speed_kmph != null ? `${weather.wind_speed_kmph} km/h` : '—'],
    ['🌱 Soil moisture', weather.soil_moisture_m3m3 != null ? `${weather.soil_moisture_m3m3} m³/m³` : '—'],
    ['⛰️ Elevation', weather.elevation_m != null ? `${weather.elevation_m} m` : '—'],
  ]
  return (
    <div>
      <h3>{weather.weather_condition ?? 'Weather'}</h3>
      <div className="wx-row" style={{ flexDirection: 'column', gap: 6 }}>
        {rows.map(([k, v]) => (
          <span key={k}><strong>{k}:</strong> {v}</span>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 10 }}>
        Source: {weather.source} · Observed: {weather.observed_at ?? '—'} · Fetched: {weather.fetched_at}
      </p>
    </div>
  )
}
