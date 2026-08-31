export const LEVELS = {
  LOW: { color: '#22c55e', emoji: '🟢', bg: '#dcfce7' },
  MODERATE: { color: '#eab308', emoji: '🟡', bg: '#fef9c3' },
  HIGH: { color: '#f97316', emoji: '🟠', bg: '#ffedd5' },
  CRITICAL: { color: '#dc2626', emoji: '🔴', bg: '#fee2e2' },
}

// Mirrors backend defaults (NER_THRESHOLD_* env vars). Backend responses
// include the live thresholds under risk.thresholds where relevant.
export const FALLBACK_THRESHOLDS = { moderate: 25, high: 50, critical: 75 }

export function levelFor(score, thresholds = FALLBACK_THRESHOLDS) {
  if (score == null) return 'LOW'
  if (score < thresholds.moderate) return 'LOW'
  if (score < thresholds.high) return 'MODERATE'
  if (score < thresholds.critical) return 'HIGH'
  return 'CRITICAL'
}

export const levelStyle = (level) => LEVELS[level] || LEVELS.LOW
