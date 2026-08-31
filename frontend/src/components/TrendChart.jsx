import { levelFor, levelStyle } from '../services/risk.js'

/** Simple dependency-free SVG trend line. points: [{score}] oldest-first. */
export default function TrendChart({ points = [] }) {
  if (points.length < 2) {
    return <p className="muted">Not enough history yet for a trend chart — it builds up as the dashboard refreshes.</p>
  }
  const w = 640
  const h = 160
  const pad = 28
  const stepX = (w - pad * 2) / (points.length - 1)
  const xy = points.map((p, i) => [
    pad + i * stepX,
    h - pad - (Math.max(0, Math.min(100, p.score)) / 100) * (h - pad * 2),
  ])
  const path = xy.map((p) => p.join(',')).join(' ')
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height: 'auto' }} className="trend-wrap">
      {[0, 25, 50, 75, 100].map((v) => {
        const y = h - pad - (v / 100) * (h - pad * 2)
        return (
          <g key={v}>
            <line x1={pad} y1={y} x2={w - pad} y2={y} stroke="#e2e8f0" strokeWidth="1" />
            <text x={4} y={y + 4} fontSize="10" fill="#94a3b8">{v}</text>
          </g>
        )
      })}
      <polyline points={path} fill="none" stroke="#0ea5e9" strokeWidth="2.5" />
      {xy.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="4" fill={levelStyle(levelFor(points[i].score)).color} />
      ))}
    </svg>
  )
}
