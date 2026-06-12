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
  status(market = 'AE') {
    return authRequest(`/api/sources/status?market=${encodeURIComponent(market)}`)
  },
}

export const delivery = {
  testBrief() {
    return authRequest('/api/delivery/test-brief', { method: 'POST' })
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
