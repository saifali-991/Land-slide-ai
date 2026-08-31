function barColor(score) {
  if (score >= 70) return '#dc2626'
  if (score >= 45) return '#f97316'
  if (score >= 25) return '#eab308'
  return '#22c55e'
}

/**
 * factors: [{ factor, label, score, detail, weight, contribution }]
 * sorted by contribution desc (backend already sorts).
 */
export default function FactorBreakdown({ factors }) {
  if (!factors?.length) return null
  return (
    <div>
      {factors.map((f) => (
        <div className="factor" key={f.factor}>
          <div className="factor-top">
            <strong>{f.label}</strong>
            <span className="pts">
              {f.score}/100 · weight {f.weight}% · +{f.contribution} pts
            </span>
          </div>
          <div className="bar">
            <div style={{ width: `${Math.max(0, Math.min(100, f.score))}%`, background: barColor(f.score) }} />
          </div>
          <div className="factor-detail">{f.detail}</div>
        </div>
      ))}
    </div>
  )
}
