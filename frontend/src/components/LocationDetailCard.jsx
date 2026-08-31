import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import FactorBreakdown from './FactorBreakdown.jsx'
import Loader from './Loader.jsx'
import RiskGauge from './RiskGauge.jsx'
import TrendChart from './TrendChart.jsx'
import { api } from '../services/api.js'
import { levelStyle } from '../services/risk.js'

/**
 * Detail view for an arbitrary point pinned on the dashboard map — anywhere
 * in India. Shows the full risk analysis (weather, gauge, factors,
 * recommendations, trend) with a link to the interactive Analyze page.
 */
export default function LocationDetailCard({ lat, lon }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let live = true
    setData(null)
    setError(null)
    const name = `Pinned location ${lat.toFixed(4)}, ${lon.toFixed(4)}`
    api
      .post('/api/risk/analyze', { lat, lon, name }, false)
      .then(async (analysis) => {
        const history = await api
          .get(`/api/history/${lat},${lon}`, false)
          .catch(() => null)
        if (!live) return
        setData({ analysis, history })
      })
      .catch((e) => {
        if (live) setError(e.message)
      })
    return () => {
      live = false
    }
  }, [lat, lon])

  if (error) return <div className="card form-error">{error}</div>
  if (!data) return <div className="card"><Loader label="Analyzing pinned point…" /></div>

  const { analysis, history } = data
  const lv = levelStyle(analysis.risk.level)
  const w = analysis.weather
  const trend = (history?.observations || []).slice().reverse()
  const outsideNER = analysis.location.state_id === 'outside-ner'

  return (
    <div className="card">
      <div
        style={{
          display: 'flex', justifyContent: 'space-between', gap: 10,
          flexWrap: 'wrap', alignItems: 'flex-start',
        }}
      >
        <div>
          <h2 style={{ marginBottom: 2 }}>
            📍 Pinned Location — {lat.toFixed(4)}, {lon.toFixed(4)}
          </h2>
          <div className="muted">
            Region: <strong>{analysis.location.state}</strong> · {analysis.location.lat}, {analysis.location.lon}
          </div>
        </div>
        <Link className="btn btn-primary btn-sm" to={`/analyze?lat=${lat}&lon=${lon}`}>
          Open in Analyze page →
        </Link>
      </div>

      {outsideNER && (
        <div
          className="form-error"
          style={{ marginTop: 12, background: '#fef3c7', color: '#92400e' }}
        >
          ⚠️ Ye point 8 NER states ke bahar hai — susceptibility baselines (geology, land cover
          etc.) sirf NER ke liye curated hain, yahan generic values use ho rahi hain. Weather
          aur terrain data real hai.
        </div>
      )}

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
          <h3>🌦️ Live weather at this point</h3>
          <div className="wx-row" style={{ flexDirection: 'column', gap: 5, marginBottom: 12 }}>
            <span>🌡️ Temperature: <strong>{w.temperature_c ?? '—'} °C</strong> · 💧 Humidity: <strong>{w.relative_humidity_pct ?? '—'} %</strong></span>
            <span>🌧️ Now: <strong>{w.precipitation_mm ?? 0} mm/h</strong> · ☔ 24h: <strong>{w.rain_24h_mm ?? '—'} mm</strong> · 72h: <strong>{w.rain_72h_mm ?? '—'} mm</strong></span>
            <span>💨 Wind: <strong>{w.wind_speed_kmph ?? '—'} km/h</strong> · 🌱 Soil moisture: <strong>{w.soil_moisture_m3m3 ?? '—'} m³/m³</strong></span>
            <span>⛰️ Elevation: <strong>{w.elevation_m ?? '—'} m</strong> · 📐 Slope: <strong>{w.slope_deg ?? '—'}°</strong></span>
            <span>☁️ Condition: <strong>{w.weather_condition ?? '—'}</strong></span>
          </div>
          <h3>📈 Risk trend at this point</h3>
          <TrendChart points={trend.map((o) => ({ score: o.risk_score }))} />
        </div>
      </div>

      <div style={{ marginTop: 8 }}>
        <h3>⚖️ Full factor breakdown</h3>
        <FactorBreakdown factors={analysis.factors} />
      </div>

      <p className="muted" style={{ marginTop: 10 }}>
        Updated: {new Date(analysis.generated_at).toLocaleString()}
      </p>
    </div>
  )
}
