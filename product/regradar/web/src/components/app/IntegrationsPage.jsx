import { useEffect, useState } from 'react'
import {
  CheckCircle,
  Copy,
  ExternalLink,
  FileText,
  Link2,
  Loader2,
  Mail,
  RefreshCw,
  Send,
  Trash2,
  Webhook,
  XCircle, Check } from 'lucide-react'

import { delivery, telegramPair } from '../../api'
import StatusBadge from './ui/StatusBadge'

function formatDate(value) {
  if (!value) return 'Not recorded'
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function StatusNotice({ type, children }) {
  const classes = {
    success: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
    error: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
    info: 'bg-[var(--trust-badge)] text-[var(--accent)] border-[var(--trust-border)]',
  }
  return (
    <div className={`flex items-center gap-2 text-xs rounded-lg px-3 py-2.5 border ${classes[type] || classes.info}`}>
      {type === 'success' && <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />}
      {type === 'error' && <XCircle className="w-3.5 h-3.5 flex-shrink-0" />}
      {type === 'info' && <Loader2 className="w-3.5 h-3.5 animate-spin flex-shrink-0" />}
      <span>{children}</span>
    </div>
  )
}

function emailModeLabel(state) {
  if (!state) return 'Email readiness unknown'
  if (state.status === 'test_mode') return 'Local outbox / test-mode'
  if (state.status === 'ready_but_disabled') return 'Provider configured but disabled'
  if (state.status === 'production_enabled' && state.send_enabled && state.provider_configured) return 'Production sending enabled'
  if (state.status === 'configuration_required') return 'Configuration required'
  return 'Email readiness unknown'
}

export default function IntegrationsPage() {
  const [status, setStatus] = useState(null)
  const [botUsername, setBotUsername] = useState('')
  const [statusLoading, setStatusLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [testing, setTesting] = useState(false)
  const [unlinking, setUnlinking] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [briefStatus, setBriefStatus] = useState('idle')
  const [briefMsg, setBriefMsg] = useState('')
  const [emailRecipient, setEmailRecipient] = useState('')
  const [emailStatus, setEmailStatus] = useState('idle')
  const [emailMsg, setEmailMsg] = useState('')
  const [emailReadiness, setEmailReadiness] = useState(null)
  const [emailReadinessLoading, setEmailReadinessLoading] = useState(true)
  const [emailConfigChecking, setEmailConfigChecking] = useState(false)
  const [copied, setCopied] = useState(false)
  const [nowTick, setNowTick] = useState(() => Date.now())

  const activeCode = status?.active_code
  const pairExpiresAtMs = activeCode?.expires_at ? new Date(activeCode.expires_at).getTime() : null
  const pairExpired = Boolean(activeCode && pairExpiresAtMs && nowTick > pairExpiresAtMs)
  const command = activeCode?.code ? `/start ${activeCode.code}` : ''
  const botLink = botUsername ? `https://t.me/${botUsername}` : ''

  async function refreshStatus() {
    setStatusLoading(true)
    setError('')
    try {
      const data = await telegramPair.status()
      setStatus(data)
      // Populate bot username from status if available (e.g. after page reload with active code)
      if (data.bot_username) setBotUsername(data.bot_username)
    } catch (err) {
      setError(err.message || 'Could not load Telegram status.')
    } finally {
      setStatusLoading(false)
    }
  }

  async function refreshEmailReadiness() {
    setEmailReadinessLoading(true)
    try {
      const data = await delivery.emailStatus()
      setEmailReadiness(data)
    } catch (err) {
      setEmailReadiness({
        ok: false,
        status: 'configuration_required',
        provider: 'unknown',
        customer_safe_status: err.message || 'Could not load email readiness.',
        missing_config: [],
        send_enabled: false,
        provider_configured: false,
      })
    } finally {
      setEmailReadinessLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refreshStatus()
      refreshEmailReadiness()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  // Auto-poll pairing status after a code is generated so "Connected" appears on
  // its own — the customer never has to hunt for a Refresh button to confirm.
  useEffect(() => {
    if (status?.connected) return
    if (!activeCode?.code) return
    if (pairExpired) return
    let active = true
    const interval = window.setInterval(async () => {
      if (!active) return
      setNowTick(Date.now()) // keep the expiry countdown live
      if (pairExpiresAtMs && Date.now() > pairExpiresAtMs) {
        window.clearInterval(interval)
        return
      }
      try {
        const data = await telegramPair.status()
        if (!active) return
        if (data.bot_username) setBotUsername(data.bot_username)
        if (data.connected) {
          setStatus(data)
          setSuccessMessage('Telegram connected.')
          window.clearInterval(interval)
        }
      } catch {
        // Keep polling quietly; the manual Refresh button remains available.
      }
    }, 4000)
    return () => {
      active = false
      window.clearInterval(interval)
    }
  }, [activeCode?.code, pairExpiresAtMs, pairExpired, status?.connected])

  async function handleGenerate() {
    setGenerating(true)
    setError('')
    setSuccessMessage('')
    setCopied(false)
    setNowTick(Date.now())
    try {
      const data = await telegramPair.generate()
      setBotUsername(data.bot_username || '')
      setStatus(prev => ({
        ...(prev || {}),
        connected: false,
        active_code: {
          code: data.code,
          expires_at: data.expires_at,
        },
      }))
      setSuccessMessage(data.instructions || 'Pairing code generated.')
    } catch (err) {
      setError(err.message || 'Could not generate pairing code.')
    } finally {
      setGenerating(false)
    }
  }

  async function handleCopy() {
    if (!command) return
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(command)
        setCopied(true)
        setTimeout(() => setCopied(false), 2500)
      }
    } catch {
      setCopied(false)
    }
  }

  async function handleTest() {
    setTesting(true)
    setError('')
    setSuccessMessage('')
    try {
      const data = await telegramPair.test()
      setSuccessMessage(data.message || 'Test message sent to your Telegram.')
      await refreshStatus()
    } catch (err) {
      setError(err.message || 'Could not send Telegram test message.')
    } finally {
      setTesting(false)
    }
  }

  async function handleSampleBrief() {
    setBriefStatus('sending')
    setBriefMsg('')
    try {
      const data = await delivery.testBrief()
      setBriefStatus('ok')
      setBriefMsg(data.message || 'Sample brief sent.')
    } catch (err) {
      setBriefStatus('error')
      setBriefMsg(err.message || 'Could not send sample brief.')
    }
    setTimeout(() => {
      setBriefStatus('idle')
      setBriefMsg('')
    }, 7000)
  }

  async function handleEmailTestMode() {
    setEmailStatus('sending')
    setEmailMsg('')
    try {
      const data = await delivery.emailTestMode(emailRecipient)
      setEmailStatus('ok')
      setEmailMsg(data.message || `Email payload written to local outbox: ${data.outbox_path || 'path unavailable'}`)
      await refreshEmailReadiness()
    } catch (err) {
      setEmailStatus('error')
      setEmailMsg(err.message || 'Could not write email test-mode payload.')
    }
    setTimeout(() => {
      setEmailStatus('idle')
      setEmailMsg('')
    }, 9000)
  }

  async function handleEmailConfigCheck() {
    setEmailConfigChecking(true)
    setEmailMsg('')
    try {
      const data = await delivery.emailConfigCheck()
      setEmailReadiness(data)
      setEmailStatus(data.status === 'configuration_required' ? 'error' : 'ok')
      setEmailMsg(data.customer_safe_status || 'Email configuration checked.')
    } catch (err) {
      setEmailStatus('error')
      setEmailMsg(err.message || 'Email configuration check failed.')
      await refreshEmailReadiness()
    } finally {
      setEmailConfigChecking(false)
    }
  }

  async function handleUnlink() {
    setUnlinking(true)
    setError('')
    setSuccessMessage('')
    try {
      await telegramPair.unlink()
      await refreshStatus()
      setSuccessMessage('Telegram disconnected from your account.')
    } catch (err) {
      setError(err.message || 'Could not unlink Telegram.')
    } finally {
      setUnlinking(false)
    }
  }

  return (
    <div className="p-5 space-y-4">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-white mb-1">Integrations</h1>
        <p className="text-sm text-[var(--text-secondary)]">Connect StatuteProof to your communication and workflow tools.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-4">

        {/* Telegram */}
        <div className="lg:col-span-2 bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5">
          <div className="flex items-start justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[var(--trust-badge)] border border-[var(--trust-border)] flex items-center justify-center flex-shrink-0">
                <Send className="w-5 h-5 text-[var(--accent)]" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Telegram</h3>
                <p className="text-xs text-[var(--text-muted)]">Pair Telegram to this account for verified test delivery.</p>
              </div>
            </div>
            <span className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${
              status?.connected
                ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20'
                : 'text-[var(--text-muted)] bg-[var(--bg-raised)] border-[var(--border)]'
            }`}>
              {status?.connected ? <><CheckCircle className="w-3 h-3" /> Connected</> : 'Not connected'}
            </span>
          </div>

          {statusLoading && (
            <StatusNotice type="info">Loading Telegram connection status...</StatusNotice>
          )}

          {!statusLoading && error && (
            <div className="mb-4">
              <StatusNotice type="error">{error}</StatusNotice>
            </div>
          )}

          {!statusLoading && successMessage && (
            <div className="mb-4">
              <StatusNotice type="success">{successMessage}</StatusNotice>
            </div>
          )}

          {!statusLoading && !status?.connected && !activeCode && (
            <div className="space-y-5">
              <div className="bg-[var(--bg-base)] border border-[var(--border-muted)] rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <Link2 className="w-5 h-5 text-[var(--accent)] mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-white mb-1">Connect Telegram</h4>
                    <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                      Generate a secure pairing code and send it to the StatuteProof bot. No manual Chat ID copy-paste needed.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid sm:grid-cols-3 gap-3 text-xs text-[var(--text-secondary)]">
                {[
                  'The code expires after 15 minutes.',
                  'The bot links the chat to your account only.',
                  'Automatic scheduled delivery is not enabled yet.',
                ].map(t => (
                  <div key={t} className="bg-[var(--bg-base)] border border-[var(--border-muted)] rounded-lg px-3 py-2.5">
                    {t}
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={handleGenerate}
                disabled={generating}
                className="inline-flex items-center gap-2 text-xs font-semibold bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)] px-4 py-2.5 rounded-lg transition-colors disabled:opacity-70"
              >
                {generating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Link2 className="w-3.5 h-3.5" />}
                Generate code
              </button>
            </div>
          )}

          {!statusLoading && !status?.connected && activeCode && (
            <div className="space-y-5">
              <div className="bg-[var(--bg-base)] border border-[var(--trust-border)] rounded-xl p-5">
                <p className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Pairing code</p>
                <div className="font-mono text-3xl font-bold text-white mb-3">
                  {activeCode.code}
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  Expires at {formatDate(activeCode.expires_at)}. Send this command to the StatuteProof Telegram bot.
                </p>
              </div>

              {/* Live pairing status — flips to Connected on its own via auto-poll. */}
              {pairExpired ? (
                <div className="flex items-start gap-2 rounded-lg border border-amber-400/25 bg-amber-400/10 px-3 py-2.5 text-xs text-amber-200">
                  <XCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
                  <span>This pairing code has expired. Generate a new code to try again.</span>
                </div>
              ) : (
                <div className="flex items-start gap-2 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-3 py-2.5 text-xs text-[var(--accent)]">
                  <Loader2 className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 animate-spin" />
                  <span>
                    Waiting for your message to @{botUsername || 'statuteproofalerts_bot'}…
                    This confirms automatically once you send the command — no need to refresh.
                  </span>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                  Telegram command
                </label>
                <div className="flex gap-2">
                  <div className="flex-1 font-mono bg-[var(--bg-base)] border border-[var(--border)] rounded-lg px-3 py-2.5 text-sm text-[var(--accent)] overflow-x-auto">
                    {command}
                  </div>
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border)] px-3 py-2 rounded-lg transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {botLink && (
                  <a
                    href={botLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-xs font-medium text-[var(--accent)] border border-[var(--trust-border)] hover:border-[var(--trust-border)] px-3 py-2 rounded-lg transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Open @{botUsername}
                  </a>
                )}
                <button
                  type="button"
                  onClick={refreshStatus}
                  disabled={statusLoading}
                  className="inline-flex items-center gap-2 text-xs font-medium text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border)] px-3 py-2 rounded-lg transition-colors disabled:opacity-70"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh status
                </button>
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={generating}
                  className="inline-flex items-center gap-2 text-xs font-medium text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border)] px-3 py-2 rounded-lg transition-colors disabled:opacity-70"
                >
                  {generating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Link2 className="w-3.5 h-3.5" />}
                  New code
                </button>
              </div>
            </div>
          )}

          {!statusLoading && status?.connected && (
            <div className="space-y-5">
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-emerald-300 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-white mb-1">Telegram connected</h4>
                    <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                      This chat is linked to your StatuteProof account for test messages, sample brief delivery, and manual reviewed alert previews.
                      Automatic scheduled delivery is not enabled yet.
                    </p>
                  </div>
                </div>
              </div>

              <dl className="grid sm:grid-cols-2 gap-3 text-xs">
                <div className="bg-[var(--bg-base)] border border-[var(--border-muted)] rounded-lg px-3 py-2.5">
                  <dt className="text-[var(--text-muted)] mb-1">Telegram user</dt>
                  <dd className="text-[var(--text-primary)]">{status.telegram_username ? `@${status.telegram_username}` : 'Not provided'}</dd>
                </div>
                <div className="bg-[var(--bg-base)] border border-[var(--border-muted)] rounded-lg px-3 py-2.5">
                  <dt className="text-[var(--text-muted)] mb-1">Chat ID</dt>
                  <dd className="font-mono text-[var(--text-primary)]">{status.telegram_chat_id_masked || 'Masked'}</dd>
                </div>
                <div className="bg-[var(--bg-base)] border border-[var(--border-muted)] rounded-lg px-3 py-2.5">
                  <dt className="text-[var(--text-muted)] mb-1">Paired</dt>
                  <dd className="text-[var(--text-primary)]">{formatDate(status.paired_at)}</dd>
                </div>
                <div className="bg-[var(--bg-base)] border border-[var(--border-muted)] rounded-lg px-3 py-2.5">
                  <dt className="text-[var(--text-muted)] mb-1">Last test</dt>
                  <dd className="text-[var(--text-primary)]">{formatDate(status.last_test_at)}</dd>
                </div>
              </dl>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleTest}
                  disabled={testing}
                  className="inline-flex items-center gap-2 text-xs font-medium text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border)] px-3 py-2 rounded-lg transition-colors disabled:opacity-70"
                >
                  {testing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                  Send test message
                </button>
                <button
                  type="button"
                  onClick={handleSampleBrief}
                  disabled={briefStatus === 'sending'}
                  className="inline-flex items-center gap-2 text-xs font-medium text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border)] px-3 py-2 rounded-lg transition-colors disabled:opacity-70"
                >
                  {briefStatus === 'sending' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5" />}
                  Send sample brief
                </button>
                <button
                  type="button"
                  onClick={refreshStatus}
                  disabled={statusLoading}
                  className="inline-flex items-center gap-2 text-xs font-medium text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border)] px-3 py-2 rounded-lg transition-colors disabled:opacity-70"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh status
                </button>
                <button
                  type="button"
                  onClick={handleUnlink}
                  disabled={unlinking}
                  className="inline-flex items-center gap-2 text-xs font-medium text-rose-300 border border-rose-500/30 hover:border-rose-500/60 px-3 py-2 rounded-lg transition-colors disabled:opacity-70"
                >
                  {unlinking ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                  Unlink Telegram
                </button>
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                Send one sample reviewed brief to confirm delivery. Production routing remains manual during the founding pilot.
              </p>
              {briefStatus !== 'idle' && (
                <StatusNotice type={
                  briefStatus === 'ok' ? 'success' :
                  briefStatus === 'error' ? 'error' :
                  'info'
                }>
                  {briefStatus === 'sending' ? 'Sending sample brief...' : briefMsg}
                </StatusNotice>
              )}
            </div>
          )}

          <p className="mt-5 text-xs text-[var(--text-muted)] bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5 leading-relaxed">
            Security: the Telegram bot token stays server-side. The dashboard never accepts or stores a manual Chat ID.
          </p>
        </div>

        {/* Email + Webhook stubs */}
        <div className="flex flex-col gap-4">

          <div className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5 flex flex-col">
            <div className="flex items-start justify-between mb-4">
              <div className="w-10 h-10 rounded-xl bg-[var(--trust-badge)] border border-[var(--trust-border)] flex items-center justify-center">
                <Mail className="w-5 h-5 text-[var(--accent)]" />
              </div>
              <span className="text-xs font-medium text-[var(--accent)] bg-[var(--trust-badge)] border border-[var(--trust-border)] px-2.5 py-1 rounded-full">
                Test mode
              </span>
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">Email Brief Delivery</h3>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              Render a reviewed weekly brief email payload into the local outbox. Production provider readiness is visible here, but no external email is sent unless explicitly configured and enabled server-side.
            </p>
            <div className="mt-4 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] p-3">
              {emailReadinessLoading ? (
                <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Loading email readiness...
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-[11px] font-semibold text-[var(--text-muted)]">Current mode</p>
                      <p className="mt-0.5 text-xs font-semibold text-[var(--text-primary)]">{emailModeLabel(emailReadiness)}</p>
                    </div>
                    <StatusBadge code={emailReadiness?.status || 'local_outbox'} />
                  </div>
                  <dl className="grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <dt className="text-[var(--text-muted)]">Provider</dt>
                      <dd className="text-[var(--text-primary)]">{(emailReadiness?.provider || 'local_outbox') === 'local_outbox' ? 'Local outbox (no external provider)' : emailReadiness.provider}</dd>
                    </div>
                    <div>
                      <dt className="text-[var(--text-muted)]">External send</dt>
                      <dd className={emailReadiness?.send_enabled && emailReadiness?.provider_configured ? 'text-emerald-300' : 'text-[var(--text-primary)]'}>
                        {emailReadiness?.send_enabled && emailReadiness?.provider_configured ? 'Enabled by server config' : 'Disabled'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[var(--text-muted)]">From</dt>
                      <dd className="break-all text-[var(--text-primary)]">{emailReadiness?.from_email || 'Not configured'}</dd>
                    </div>
                    <div>
                      <dt className="text-[var(--text-muted)]">Last status</dt>
                      <dd className="text-[var(--text-primary)]">{emailReadiness?.last_delivery_status?.status || 'No delivery status yet'}</dd>
                    </div>
                  </dl>
                  {emailReadiness?.missing_config?.length ? (
                    <div>
                      <p className="mb-1 text-[11px] font-semibold text-amber-300">Missing configuration</p>
                      <div className="flex flex-wrap gap-1">
                        {emailReadiness.missing_config.map(item => (
                          <span key={item} className="rounded border border-amber-400/25 bg-amber-400/10 px-1.5 py-0.5 text-[10px] text-amber-200">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <p className="text-[11px] leading-relaxed text-[var(--text-muted)]">
                    {emailReadiness?.customer_safe_status || 'Email delivery status is not available.'}
                  </p>
                  <button
                    type="button"
                    onClick={handleEmailConfigCheck}
                    disabled={emailConfigChecking}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-2.5 py-1.5 text-[11px] font-semibold text-[var(--text-primary)] hover:border-[var(--border)] hover:text-white disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {emailConfigChecking ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                    Check provider config
                  </button>
                </div>
              )}
            </div>
            <label className="mt-4 block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Test recipient</label>
            <input
              value={emailRecipient}
              onChange={event => setEmailRecipient(event.target.value)}
              placeholder="mlro@example.com"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-base)] px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
            />
            <button
              type="button"
              onClick={handleEmailTestMode}
              disabled={emailStatus === 'sending' || !emailRecipient.trim()}
              className="mt-3 inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--trust-border)] px-3 py-2 text-xs font-semibold text-[var(--accent)] transition-colors hover:border-[var(--trust-border)] disabled:cursor-not-allowed disabled:border-[var(--border)] disabled:text-[var(--text-muted)]"
            >
              {emailStatus === 'sending' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Mail className="w-3.5 h-3.5" />}
              Write email payload
            </button>
            <p className="mt-3 text-[11px] leading-relaxed text-[var(--text-secondary)]">
              Test-mode writes a local payload and delivery-status row. No provider secrets are shown in the dashboard. Monitoring intelligence only. Not legal advice.
            </p>
            {emailStatus !== 'idle' && (
              <div className="mt-3">
                <StatusNotice type={
                  emailStatus === 'ok' ? 'success' :
                  emailStatus === 'error' ? 'error' :
                  'info'
                }>
                  {emailStatus === 'sending' ? 'Writing email payload...' : emailMsg}
                </StatusNotice>
              </div>
            )}
          </div>

          {/* opacity-60 on a whole card dropped its body text below 4.5:1. The
              "coming later" read now comes from the copy and aria-disabled,
              not from making the words hard to see. */}
          <div aria-disabled="true" className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5 flex flex-col opacity-80">
            <div className="flex items-start justify-between mb-4">
              <div className="w-10 h-10 rounded-xl bg-[var(--bg-raised)] border border-[var(--border)] flex items-center justify-center">
                <Webhook className="w-5 h-5 text-[var(--text-muted)]" />
              </div>
              <span className="text-xs font-medium text-[var(--text-muted)] bg-[var(--bg-raised)] border border-[var(--border)] px-2.5 py-1 rounded-full">
                Planned
              </span>
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">Webhook / API</h3>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              Push alert payloads to your own systems. REST webhook with JSON brief format.
            </p>
          </div>
        </div>
      </div>

      {/* Security strip */}
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl px-5 py-4">
        <h3 className="text-xs font-semibold text-white mb-3">Integration Security</h3>
        <div className="grid sm:grid-cols-3 gap-3 text-xs text-[var(--text-secondary)]">
          {[
            'Bot token stored server-side only and never exposed to clients',
            'Pairing codes are one-time account links with a 15-minute expiry',
            'Global admin Telegram settings remain separate from account pairing',
          ].map(t => (
            <div key={t} className="flex items-start gap-2">
              <Check className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-emerald-400" />
              <span>{t}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
