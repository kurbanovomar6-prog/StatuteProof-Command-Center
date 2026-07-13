import { useEffect, useMemo, useState } from 'react'
import { CheckCircle, ExternalLink, Search, Send, ShieldCheck } from 'lucide-react'

import { delivery } from '../../api'
import ActionLogPanel from './ActionLogPanel'
import AlertChecklistPanel from './AlertChecklistPanel'
import AlertDecisionPanel from './AlertDecisionPanel'
import AlertProofPanel from './AlertProofPanel'
import { RISK_BAND_LEGEND, riskBand } from './riskBands'
import EmptyState from './ui/EmptyState'
import ErrorState from './ui/ErrorState'

// A band is colour + text label + a review-priority definition (never colour
// alone). The colour comes from a design token; the label and the "Priority: …"
// line make it legible to colour-blind and screen-reader users.
function RiskBand({ level }) {
  const band = riskBand(level)
  return (
    <span className="inline-flex items-center gap-2">
      <span
        title={band.priority}
        aria-label={`${band.label} risk. ${band.priority}`}
        className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-bold"
        style={{
          color: band.color,
          borderColor: band.color,
          backgroundColor: `color-mix(in srgb, ${band.color} 14%, transparent)`,
        }}
      >
        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: band.color }} aria-hidden="true" />
        {band.label} risk
      </span>
      {/* Visible for sighted users; the badge aria-label already carries it, so
          it is hidden from the a11y tree to avoid a duplicate announcement. */}
      <span aria-hidden="true" className="text-[10px] font-medium text-[var(--text-muted)]">{band.priority}</span>
    </span>
  )
}

