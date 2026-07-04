// Chart + ink tokens (validated palette — see dataviz reference).
// Light mode only: the dashboard pins a light AntD theme.
export const viz = {
  series1: '#2a78d6',   // blue  — primary series
  series2: '#1baf7a',   // aqua  — secondary series (sub-3:1: keep legend/labels)
  surface: '#fcfcfb',
  grid: '#e1e0d9',
  baseline: '#c3c2b7',
  muted: '#898781',
  inkPrimary: '#0b0b0b',
  inkSecondary: '#52514e',
  // status (icon + label always accompanies color)
  good: '#0ca30c',
  critical: '#d03b3b',
  neutral: '#898781',
  divergingMid: '#f0efec',
}

export const sentimentColor = (label) =>
  label === 'positive' ? viz.good
  : label === 'negative' ? viz.critical
  : viz.neutral

export const fmtScore = (v) => {
  const n = Number(v)
  return Number.isFinite(n) ? (n > 0 ? `+${n.toFixed(2)}` : n.toFixed(2)) : '—'
}
