const BASE = '/api'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json()
}

export const api = {
  recentNews: (page = 1, pageSize = 25) =>
    get(`/news/recent?page=${page}&page_size=${pageSize}`),
  entities: () => get('/entities'),
  entityTrend: (id, hours = 168) => get(`/entities/${id}/trend?hours=${hours}`),
  recentDecisions: (limit = 50) => get(`/decisions/recent?limit=${limit}`),
  decisionTrace: (id) => get(`/decisions/${id}`),
  winrate: () => get('/analytics/winrate'),
  spikes: () => get('/analytics/spikes'),
  runAgent: (newsId = null) =>
    fetch(`${BASE}/agent/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ news_id: newsId }),
    }).then((r) => r.json()),
}
