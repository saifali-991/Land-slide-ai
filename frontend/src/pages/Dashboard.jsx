import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import AlertBanner from '../components/AlertBanner.jsx'
import Loader from '../components/Loader.jsx'
import MapView from '../components/MapView.jsx'
import RiskBadge from '../components/RiskBadge.jsx'
import LocationDetailCard from '../components/LocationDetailCard.jsx'
import StateDetailCard from '../components/StateDetailCard.jsx'
import { api } from '../services/api.js'
import { levelStyle } from '../services/risk.js'

const REFRESH_MS = 5 * 60 * 1000 // auto-refresh weather/risk every 5 minutes

function StateCard({ s }) {
  const w = s.weather || {}
  return (
    <div className="card state-card">
      <div className="head">
        <div>
          <Link to={`/state/${s.id}`}>{s.name}</Link>
          <div className="muted">{s.capital} · {s.lat?.toFixed(2)}°N {s.lon?.toFixed(2)}°E</div>
        </div>
        <RiskBadge level={s.risk?.level} />
      </div>
      <div className="wx-row">
        <span>🌡️ {w.temperature_c ?? '—'}°C</span>
        <span>💧 {w.relative_humidity_pct ?? '—'}%</span>
        <span>🌧️ {w.precipitation_mm ?? 0} mm</span>
        <span>💨 {w.wind_speed_kmph ?? '—'} km/h</span>
        <span>🌱 {w.soil_moisture_m3m3 ?? '—'} m³/m³</span>
      </div>
      <div className="score-line">
        <span className="muted">Landslide risk</span>
        <span className="score-num" style={{ color: levelStyle(s.risk?.level).color }}>
          {s.risk?.score ?? '—'}
        </span>
      </div>
      <div className="muted">Top factors: {s.top_contributors?.join(', ') || '—'}</div>
      <div className="muted">Updated: {s.updated_at ? new Date(s.updated_at).toLocaleString() : '—'}</div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState('')
  const [stateNames, setStateNames] = useState([])
  const [focusedMeta, setFocusedMeta] = useState(null)
  const [locationPoint, setLocationPoint] = useState(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      setData(await api.get('/api/dashboard', false))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    api.get('/api/alerts/latest', false).then((d) => setAlerts(d.alerts || [])).catch(() => {})
    api.get('/api/states', false).then((d) => setStateNames(d.states)).catch(() => {})
    const t = setInterval(load, REFRESH_MS)
    return () => clearInterval(t)
  }, [load])

  // Focused-state metadata (capital + known hotspot coordinates for the map)
  useEffect(() => {
    if (!selectedId) {
      setFocusedMeta(null)
      return
    }
    let live = true
    api
      .get(`/api/states/${selectedId}`, false)
      .then((s) => {
        if (live) setFocusedMeta(s)
      })
      .catch(() => {})
    return () => {
      live = false
    }
  }, [selectedId])

  const isFocused = Boolean(selectedId)
  const focusedState = isFocused ? (data?.states || []).find((x) => x.id === selectedId) : null
  const inLocationMode = Boolean(locationPoint)
  const showAll = !isFocused && !inLocationMode

  const handleMapPick = (p) => {
    setSelectedId('')
    setFocusedMeta(null)
    setLocationPoint({ lat: Number(p.lat.toFixed(5)), lon: Number(p.lon.toFixed(5)) })
  }

  const counts = data?.summary?.counts || { LOW: 0, MODERATE: 0, HIGH: 0, CRITICAL: 0 }

  const allMarkers = (data?.states || []).map((s) => ({
    key: s.id,
    lat: s.lat,
    lon: s.lon,
    label: `${s.name} — ${s.risk?.level} (${s.risk?.score})`,
    color: levelStyle(s.risk?.level).color,
    radius: s.risk?.level === 'CRITICAL' ? 14 : 10,
  }))

  const focusedMarkers = (focusedMeta || focusedState)
    ? [
        {
          key: 'cap',
          lat: focusedMeta?.lat ?? focusedState?.lat,
          lon: focusedMeta?.lon ?? focusedState?.lon,
          label: `${focusedState?.name || focusedMeta?.name || 'Capital'} — capital${
            focusedState ? ` — ${focusedState.risk?.level} (${focusedState.risk?.score}/100)` : ''
          }`,
          color: focusedState ? levelStyle(focusedState.risk?.level).color : '#0ea5e9',
          radius: 13,
        },
        ...(focusedMeta?.known_hotspots || []).map((h) => ({
          key: h.name,
          lat: h.lat,
          lon: h.lon,
          label: `${h.name} — known landslide zone (severity ${h.severity}/100)`,
          color: '#f97316',
          radius: 8,
        })),
      ]
    : []

  const locationMarkers = inLocationMode
    ? [{
        key: 'pin',
        lat: locationPoint.lat,
        lon: locationPoint.lon,
        label: `📍 Pinned: ${locationPoint.lat.toFixed(4)}, ${locationPoint.lon.toFixed(4)}`,
        color: '#0ea5e9',
        radius: 12,
      }]
    : []

  const mapCenter = inLocationMode
    ? { lat: locationPoint.lat, lon: locationPoint.lon, zoom: 9 }
    : isFocused
      ? {
          lat: focusedMeta?.lat ?? focusedState?.lat ?? 26.2,
          lon: focusedMeta?.lon ?? focusedState?.lon ?? 92.2,
          zoom: 8,
        }
      : { lat: 26.2, lon: 92.2, zoom: 6 }

  return (
    <div className="page container">
      <h1>NER Landslide AI — Live Dashboard</h1>
      <p className="subtitle">
        Landslide risk monitoring for the 8 North Eastern states · auto-refreshes every 5 minutes
      </p>

      <AlertBanner alerts={alerts} />

      <div className="card" style={{ marginBottom: 16 }}>
        <h2>🔍 Select a State</h2>
        <div className="field" style={{ maxWidth: 460 }}>
          <label htmlFor="state-picker">State choose karo — uska detail turant yahin dikhega</label>
          <select
            id="state-picker"
            value={selectedId}
            onChange={(e) => {
              setLocationPoint(null)
              setSelectedId(e.target.value)
            }}
          >
            <option value="">🗺️ All States — poore 8 NER states ka overview</option>
            {(stateNames.length ? stateNames : data?.states || []).map((s) => {
              const dash = data?.states?.find((x) => x.id === s.id)
              const emoji = dash ? levelStyle(dash.risk?.level).emoji : '📍'
              const suffix = dash ? ` — ${dash.risk?.level} (${dash.risk?.score}/100)` : ''
              return (
                <option key={s.id} value={s.id}>
                  {emoji} {s.name}{suffix}
                </option>
              )
            })}
          </select>
        </div>
        <p className="muted" style={{ marginTop: 8 }}>
          {inLocationMode
            ? `📍 Pinned location mode — pura page isi point (${locationPoint.lat.toFixed(4)}, ${locationPoint.lon.toFixed(4)}) ke baare me hai. Map par kahin bhi click karke point badal sakte ho.`
            : selectedId
              ? `✅ Ab pura page ${focusedState?.name || focusedMeta?.name || 'isi state'} ke baare me hai — map, details sab isi state ke.`
              : 'Koi state select karo YA seedha map par kahin bhi click karo (poora India) — pura page wahan ka ho jayega.'}
        </p>
        {(inLocationMode || isFocused) && (
          <button
            className="btn btn-outline btn-sm"
            style={{ marginTop: 8 }}
            onClick={() => {
              setLocationPoint(null)
              setSelectedId('')
              setFocusedMeta(null)
            }}
          >
            ✖ Exit focused view — wapas All States
          </button>
        )}
      </div>

      {selectedId && (
        <div style={{ marginBottom: 16 }}>
          <StateDetailCard key={selectedId} stateId={selectedId} />
        </div>
      )}

      {error && (
        <div className="form-error" style={{ marginBottom: 16 }}>
          {error} — is the backend running? Start it with{' '}
          <code>python -m uvicorn main:app --port 8000</code> from the backend/ folder.
        </div>
      )}
      {loading && <Loader label={isFocused ? `Loading ${selectedId} details…` : 'Fetching live weather + risk for 8 states…'} />}

      {inLocationMode && (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <h2>🗺️ Pinned location map — {locationPoint.lat.toFixed(4)}, {locationPoint.lon.toFixed(4)}</h2>
            <MapView markers={locationMarkers} center={mapCenter} height={420} onPick={handleMapPick} />
            <p className="muted map-hint">
              🔵 Tumhara pin · India me kahin bhi click karke point badal sakte ho.
            </p>
          </div>
          <LocationDetailCard lat={locationPoint.lat} lon={locationPoint.lon} />
          <div style={{ height: 16 }} />
        </>
      )}

      {isFocused && (focusedState || focusedMeta) && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h2>🗺️ {focusedState?.name || focusedMeta?.name} — sirf isi state ka map</h2>
          <MapView markers={focusedMarkers} center={mapCenter} height={420} onPick={handleMapPick} />
          <p className="muted map-hint">
            🔵 Capital · 🟠 Known landslide hotspots
            {focusedState ? ` · Risk: ${focusedState.risk?.level} (${focusedState.risk?.score}/100)` : ''}.
            Wapas poora region dekhne ke liye upar <strong>"All States"</strong> select karo.
          </p>
        </div>
      )}

      {data && showAll && (
        <>
          <div className="grid grid-stats" style={{ marginBottom: 16 }}>
            <div className="card stat-card">
              <div className="stat-value">{data.summary.states_monitored}</div>
              <div className="stat-label">States monitored</div>
            </div>
            <div className="card stat-card" style={{ color: '#15803d' }}>
              <div className="stat-value">{counts.LOW}</div>
              <div className="stat-label">🟢 Low risk</div>
            </div>
            <div className="card stat-card" style={{ color: '#a16207' }}>
              <div className="stat-value">{counts.MODERATE}</div>
              <div className="stat-label">🟡 Moderate</div>
            </div>
            <div className="card stat-card" style={{ color: '#c2410c' }}>
              <div className="stat-value">{counts.HIGH}</div>
              <div className="stat-label">🟠 High</div>
            </div>
            <div className="card stat-card" style={{ color: '#b91c1c' }}>
              <div className="stat-value">{counts.CRITICAL}</div>
              <div className="stat-label">🔴 Critical</div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <h2>🗺️ All States map — kahin bhi click karo, wahan ka analysis</h2>
            <MapView markers={allMarkers} center={mapCenter} height={420} zoom={6} onPick={handleMapPick} />
            <p className="muted map-hint">
              🟢 LOW · 🟡 MODERATE · 🟠 HIGH · 🔴 CRITICAL. Click a state to open its detail page,
              or use <Link to="/analyze">Analyze Location</Link> to click anywhere on the map.
            </p>
          </div>

          <div className="grid grid-states">
            {data.states.map((s) => <StateCard key={s.id} s={s} />)}
          </div>

          <p className="muted" style={{ marginTop: 14 }}>
            Last updated: {new Date(data.generated_at).toLocaleString()} ·
            Weather source: {data.summary.weather_source}
          </p>
        </>
      )}
    </div>
  )
}
