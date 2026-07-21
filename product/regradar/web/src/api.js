// API base URL. Empty (default) = same-origin — correct for dev (Vite proxy)
// and for production behind the reverse proxy. Set VITE_API_URL only for
// split-origin deployments; it must never point at localhost in a prod build
// (deploy-check enforces this).
const API_BASE = (import.meta.env?.VITE_API_URL || '').replace(/\/$/, '')

export async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  const response = await fetch(API_BASE + path, {
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
    const err = new Error(data.message || data.error || `HTTP ${response.status}`)
    if (data.requires_verification) {
      err.requiresVerification = true
      err.email = data.email || ''
    }
    throw err
  }
  return data
}

// Public, no-login evidence verifier. Posts a caller-held record (+ optional
// raw/normalized text) to /api/verify and returns the check envelope. No auth,
// no session required — the whole point is verifying without trusting us.
export async function verifyRecord({ record, raw, normalized, diff, timestampToken, timestampDigest }) {
  const body = { record }
  if (typeof raw === 'string' && raw.length) body.raw = raw
  if (typeof normalized === 'string' && normalized.length) body.normalized = normalized
  // diff.txt is the sealed redline; the server checks sha256(diff) against the
  // record's diff_hash (diff_bytes_match). Additive — legacy records skip it.
  if (typeof diff === 'string' && diff.length) body.diff = diff
  if (typeof timestampToken === 'string' && timestampToken.length) {
    body.timestamp_token = timestampToken
  }
  // Chain-head tokens attest the anchored head hash, not a record's own
  // record_hash — the caller supplies that digest (from the .tsr.json
  // sidecar) or the server defaults to the record's record_hash.
  if (typeof timestampDigest === 'string' && timestampDigest.trim().length) {
    body.timestamp_digest = timestampDigest.trim()
  }

  const response = await apiFetch('/api/verify', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.error || data.message || `HTTP ${response.status}`)
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

  resendVerification(email) {
    return authRequest('/api/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  },

  forgotPassword(email) {
    return authRequest('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  },

  resetPassword(token, password) {
    return authRequest('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    })
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

// Self-service account data export (exit portability). GET streams everything
// the signed-in user owns — account profile, workspace profile, notification
// preferences, checklist items, the org's sealed decision records + chain head,
// and the Telegram link — as one application/json attachment. Mirrors
// reports.regulatorBinder's blob shape: returns { blob, filename } so the
// caller triggers the browser download; throws with `status` on error.
export const account = {
  async exportData() {
    const response = await apiFetch('/api/account/export')
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const err = new Error(data.message || `HTTP ${response.status}`)
      err.status = response.status
      throw err
    }
    const blob = await response.blob()
    const filename = parseFilename(response.headers.get('Content-Disposition'))
      || 'statuteproof-account-export.json'
    return { blob, filename }
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

function parseFilename(disposition) {
  if (!disposition) return ''
  const match = /filename="?([^"]+)"?/.exec(disposition)
  return match ? match[1] : ''
}

export const reports = {
  // Regulator-ready evidence binder: POSTs the source + period, receives a sealed
  // application/zip on success (streamed as a blob for download) or a JSON error
  // envelope otherwise. Returns { blob, filename } so the caller can trigger the
  // browser download; throws on error with an `empty` flag for the 404 case.
  async regulatorBinder({ sourceIds, dateFrom, dateTo }) {
    const response = await apiFetch('/api/reports/regulator-binder', {
      method: 'POST',
      body: JSON.stringify({ source_ids: sourceIds, date_from: dateFrom, date_to: dateTo }),
    })
    const contentType = response.headers.get('Content-Type') || ''
    if (!response.ok || !contentType.includes('application/zip')) {
      const data = await response.json().catch(() => ({}))
      const err = new Error(data.message || `HTTP ${response.status}`)
      err.status = response.status
      err.empty = response.status === 404 || data.status === 'empty'
      throw err
    }
    const blob = await response.blob()
    const filename = parseFilename(response.headers.get('Content-Disposition')) || 'regulator-binder.zip'
    return { blob, filename }
  },

  // Negative-assurance coverage certificate. GET with an optional period
  // (period_start/period_end ISO dates; defaults to the current month server-side)
  // and optional source scope. format 'json' returns the structured certificate
  // for in-dashboard rendering; 'markdown'/'html' return a `report` string for
  // download. Returns the parsed { status, certificate, report? } envelope.
  coverageCertificate({ periodStart, periodEnd, sourceIds, clientName, format = 'json' } = {}) {
    const q = new URLSearchParams()
    if (periodStart) q.set('period_start', periodStart)
    if (periodEnd) q.set('period_end', periodEnd)
    if (sourceIds && sourceIds.length) q.set('source_ids', sourceIds.join(','))
    if (clientName) q.set('client_name', clientName)
    q.set('format', format)
    return authRequest(`/api/reports/coverage-certificate?${q.toString()}`)
  },

  // Self-serve, self-verifiable Evidence Pack: POSTs source + period, receives a
  // sealed application/zip (manifest + standalone verify.py + snapshots) streamed
  // as a blob. Mirrors regulatorBinder — returns { blob, filename }; throws on
  // error with an `empty` flag for the 404 case.
  async evidencePack({ sourceIds, dateFrom, dateTo }) {
    const response = await apiFetch('/api/evidence/pack', {
      method: 'POST',
      body: JSON.stringify({ source_ids: sourceIds, date_from: dateFrom, date_to: dateTo }),
    })
    const contentType = response.headers.get('Content-Type') || ''
    if (!response.ok || !contentType.includes('application/zip')) {
      const data = await response.json().catch(() => ({}))
      const err = new Error(data.message || `HTTP ${response.status}`)
      err.status = response.status
      err.empty = response.status === 404 || data.status === 'empty'
      throw err
    }
    const blob = await response.blob()
    const filename = parseFilename(response.headers.get('Content-Disposition')) || 'evidence-pack.zip'
    return { blob, filename }
  },
}

export const evidenceRoom = {
  // Owner-side management (authenticated). The create response contains the
  // share token EXACTLY ONCE — the server stores only its hash and can never
  // show the link again.
  createShare({ sourceIds, dateFrom, dateTo, expiresDays, orgDisplayName }) {
    return authRequest('/api/evidence-room/shares', {
      method: 'POST',
      body: JSON.stringify({
        source_ids: sourceIds,
        date_from: dateFrom,
        date_to: dateTo,
        expires_days: expiresDays,
        org_display_name: orgDisplayName || '',
      }),
    })
  },

  listShares() {
    return authRequest('/api/evidence-room/shares')
  },

  revokeShare(shareId) {
    return authRequest('/api/evidence-room/shares/revoke', {
      method: 'POST',
      body: JSON.stringify({ share_id: shareId }),
    })
  },

  // Public examiner view — no session required; the token IS the credential.
  // Expired, revoked, and unknown links all return the same 404 envelope.
  async view(token) {
    const response = await apiFetch(`/api/room/${encodeURIComponent(token)}`)
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      const err = new Error(data.message || data.error || `HTTP ${response.status}`)
      err.status = response.status
      throw err
    }
    return data
  },
}

export const calendar = {
  // Forward-looking view of key dates StatuteProof DETECTED in the changed text
  // of monitored sources (effective dates / deadlines / consultation closes),
  // each linked to its sealed evidence record. Read-only, own-scope. Returns the
  // { ok, dates, horizon, framing, disclaimer } envelope. `days` defaults to 90.
  effectiveDates({ days = 90, from, to, sourceIds } = {}) {
    const q = new URLSearchParams()
    if (days) q.set('days', String(days))
    if (from) q.set('from', from)
    if (to) q.set('to', to)
    if (sourceIds && sourceIds.length) q.set('source_ids', sourceIds.join(','))
    return authRequest(`/api/calendar/effective-dates?${q.toString()}`)
  },
}

export const health = {
  // System health for the existing public /api/health endpoint (same one the
  // topbar polls). Best-effort: returns the parsed payload
  // ({ ok, db, sources_active, last_run_at, ... }) and never throws for a
  // non-2xx response — a "degraded" health signal is itself meaningful. A
  // genuine network failure rejects, so callers can distinguish unreachable.
  async get() {
    const response = await apiFetch('/api/health')
    const data = await response.json().catch(() => ({}))
    return { ...data, http_ok: response.ok }
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

// Founder admin panel. Both calls are gated server-side (identity + the
// owner-only plan.admin RBAC action); the client gate is only a UI hint. A
// non-founder call is answered 403 and rejects here.
export const admin = {
  listAccounts() {
    return authRequest('/api/admin/accounts')
  },

  activatePlan({ userId, email, planName }) {
    const body = { plan_name: planName }
    if (userId != null && userId !== '') body.user_id = userId
    else if (email) body.email = email
    return authRequest('/api/admin/activate-plan', {
      method: 'POST',
      body: JSON.stringify(body),
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

// Per-alert review checklist (obligation-workflow v1). The user's OWN review
// action items for an alert — list, add, tick/edit, and delete. Owner-scoped by
// the session on the server; the item text is the user's own words. The GET
// response carries a server-authored `framing` block (guard-clean copy).
export const checklist = {
  list(alertId) {
    return authRequest(`/api/alerts/checklist?alert_id=${encodeURIComponent(alertId)}`)
  },

  add({ alertId, text, assignee = '', dueDate = '' }) {
    return authRequest('/api/alerts/checklist', {
      method: 'POST',
      body: JSON.stringify({ alert_id: alertId, text, assignee, due_date: dueDate }),
    })
  },

  update(body) {
    return authRequest('/api/alerts/checklist/update', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  toggle(itemId, status) {
    return this.update({ item_id: itemId, status })
  },

  remove(itemId) {
    return this.update({ item_id: itemId, delete: true })
  },
}

// Sealed-evidence redline: the added/removed text of one alert's SEALED diff
// artifact, parsed server-side into structured blocks. Read-only; owner-scoped
// on the server via the same routing preview the alerts page is built from.
export const redline = {
  get(alertId) {
    return authRequest(`/api/alerts/redline?alert_id=${encodeURIComponent(alertId)}`)
  },
}

// Sealed decision log: the reviewer's OWN sign-off for one alert, sealed in
// their own words into the org's append-only hash chain. GET is readable by
// every org role (incl. auditor); POST requires review.submit — the panel
// needs the HTTP status to tell a role denial (403 → read-only) from a
// validation error, so seal() attaches it to the thrown error.
export const decisions = {
  list(alertId) {
    return authRequest(`/api/alerts/decisions?alert_id=${encodeURIComponent(alertId)}`)
  },

  async seal(body) {
    const response = await apiFetch('/api/alerts/decisions', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      const err = new Error(data.message || data.error || `HTTP ${response.status}`)
      err.status = response.status
      throw err
    }
    return data
  },
}
