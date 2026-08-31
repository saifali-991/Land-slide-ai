import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import FactorBreakdown from '../components/FactorBreakdown.jsx'
import Loader from '../components/Loader.jsx'
import MapView from '../components/MapView.jsx'
import RiskGauge from '../components/RiskGauge.jsx'
import TrendChart from '../components/TrendChart.jsx'
import WeatherPanel from '../components/WeatherPanel.jsx'
import { api } from '../services/api.js'
import { levelStyle } from '../services/risk.js'

export default function StateDetail() {
  const { stateId } = useParams()
  const [state, setState] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [history, setHistory] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let live = true
    setError(null)
    setState(null)
    setAnalysis(null)
    api
      .get(`/api/states/${stateId}`, false)
      .then(async (s) => {
        if (!live) return
        setState(s)
        const [a, h] = await Promise.all([
          api.post('/api/risk/analyze', { lat: s.lat, lon: s.lon, state: s.name, name: s.capital }, false),
          api.get(`/api/history/${encodeURIComponent(s.id)}`, false).catch(() => null),
        ])
        if (!live) return
        setAnalysis(a)
        setHistory(h)
      })
      .catch((e) => setError(e.message))
    return () => {
      live = false
    }
  }, [stateId])

  if (error) {
    return <div className="page container"><div className="form-error">{error}</div></div>
  }
  if (!state) {
    return <div className="page container"><Loader label="Loading state…" /></div>
  }

  const markers = [
    {
      key: 'cap', lat: state.lat, lon: state.lon,
      label: `${state.capital} (capital)`, color: '#0ea5e9', radius: 11,
    },
    ...state.known_hotspots.map((h) => ({
      key: h.name, lat: h.lat, lon: h.lon,
      label: `${h.name} — known landslide zone`, color: '#f97316', radius: 8,
    })),
  ]
  const trend = (history?.observations || []).slice().reverse()

  return (
    <div className="page container">
      <p className="muted"><Link to="/">← Back to dashboard</Link></p>
      <h1>{state.name}</h1>
      <p className="subtitle">
        {state.capital} · {state.lat}°N, {state.lon}°E · avg elevation ~{state.avg_elevation_m} m
      </p>

      {analysis ? (
        <>
          {analysis.warning && (
            <div
              className="alert-banner"
              style={{
                borderLeftColor: levelStyle(analysis.risk.level).color,
                background: levelStyle(analysis.risk.level).bg,
              }}
            >
              <h4 style={{ color: levelStyle(analysis.risk.level).color }}>{analysis.warning.title}</h4>
              <pre>{analysis.warning.message}</pre>
            </div>
          )}

          <div className="grid grid-2">
            <div className="card">
              <h2>📍 Capital — current risk</h2>
              <RiskGauge score={analysis.risk.score} level={analysis.risk.level} />
              <p>{analysis.explanation}</p>
              <h3>Recommended actions</h3>
              <ul className="reco-list">
                {analysis.recommendations.map((r) => <li key={r}>{r}</li>)}
              </ul>
            </div>
            <div className="card">
              <h2>🌦️ Live weather at capital</h2>
              <WeatherPanel weather={analysis.weather} />
            </div>
            <div className="card">
              <h2>⚖️ Main contributing factors</h2>
              <FactorBreakdown factors={analysis.factors} />
            </div>
            <div className="card">
              <h2>📈 Risk trend (stored observations)</h2>
              <TrendChart points={trend.map((o) => ({ score: o.risk_score }))} />
              <p className="muted">{history?.count ?? 0} stored observations</p>
            </div>
          </div>
        </>
      ) : (
        <Loader label="Analyzing capital location…" />
      )}

      <div className="card" style={{ marginTop: 16 }}>
        <h2>🗺️ {state.name} — capital &amp; known landslide hotspots</h2>
        <MapView markers={markers} center={{ lat: state.lat, lon: state.lon }} zoom={7} height={380} />
        <p className="muted">{state.historical_note}</p>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h2>🧭 Static susceptibility profile (prototype baselines)</h2>
        <div className="wx-row" style={{ flexDirection: 'column', gap: 6 }}>
          <span><strong>Geology:</strong> {state.geology} ({state.geology_score}/100)</span>
          <span><strong>Land cover:</strong> {state.land_cover} ({state.land_cover_score}/100)</span>
          <span><strong>Annual rainfall:</strong> ~{state.annual_rainfall_mm} mm</span>
          <span><strong>Drainage score:</strong> {state.drainage_score}/100 ·
            <strong> Road cutting score:</strong> {state.road_cutting_score}/100</span>
        </div>
      </div>

      <p className="disclaimer">{analysis?.disclaimer}</p>
    </div>
  )
}
