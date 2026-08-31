import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Loader from './Loader.jsx'
import RiskGauge from './RiskGauge.jsx'
import TrendChart from './TrendChart.jsx'
import { api } from '../services/api.js'
import { levelStyle } from '../services/risk.js'

/**
 * Compact detail view for a state selected from the Dashboard's
 * "Select a state" picker: live weather, risk score, why-explanation,
 * recommendations and the stored risk trend — with a link to the full page.
 */
export default function StateDetailCard({ stateId }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let live = true
    setData(null)
    setError(null)
    api
      .get(`/api/states/${stateId}`, false)
      .then(async (s) => {
        const [analysis, history] = await Promise.all([
          api.post(
            '/api/risk/analyze',
            { lat: s.lat, lon: s.lon, state: s.name, name: s.capital },
            false,
          ),
          api.get(`/api/history/${encodeURIComponent(s.id)}`, false).catch(() => null),
        ])
        if (!live) return
        setData({ state: s, analysis, history })
      })
      .catch((e) => {
        if (live) setError(e.message)
      })
    return () => {
      live = false
    }
  }, [stateId])

  if (error) return <div className="card form-error">{error}</div>
  if (!data) {
    return <div className="card"><Loader label="Fetching selected state details…" /></div>
  }

  const { state: s, analysis, history } = data
  const lv = levelStyle(analysis.risk.level)
  const w = analysis.weather
  const trend = (history?.observations || []).slice().reverse()

  return (
    <div className="card">
      <div
        style={{
          display: 'flex', justifyContent: 'space-between', gap: 10,
          flexWrap: 'wrap', alignItems: 'flex-start',
        }}
      >
        <div>
          <h2 style={{ marginBottom: 2 }}>📍 {s.name} — State Details</h2>
          <div className="muted">
            Capital: {s.capital} · {s.lat}°N, {s.lon}°E · avg elevation ~{s.avg_elevation_m} m ·
            annual rainfall ~{s.annual_rainfall_mm} mm
          </div>
        </div>
        <Link className="btn btn-primary btn-sm" to={`/state/${s.id}`}>
          Open full page →
        </Link>
      </div>

      {analysis.warning && (
        <div className="alert-banner" style={{ borderLeftColor: lv.color, background: lv.bg, marginTop: 12 }}>
          <h4 style={{ color: lv.color }}>{analysis.warning.title}</h4>
          <pre>{analysis.warning.message}</pre>
        </div>
      )}

      <div className="grid grid-2" style={{ marginTop: 14 }}>
        <div>
          <RiskGauge score={analysis.risk.score} level={analysis.risk.level} />
          <p style={{ marginBottom: 6 }}>{analysis.explanation}</p>
          <div className="muted" style={{ marginBottom: 8 }}>
            Top contributing factors: <strong>{analysis.top_contributors?.join(', ') || '—'}</strong>
          </div>
          <h3>Recommended actions</h3>
          <ul className="reco-list">
            {analysis.recommendations.slice(0, 3).map((r) => <li key={r}>{r}</li>)}
          </ul>
        </div>
        <div>
          <h3>🌦️ Live weather at capital</h3>
          <div className="wx-row" style={{ flexDirection: 'column', gap: 5, marginBottom: 12 }}>
            <span>🌡️ Temperature: <strong>{w.temperature_c ?? '—'} °C</strong> · 💧 Humidity: <strong>{w.relative_humidity_pct ?? '—'} %</strong></span>
            <span>🌧️ Now: <strong>{w.precipitation_mm ?? 0} mm/h</strong> · ☔ 24h: <strong>{w.rain_24h_mm ?? '—'} mm</strong> · 72h: <strong>{w.rain_72h_mm ?? '—'} mm</strong></span>
            <span>💨 Wind: <strong>{w.wind_speed_kmph ?? '—'} km/h</strong> · 🌱 Soil moisture: <strong>{w.soil_moisture_m3m3 ?? '—'} m³/m³</strong></span>
            <span>⛰️ Elevation: <strong>{w.elevation_m ?? '—'} m</strong> · 📐 Slope: <strong>{w.slope_deg ?? '—'}°</strong></span>
            <span>☁️ Condition: <strong>{w.weather_condition ?? '—'}</strong></span>
          </div>
          <h3>📈 Risk trend (stored observations)</h3>
          <TrendChart points={trend.map((o) => ({ score: o.risk_score }))} />
        </div>
      </div>

      <p className="muted" style={{ marginTop: 10 }}>
        ⚠️ {s.historical_note} · Updated: {new Date(analysis.generated_at).toLocaleString()}
      </p>
    </div>
  )
}
