import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Loader from '../components/Loader.jsx'
import RiskBadge from '../components/RiskBadge.jsx'
import { api } from '../services/api.js'

export default function MyLocations() {
  const [locations, setLocations] = useState(null)
  const [error, setError] = useState(null)
  const [notes, setNotes] = useState({})

  const load = useCallback(() => {
    api.get('/api/locations')
      .then((d) => setLocations(d.locations))
      .catch((e) => setError(e.message))
  }, [])

  useEffect(load, [load])

  const refresh = async (id) => {
    setNotes((n) => ({ ...n, [id]: 'Checking…' }))
    try {
      const d = await api.post(`/api/locations/${id}/check`)
      const a = d.analysis
      setNotes((n) => ({
        ...n,
        [id]: d.notification
          ? `⚠️ ${d.notification.message.split('\n')[0]}`
          : `Updated: ${a.risk.level} (${a.risk.score}/100)`,
      }))
      load()
    } catch (e) {
      setNotes((n) => ({ ...n, [id]: e.message }))
    }
  }

  const remove = async (id) => {
    try {
      await api.del(`/api/locations/${id}`)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="page container">
      <h1>My Locations</h1>
      <p className="subtitle">Saved places with their latest available risk snapshot.</p>
      {error && <div className="form-error">{error}</div>}
      {!locations && !error && <Loader />}
      {locations && locations.length === 0 && (
        <div className="card">
          <p>
            No saved locations yet. Open <Link to="/analyze">Analyze Location</Link>, pick a
            place and press “Save this location”.
          </p>
        </div>
      )}
      <div className="grid grid-states">
        {(locations || []).map((l) => (
          <div className="card state-card" key={l.id}>
            <div className="head">
              <div>
                <Link to={`/analyze?lat=${l.lat}&lon=${l.lon}`}>{l.name}</Link>
                <div className="muted">{l.state_name || '—'} · {l.lat.toFixed(4)}, {l.lon.toFixed(4)}</div>
              </div>
              {l.last_risk_level
                ? <RiskBadge level={l.last_risk_level} score={l.last_risk_score} />
                : <span className="muted">not checked yet</span>}
            </div>
            <div className="muted">
              Last checked: {l.last_checked_at ? new Date(l.last_checked_at).toLocaleString() : 'never'}
            </div>
            {notes[l.id] && <div className="form-success">{notes[l.id]}</div>}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="btn btn-primary btn-sm" onClick={() => refresh(l.id)}>🔄 Refresh risk</button>
              <button className="btn btn-danger btn-sm" onClick={() => remove(l.id)}>🗑️ Remove</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