function AlertsEmpty() {
  return (
    <EmptyState
      icon={ShieldCheck}
      title="No reviewed alerts yet."
      className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-base)]"
    >
      Reviewed alerts will appear after monitored changes are detected, evidence
      is saved, and the item is approved for review. No sample alerts are shown
      in the authenticated workspace.
    </EmptyState>
  )
}
export default function AlertsPage({ navigate }) {
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [riskFilter, setRiskFilter] = useState('All')
  const [search, setSearch] = useState('')
  const [licenceFilter, setLicenceFilter] = useState('All')
  const [sendState, setSendState] = useState({})

  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    delivery.preview(14)
      .then(data => {
        if (active) { setPreview(data.preview || {}); setError('') }
      })
      .catch(err => {
        if (active) setError(err.message || 'Could not load reviewed alerts.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [reloadKey])

  function retryAlerts() {
    setLoading(true)
    setError('')
    setReloadKey(k => k + 1)
  }

  const filtered = useMemo(() => (preview?.matches || []).filter(item => {
    const risk = String(item.risk_level || 'MEDIUM').toUpperCase()
    if (riskFilter !== 'All' && risk !== riskFilter) return false
    if (licenceFilter !== 'All') {
      const types = Array.isArray(item.affected_licence_types) ? item.affected_licence_types : []
      if (!types.some(t => String(t).toLowerCase().includes(licenceFilter.toLowerCase()))) return false
    }
    const haystack = [
      item.title,
      item.source_name,
      item.market,
      item.jurisdiction,
      item.executive_summary,
    ].join(' ').toLowerCase()
    return !search || haystack.includes(search.toLowerCase())
  }), [preview, riskFilter, search, licenceFilter])

  async function handleSendPreviewAlert(alertId) {
    setSendState(prev => ({ ...prev, [alertId]: { status: 'sending', message: '' } }))
    try {
      const result = await delivery.sendPreviewAlert(alertId)
      setSendState(prev => ({
        ...prev,
        [alertId]: { status: 'ok', message: result.message || 'Preview alert sent.' },
      }))
      const data = await delivery.preview(14)
      setPreview(data.preview || {})
    } catch (err) {
      setSendState(prev => ({
        ...prev,
        [alertId]: { status: 'error', message: err.message || 'Could not send preview alert.' },
      }))
    }
  }

  return (
    <div className="min-h-full space-y-5 bg-[var(--bg-navy)] p-5 pb-10">
      <div>
        <h1 className="text-lg font-bold text-white mb-1">Reviewed Alerts</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
          Real reviewed alert routing records only. Customer delivery remains manual/test-mode unless an approved delivery channel is configured.
        </p>
      </div>

      <div className="rounded-xl border border-[var(--trust-border)] bg-[var(--bg-elevated)] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Reviewed alert routing</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
              Alerts shown here come from approved local alert records matched against your workspace profile. This page does not create sample alerts.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="relative w-full md:max-w-sm">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search reviewed alerts"
              value={search}
              onChange={event => setSearch(event.target.value)}
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] py-2 pl-9 pr-3 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none"
            />
          </div>
          <div className="flex flex-wrap gap-1.5">
            {['All', 'HIGH', 'MEDIUM', 'LOW'].map(risk => (
              <button
                key={risk}
                type="button"
                onClick={() => setRiskFilter(risk)}
                className={`rounded-lg border px-2.5 py-1 text-xs transition-colors ${
                  riskFilter === risk
                    ? 'border-[var(--trust-border)] bg-[var(--trust-badge)] text-[var(--accent)]'
                    : 'border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                {risk === 'All' ? 'All risk' : risk.charAt(0) + risk.slice(1).toLowerCase() + ' risk'}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[11px] font-semibold text-[var(--text-muted)] whitespace-nowrap">Licence type</label>
            <select
              value={licenceFilter}
              onChange={e => setLicenceFilter(e.target.value)}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] py-1.5 pl-2.5 pr-8 text-xs text-[var(--text-primary)] focus:border-[var(--trust-border)] focus:outline-none"
            >
              <option value="All">All types</option>
              <option value="VASP">VASP</option>
              <option value="CBUAE">CBUAE Payment Institution</option>
              <option value="DIFC">DIFC Licence</option>
              <option value="ADGM">ADGM Licence</option>
              <option value="DFSA">DFSA Regulated</option>
            </select>
          </div>
        </div>
        <p className="mt-3 text-[11px] leading-relaxed text-[var(--text-muted)]">{RISK_BAND_LEGEND}</p>
      </div>

      {loading && (
        <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-5 py-8 text-sm text-[var(--text-secondary)]">
          Loading reviewed alerts...
        </div>
      )}

      {!loading && error && (
        <ErrorState
          title="Could not load reviewed alerts."
          detail={error}
          onRetry={retryAlerts}
          className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)]"
        />
      )}

      {!loading && !error && filtered.length === 0 && <AlertsEmpty />}

      {!loading && !error && filtered.length > 0 && (
        <div className="grid gap-3 xl:grid-cols-2">
          {filtered.map(item => {
            const risk = String(item.risk_level || 'MEDIUM').toUpperCase()
            const state = sendState[item.alert_id] || {}
            const disabled = !item.delivery_ready || state.status === 'sending'
            const disabledText = item.already_sent
              ? 'Sent'
              : !item.matched
              ? 'Not matched to profile'
              : item.not_ready_reasons?.[0] || 'Not ready'
            return (
              <article key={item.alert_id} className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <RiskBand level={risk} />
                  <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                    {item.review_status || 'Approved'}
                  </span>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
                    item.matched
                      ? 'border-[var(--trust-border)] bg-[var(--trust-badge)] text-[var(--accent)]'
                      : 'border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--text-secondary)]'
                  }`}>
                    Relevance {item.score ?? 'n/a'}
                  </span>
                  {item.action_orientation?.label && (
                    <span
                      title="A review-workflow prompt, not a legal obligation."
                      className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
                        item.action_orientation.code === 'actionable'
                          ? 'border-amber-400/30 bg-amber-400/10 text-amber-300'
                          : item.action_orientation.code === 'indicative'
                          ? 'border-sky-400/30 bg-sky-400/10 text-sky-300'
                          : 'border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--text-secondary)]'
                      }`}
                    >
                      {item.action_orientation.label}
                    </span>
                  )}
                </div>
                <h3 className="text-sm font-semibold text-white">{item.title || 'Reviewed alert'}</h3>
                <p className="mt-1 text-xs text-[var(--text-muted)]">{item.market || item.jurisdiction || 'Market not specified'} · {item.source_name || 'Source not specified'}</p>
                <p className="mt-3 line-clamp-3 text-xs leading-relaxed text-[var(--text-secondary)]">{item.executive_summary || 'No executive summary recorded.'}</p>
                {item.source_url && (
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--accent)] hover:text-[var(--accent)]"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    Official source
                  </a>
                )}
                <AlertProofPanel item={item} navigate={navigate} />
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => handleSendPreviewAlert(item.alert_id)}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                      disabled
                        ? 'cursor-not-allowed border-[var(--border)] bg-[var(--bg-raised)] text-[var(--text-muted)]'
                        : 'border-[var(--trust-border)] bg-[var(--trust-badge)] text-[var(--accent)] hover:bg-[var(--trust-badge)]'
                    }`}
                  >
                    {item.delivery_ready ? <Send className="h-3.5 w-3.5" /> : <CheckCircle className="h-3.5 w-3.5" />}
                    {state.status === 'sending' ? 'Sending...' : item.delivery_ready ? 'Send preview to Telegram' : disabledText}
                  </button>
                  {state.message && (
                    <span className={`text-xs ${state.status === 'ok' ? 'text-emerald-300' : 'text-rose-300'}`}>
                      {state.message}
                    </span>
                  )}
                </div>
                <AlertChecklistPanel alertId={item.alert_id} />
                <AlertDecisionPanel alertId={item.alert_id} />
                <ActionLogPanel alertId={item.alert_id} />
              </article>
            )
          })}
        </div>
      )}

      <p className="text-xs leading-relaxed text-[var(--text-secondary)]">
        Monitoring intelligence only. Not legal advice. Users should verify official source material directly and consult qualified professionals before making regulatory decisions.
      </p>
    </div>
  )
}
