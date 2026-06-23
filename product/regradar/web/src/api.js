export async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  const response = await fetch(path, {
    credentials: 'include',
    ...options,
    headers,
  })

  if (response.status === 401 && typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('auth:expired'))
  }

  return response
}

async function authRequest(path, options = {}) {
  const response = await apiFetch(path, options)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.message || data.error || `HTTP ${response.status}`)
  }
  return data
}

export const auth = {
  register(body) {
    return authRequest('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  login(body) {
    return authRequest('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  logout() {
    return authRequest('/api/auth/logout', { method: 'POST' })
  },

  me() {
    return authRequest('/api/auth/me')
  },

  googleStatus() {
    return authRequest('/api/auth/google/status')
  },

  googleStartUrl(next = '/app') {
    return `/api/auth/google/start?next=${encodeURIComponent(next)}`
  },
}

export const profile = {
  get() {
    return authRequest('/api/profile')
  },

  update(body) {
    return authRequest('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(body),
    })
  },
}

export const telegramPair = {
  generate() {
    return authRequest('/api/telegram/pair/generate', { method: 'POST' })
  },

  status() {
    return authRequest('/api/telegram/pair/status')
  },

  unlink() {
    return authRequest('/api/telegram/pair/unlink', { method: 'POST' })
  },

  test() {
    return authRequest('/api/telegram/test', { method: 'POST' })
  },
}

export const sources = {
  summary(market = 'AE') {
    return authRequest(`/api/sources/summary?market=${encodeURIComponent(market)}`)
  },

  status(market = 'AE') {
    return authRequest(`/api/sources/status?market=${encodeURIComponent(market)}`)
  },

  timeline(sourceId, limit = 100) {
    return authRequest(`/api/sources/timeline?source_id=${encodeURIComponent(sourceId)}&limit=${encodeURIComponent(limit)}`)
  },
}

export const evidence = {
  list(market = 'AE', limit = 50) {
    return authRequest(`/api/evidence?market=${encodeURIComponent(market)}&limit=${encodeURIComponent(limit)}`)
  },

  fetchDiff(runId) {
    return authRequest(`/api/evidence/diff?run_id=${encodeURIComponent(runId)}`)
  },

  review(evidenceRecordId) {
    return authRequest(`/api/evidence/review?evidence_record_id=${encodeURIComponent(evidenceRecordId)}`)
  },

  reviewHistory(evidenceRecordId) {
    return authRequest(`/api/evidence/review-history?evidence_record_id=${encodeURIComponent(evidenceRecordId)}`)
  },

  assess(body) {
    return authRequest('/api/evidence/assess', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  exportAuditPack(evidenceRecordId, format = 'md_html') {
    return authRequest('/api/evidence/export', {
      method: 'POST',
      body: JSON.stringify({ evidence_record_id: evidenceRecordId, format }),
    })
  },
}

export const reviews = {
  queue(params = {}) {
    const search = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        search.set(key, value)
      }
    })
    return authRequest(`/api/reviews/queue?${search.toString()}`)
  },

  canonicalEvidence() {
    return authRequest('/api/canonical-evidence')
  },

  reviewCanonicalEvidence(body) {
    return authRequest('/api/canonical-evidence/review', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
}

export const briefs = {
  list(market = 'AE', limit = 50) {
    return authRequest(`/api/briefs?market=${encodeURIComponent(market)}&limit=${encodeURIComponent(limit)}`)
  },
  generate(sourceId, runId) {
    const body = { source_id: sourceId }
    if (runId) body.run_id = runId
    return authRequest('/api/briefs/generate', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
}

export const delivery = {
  testBrief() {
    return authRequest('/api/delivery/test-brief', { method: 'POST' })
  },

  emailStatus() {
    return authRequest('/api/delivery/email-status')
  },

  emailTestMode(recipientEmail) {
    return authRequest('/api/delivery/email-test-mode', {
      method: 'POST',
      body: JSON.stringify({ recipient_email: recipientEmail }),
    })
  },

  emailConfigCheck() {
    return authRequest('/api/delivery/email-config-check', { method: 'POST' })
  },

  logs(limit = 20) {
    return authRequest(`/api/delivery/logs?limit=${limit}`)
  },

  preview(days = 14) {
    return authRequest(`/api/delivery/preview?days=${days}`)
  },

  sendPreviewAlert(alertId) {
    return authRequest('/api/delivery/send-preview-alert', {
      method: 'POST',
      body: JSON.stringify({ alert_id: alertId }),
    })
  },
}

export const plan = {
  get() {
    return authRequest('/api/plan')
  },

  set(planName) {
    return authRequest('/api/plan', {
      method: 'POST',
      body: JSON.stringify({ plan_name: planName }),
    })
  },
}

export const actionLog = {
  list(alertId) {
    return authRequest(`/api/alerts/action-log?alert_id=${encodeURIComponent(alertId)}`)
  },

  create(body) {
    return authRequest('/api/alerts/action-log', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
}
