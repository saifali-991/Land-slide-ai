import { levelStyle } from '../services/risk.js'

export default function RiskGauge({ score, level }) {
  const s = levelStyle(level)
  const r = 54
  const c = 2 * Math.PI * r
  const filled = Math.max(0, Math.min(100, score ?? 0)) / 100
  return (
    <div className="gauge-wrap">
      <svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label={`Risk ${score} of 100`}>
        <circle cx="70" cy="70" r={r} fill="none" stroke="#eef2f7" strokeWidth="13" />
        <circle
          cx="70" cy="70" r={r} fill="none" stroke={s.color} strokeWidth="13"
          strokeLinecap="round"
          strokeDasharray={`${filled * c} ${c}`}
          transform="rotate(-90 70 70)"
        />
        <text x="70" y="66" textAnchor="middle" fontSize="30" fontWeight="800" fill="#0f172a">
          {score ?? '–'}
        </text>
        <text x="70" y="88" textAnchor="middle" fontSize="12" fill="#64748b">/ 100</text>
      </svg>
      <div>
        <div style={{ fontSize: '1.35rem', fontWeight: 800, color: s.color }}>
          {s.emoji} {level}
        </div>
        <div className="muted">Landslide Risk Score</div>
      </div>
    </div>
  )
}
