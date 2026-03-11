const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

let _authToken = null

export function setAuthToken(token) {
  _authToken = token
}

export function getAuthToken() {
  return _authToken
}

async function request(path, options = {}) {
  const headers = { ...options.headers }
  if (_authToken) headers['Authorization'] = `Bearer ${_authToken}`
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch (_) {}
    throw new Error(detail)
  }
  return res.json()
}

export async function getProviders() {
  return request('/api/providers')
}

export async function createSession(provider) {
  return request('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  })
}

export async function uploadDocs(sessionId, files) {
  const formData = new FormData()
  files.forEach((f) => formData.append('files', f))
  return request(`/api/sessions/${sessionId}/docs`, { method: 'POST', body: formData })
}

export async function uploadQuestionnaire(sessionId, file, text) {
  const formData = new FormData()
  if (file) formData.append('file', file)
  if (text) formData.append('text', text)
  return request(`/api/sessions/${sessionId}/questionnaire`, { method: 'POST', body: formData })
}

export async function processQuestionnaire(sessionId) {
  return request(`/api/sessions/${sessionId}/process`, { method: 'POST' })
}

export async function getStatus(sessionId) {
  return request(`/api/sessions/${sessionId}/status`)
}

export async function getAnswers(sessionId) {
  return request(`/api/sessions/${sessionId}/answers`)
}

export async function updateAnswer(sessionId, questionId, update) {
  return request(`/api/sessions/${sessionId}/answers/${questionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
}

export function getExcelUrl(sessionId) {
  return `${BASE}/api/sessions/${sessionId}/export/excel`
}

export function getPdfUrl(sessionId) {
  return `${BASE}/api/sessions/${sessionId}/export/pdf`
}
