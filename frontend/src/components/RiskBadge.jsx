import { levelStyle } from '../services/risk.js'

export default function RiskBadge({ level, score, large = false }) {
  const s = levelStyle(level)
  return (
    <span
      className={`badge ${large ? 'badge-lg' : ''}`}
      style={{ background: s.bg, color: s.color }}
    >
      {s.emoji} {level}
      {score != null ? ` · ${score}/100` : ''}
    </span>
  )
}
