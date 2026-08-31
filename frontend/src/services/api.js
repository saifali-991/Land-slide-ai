const BASE = import.meta.env.VITE_API_BASE_URL || ''

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('ner_token')
  if (token && auth) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = typeof data.detail === 'string'
      ? data.detail
      : `Request failed (${res.status})`
    const err = new Error(detail)
    err.status = res.status
    throw err
  }
  return data
}

export const api = {
  get: (path, auth = true) => request(path, { auth }),
  post: (path, body, auth = true) => request(path, { method: 'POST', body, auth }),
  patch: (path, body, auth = true) => request(path, { method: 'PATCH', body, auth }),
  del: (path, auth = true) => request(path, { method: 'DELETE', auth }),
}
