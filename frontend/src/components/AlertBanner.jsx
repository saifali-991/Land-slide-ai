import { useState } from 'react'
import { levelStyle } from '../services/risk.js'

/** Displays recent HIGH/CRITICAL broadcast alerts (dismissible). */
export default function AlertBanner({ alerts = [] }) {
  const [dismissed, setDismissed] = useState(() => new Set())
  const visible = alerts.filter((a) => !dismissed.has(a.id)).slice(0, 3)
  if (!visible.length) return null

  const dismiss = (id) => setDismissed((d) => new Set(d).add(id))

  return (
    <div>
      {visible.map((a) => {
        const s = levelStyle(a.risk_level)
        return (
          <div key={a.id} className="alert-banner" style={{ borderLeftColor: s.color, background: s.bg }}>
            <h4 style={{ color: s.color }}>{a.title}</h4>
            <pre>{a.message}</pre>
            <button className="btn btn-outline btn-sm" onClick={() => dismiss(a.id)}>Dismiss</button>
          </div>
        )
      })}
    </div>
  )
}
