import { useCallback, useEffect, useState } from 'react'
import Loader from '../components/Loader.jsx'
import RiskBadge from '../components/RiskBadge.jsx'
import TrendChart from '../components/TrendChart.jsx'
import { api } from '../services/api.js'

const STATES = ['assam', 'arunachal-pradesh', 'manipur', 'meghalaya',
  'mizoram', 'nagaland', 'sikkim', 'tripura']

export default function HistoryPage() {
  const [query, setQuery] = useState('meghalaya')
  const [custom, setCustom] = useState('')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async (q) => {
    if (!q) return
    setLoading(true)
    setError(null)
    try {
      setData(await api.get(`/api/history/${encodeURIComponent(q)}`, false))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(query)
  }, [load, query])

  const submit = (e) => {
    e.preventDefault()
    if (custom.trim()) load(custom.trim())
  }

  const trend = (data?.observations || []).slice().reverse()

  return (
    <div className="page container">
      <h1>Historical Risk Observations</h1>
      <p className="subtitle">
        Stored environmental + risk observations — search by state or by coordinates ("lat,lon").
      </p>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="form" style={{ flexDirection: 'row', flexWrap: 'wrap', alignItems: 'flex-end', maxWidth: 'none' }}>
          <div className="field">
            <label htmlFor="state-select">State</label>
            <select id="state-select" value={query} onChange={(e) => setQuery(e.target.value)}>
              {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="field" style={{ flex: 1, minWidth: 240 }}>
            <label htmlFor="custom-q">Or search coordinates / location name</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                id="custom-q"
                placeholder='e.g. "25.58,91.89" or "Shillong"'
                value={custom}
                onChange={(e) => setCustom(e.target.value)}
              />
              <button className="btn btn-primary" onClick={submit}>Search</button>
            </div>
          </div>
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}
      {loading && <Loader label="Loading observations…" />}
      {data && (
        <>
          <div className="grid grid-stats" style={{ marginBottom: 16 }}>
            <div className="card stat-card">
              <div className="stat-value">{data.count}</div>
              <div className="stat-label">Observations</div>
            </div>
            <div className="card stat-card"><div className="stat-value" style={{ color: '#15803d' }}>{data.level_counts.LOW}</div><div className="stat-label">🟢 LOW</div></div>
            <div className="card stat-card"><div className="stat-value" style={{ color: '#a16207' }}>{data.level_counts.MODERATE}</div><div className="stat-label">🟡 MODERATE</div></div>
            <div className="card stat-card"><div className="stat-value" style={{ color: '#c2410c' }}>{data.level_counts.HIGH}</div><div className="stat-label">🟠 HIGH</div></div>
            <div className="card stat-card"><div className="stat-value" style={{ color: '#b91c1c' }}>{data.level_counts.CRITICAL}</div><div className="stat-label">🔴 CRITICAL</div></div>
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <h2>📈 Risk score trend — {data.location}</h2>
            <TrendChart points={trend.map((o) => ({ score: o.risk_score }))} />
          </div>

          <div className="card">
            <h2>🗒️ Observation log</h2>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>When</th><th>Location</th><th>Rain 24h</th>
                    <th>Soil moisture</th><th>Slope</th><th>Score</th><th>Level</th>
                  </tr>
                </thead>
                <tbody>
                  {data.observations.map((o) => (
                    <tr key={o.id}>
                      <td>{new Date(o.created_at).toLocaleString()}</td>
                      <td>{o.location_name}</td>
                      <td>{o.rainfall_24h_mm ?? '—'} mm</td>
                      <td>{o.soil_moisture ?? '—'}</td>
                      <td>{o.slope_deg ?? '—'}°</td>
                      <td>{o.risk_score}</td>
                      <td><RiskBadge level={o.risk_level} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
