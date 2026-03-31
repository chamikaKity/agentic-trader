const BASE = 'http://localhost:8000'

export const analyze = (symbol, interval) =>
  fetch(`${BASE}/api/analyze/${symbol}?interval=${interval}`).then(r => r.json())

export const candles = (symbol, interval) =>
  fetch(`${BASE}/api/candles/${symbol}?interval=${interval}`).then(r => r.json())

export const indicators = (symbol, interval) =>
  fetch(`${BASE}/api/indicators/${symbol}?interval=${interval}`).then(r => r.json())
