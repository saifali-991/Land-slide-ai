import { useCallback, useEffect, useState } from 'react'
import Loader from '../components/Loader.jsx'
import { api } from '../services/api.js'
import { levelStyle } from '../services/risk.js'

export default function AlertsPage() {
  const [prefs, setPrefs] = useState({ in_app: true, email: false, email_address: '', sms: false, min_level: 'HIGH' })
  const [notifications, setNotifications] = useState(null)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    api.get('/api/alerts/preferences').then(setPrefs).catch((e) => setError(e.message))
    api.get('/api/alerts/notifications').then(setNotifications).catch((e) => setError(e.message))
  }, [])

  useEffect(load, [load])

  const savePrefs = async (e) => {
    e.preventDefault()
    setMessage(null)
    setError(null)
    try {
      const d = await api.post('/api/alerts/subscribe', {
        in_app: prefs.in_app,
        email: prefs.email,
        email_address: prefs.email || null,
        sms: prefs.sms,
        min_level: prefs.min_level,
      })
      setMessage(d.message)
    } catch (err) {
      setError(err.message)
    }
  }

  const markAllRead = async () => {
    try {
      await api.post('/api/alerts/notifications/read', {})
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page container">
      <h1>Alerts &amp; Notifications</h1>
      <p className="subtitle">Configure when you want to be warned, and read your in-app notifications.</p>
      {error && <div className="form-error" style={{ marginBottom: 12 }}>{error}</div>}
      {message && <div className="form-success" style={{ marginBottom: 12 }}>{message}</div>}

      <div className="grid grid-2">
        <div className="card">
          <h2>🔔 Notification preferences</h2>
          <form className="form" onSubmit={savePrefs}>
            <label className="checkbox-row">
              <input
                type="checkbox" checked={prefs.in_app}
                onChange={(e) => setPrefs({ ...prefs, in_app: e.target.checked })}
              />
              In-app notifications
            </label>
            <label className="checkbox-row">
              <input
                type="checkbox" checked={prefs.email}
                onChange={(e) => setPrefs({ ...prefs, email: e.target.checked })}
              />
              Email notifications
            </label>
            {prefs.email && (
              <div className="field">
                <label htmlFor="email">Email address</label>
                <input
                  id="email" type="email" placeholder="you@example.com"
                  value={prefs.email_address || ''}
                  onChange={(e) => setPrefs({ ...prefs, email_address: e.target.value })}
                />
              </div>
            )}
            <label className="checkbox-row">
              <input
                type="checkbox" checked={prefs.sms}
                onChange={(e) => setPrefs({ ...prefs, sms: e.target.checked })}
              />
              SMS / push (needs a provider — logged stub in prototype)
            </label>
            <div className="field">
              <label htmlFor="minlevel">Notify me when risk reaches</label>
              <select
                id="minlevel" value={prefs.min_level}
                onChange={(e) => setPrefs({ ...prefs, min_level: e.target.value })}
              >
                <option value="MODERATE">🟡 MODERATE or above</option>
                <option value="HIGH">🟠 HIGH or above (recommended)</option>
                <option value="CRITICAL">🔴 CRITICAL only</option>
              </select>
            </div>
            <button className="btn btn-primary" type="submit">Save preferences</button>
            <p className="muted">
              Email/SMS are stubs in this prototype: alerts are stored in-app and external
              sends are logged on the server. Plug SMTP/Twilio/FCM into
              <code> alert_service._send_external()</code> to enable them.
            </p>
          </form>
        </div>

        <div className="card">
          <h2>📥 My notifications {notifications ? `(${notifications.unread} unread)` : ''}</h2>
          {!notifications && <Loader />}
          {notifications && notifications.notifications.length === 0 && (
            <p className="muted">
              No notifications yet. Save locations in “My Locations” and refresh their risk to
              receive alerts when conditions worsen.
            </p>
          )}
          {notifications && notifications.notifications.length > 0 && (
            <>
              <button className="btn btn-outline btn-sm" style={{ marginBottom: 10 }} onClick={markAllRead}>
                Mark all as read
              </button>
              <div>
                {notifications.notifications.map((n) => (
                  <div
                    key={n.id}
                    className="alert-banner"
                    style={{
                      borderLeftColor: levelStyle(n.risk_level).color,
                      background: levelStyle(n.risk_level).bg,
                      opacity: n.is_read ? 0.65 : 1,
                    }}
                  >
                    <h4 style={{ color: levelStyle(n.risk_level).color }}>
                      {n.is_read ? '' : '🆕 '}{n.title}
                    </h4>
                    <pre>{n.message}</pre>
                    <span className="muted">{new Date(n.created_at).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
