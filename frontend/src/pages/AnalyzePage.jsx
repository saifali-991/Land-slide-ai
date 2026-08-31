import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import FactorBreakdown from '../components/FactorBreakdown.jsx'
import Loader from '../components/Loader.jsx'
import MapView from '../components/MapView.jsx'
import RiskGauge from '../components/RiskGauge.jsx'
import WeatherPanel from '../components/WeatherPanel.jsx'
import { api } from '../services/api.js'
import { useAuth } from '../services/auth.jsx'
import { levelStyle } from '../services/risk.js'

export default function AnalyzePage() {
  const [params] = useSearchParams()
  const { user } = useAuth()
  const [picked, setPicked] = useState(() => {
    const lat = parseFloat(params.get('lat'))
    const lon = parseFloat(params.get('lon'))
    return Number.isFinite(lat) && Number.isFinite(lon) ? { lat, lon } : null
  })
  const [name, setName] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [saveMsg, setSaveMsg] = useState(null)
  const [predictNote, setPredictNote] = useState(null)

  const analyze = async (pt = picked) => {
    if (!pt) return
    setBusy(true)
    setError(null)
    setSaveMsg(null)
    setPredictNote(null)
    try {
      const a = await api.post(
        '/api/risk/analyze',
        { lat: pt.lat, lon: pt.lon, name: name || null },
        false,
      )
      setResult(a)
      // Optional ML comparison (non-blocking; works once the model is trained)
      api
        .post('/api/risk/predict', { lat: pt.lat, lon: pt.lon }, false)
        .then((p) => {
          if (p?.ml) {
            setPredictNote(
              `🤖 ML model (${p.ml.model_type}) says ${p.ml.risk_score}/100 → ${p.ml.risk_level} · ` +
              `ROC-AUC ${p.ml.metrics?.roc_auc ?? '—'} (trained on prototype data)`,
            )
          }
        })
        .catch(() => {})
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const saveLocation = async () => {
    if (!result) return
    try {
      const d = await api.post('/api/locations', {
        name: name || result.location.name,
        lat: result.location.lat,
        lon: result.location.lon,
        state: result.location.state,
      })
      setSaveMsg(`✅ Saved to My Locations (id ${d.id}).`)
    } catch (e) {
      setSaveMsg(e.status === 401 ? 'Please log in to save locations.' : e.message)
    }
  }

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by this browser.')
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setPicked({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => setError('Could not get your location (permission denied).'),
    )
  }

  useEffect(() => {
    document.title = 'Analyze Location — NER Landslide AI'
  }, [])

  const markers = picked
    ? [{
        key: 'p',
        lat: picked.lat,
        lon: picked.lon,
        label: `${picked.lat.toFixed(4)}, ${picked.lon.toFixed(4)}`,
        color: result ? levelStyle(result.risk.level).color : '#0ea5e9',
        radius: 11,
      }]
    : []

  return (
    <div className="page container">
      <h1>Analyze a Location</h1>
      <p className="subtitle">
        Click anywhere on the map (or use your device location) and press Analyze — the backend
        pulls live weather, terrain and susceptibility data for that exact point.
      </p>

      <div className="grid grid-2">
        <div className="card">
          <h2>1️⃣ Pick a location</h2>
          <MapView
            markers={markers}
            center={picked || undefined}
            zoom={7}
            height={360}
            onPick={(p) => {
              setPicked({ lat: p.lat, lon: p.lon })
              setError(null)
            }}
          />
          <p
            className="muted map-hint"
            style={picked ? undefined : { color: '#b45309', fontWeight: 600 }}
          >
            {picked
              ? `✅ Selected: ${picked.lat.toFixed(5)}, ${picked.lon.toFixed(5)} — ab Analyze dabao`
              : '⚠️ Pehle upar map par click karo — location select karne ke baad hi Analyze chalega.'}
          </p>
          <div className="form" style={{ marginTop: 10 }}>
            <div className="field">
              <label htmlFor="loc-name">Label (optional)</label>
              <input
                id="loc-name"
                placeholder="e.g. Home, Guwahati route…"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={160}
              />
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button
                className="btn btn-primary"
                disabled={busy}
                onClick={() => {
                  if (!picked) {
                    setError(
                      'Pehle upar map par click karke location select karo (ya "Use my location" dabao) — uske baad Analyze chalega.',
                    )
                    return
                  }
                  analyze()
                }}
              >
                {busy ? 'Analyzing…' : '🔍 Analyze risk'}
              </button>
              <button className="btn btn-outline" type="button" onClick={useMyLocation}>
                📍 Use my location
              </button>
            </div>
          </div>
        </div>

        <div className="card">
          <h2>2️⃣ Result</h2>
          {error && <div className="form-error">{error}</div>}
          {busy && <Loader label="Collecting live weather + terrain data…" />}
          {!result && !busy && !error && (
            <p className="muted">Select a location and press Analyze to see the risk breakdown here.</p>
          )}
          {result && (
            <>
              <p className="muted">
                <strong>{result.location.name}</strong> · {result.location.state} ·
                Lat {result.location.lat}, Lon {result.location.lon}
              </p>
              <RiskGauge score={result.risk.score} level={result.risk.level} />
              <p>{result.explanation}</p>
              {result.trigger_notes?.length > 0 && (
                <ul className="reco-list">
                  {result.trigger_notes.map((t) => <li key={t}>⚠️ {t}</li>)}
                </ul>
              )}
              {result.warning && (
                <div
                  className="alert-banner"
                  style={{
                    borderLeftColor: levelStyle(result.risk.level).color,
                    background: levelStyle(result.risk.level).bg,
                  }}
                >
                  <h4 style={{ color: levelStyle(result.risk.level).color }}>{result.warning.title}</h4>
                  <pre>{result.warning.message}</pre>
                </div>
              )}
              <h3>Recommended actions</h3>
              <ul className="reco-list">
                {result.recommendations.map((r) => <li key={r}>{r}</li>)}
              </ul>
              <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                <button className="btn btn-primary btn-sm" onClick={saveLocation}>💾 Save this location</button>
                {!user && <span className="muted">(login to keep saved locations &amp; alerts)</span>}
              </div>
              {saveMsg && <div className="form-success" style={{ marginTop: 10 }}>{saveMsg}</div>}
              {predictNote && <p className="muted" style={{ marginTop: 10 }}>{predictNote}</p>}
            </>
          )}
        </div>
      </div>

      {result && (
        <div className="grid grid-2" style={{ marginTop: 16 }}>
          <div className="card">
            <h2>⚖️ Why this risk level? (weighted factors)</h2>
            <FactorBreakdown factors={result.factors} />
          </div>
          <div className="card">
            <h2>🌦️ Live conditions</h2>
            <WeatherPanel weather={result.weather} />
          </div>
        </div>
      )}

      <p className="disclaimer">{result?.disclaimer}</p>
    </div>
  )
}

