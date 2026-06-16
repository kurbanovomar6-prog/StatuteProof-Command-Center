import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle, ExternalLink, Search, Send, ShieldCheck } from 'lucide-react'

import { delivery } from '../../api'

const RISK_DARK = {
  HIGH: 'text-red-400 bg-red-500/15 border border-red-500/30',
  MEDIUM: 'text-amber-400 bg-amber-500/15 border border-amber-500/30',
  LOW: 'text-emerald-400 bg-emerald-500/15 border border-emerald-500/30',
}

function EmptyState() {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/35 px-6 py-12 text-center">
      <ShieldCheck className="mx-auto mb-3 h-8 w-8 text-slate-600" />
      <p className="text-sm font-semibold text-white">No reviewed alerts yet.</p>
      <p className="mx-auto mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
        Reviewed alerts will appear after monitored changes are detected, evidence is saved, and the item is approved for review.
        No sample alerts are shown in the authenticated workspace.
      </p>
    </div>
  )
}
export default function AlertsPage() {
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [riskFilter, setRiskFilter] = useState('All')
  const [search, setSearch] = useState('')
  const [sendState, setSendState] = useState({})

  useEffect(() => {
    let active = true
    delivery.preview(14)
      .then(data => {
        if (active) setPreview(data.preview || {})
      })
      .catch(err => {
        if (active) setError(err.message || 'Could not load reviewed alerts.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const filtered = useMemo(() => (preview?.matches || []).filter(item => {
    const risk = String(item.risk_level || 'MEDIUM').toUpperCase()
    if (riskFilter !== 'All' && risk !== riskFilter) return false
    const haystack = [
      item.title,
      item.source_name,
      item.market,
      item.jurisdiction,
      item.executive_summary,
    ].join(' ').toLowerCase()
    return !search || haystack.includes(search.toLowerCase())
  }), [preview, riskFilter, search])

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
    <div className="min-h-full space-y-5 bg-[#07111F] p-5 pb-10">
      <div>
        <h1 className="text-lg font-bold text-white mb-1">Reviewed Alerts</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-400">
          Real reviewed alert routing records only. Customer delivery remains manual/test-mode unless an approved delivery channel is configured.
        </p>
      </div>

      <div className="rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Reviewed alert routing</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-400">
              Alerts shown here come from approved local alert records matched against your workspace profile. This page does not create sample alerts.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Approved records only', 'Profile matched', 'Manual preview', 'Not legal advice'].map(label => (
              <span key={label} className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-slate-300">
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="relative w-full md:max-w-sm">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search reviewed alerts"
              value={search}
              onChange={event => setSearch(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 py-2 pl-9 pr-3 text-xs text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
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
                    ? 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300'
                    : 'border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                {risk === 'All' ? 'All risk' : risk}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading && (
        <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] px-5 py-8 text-sm text-slate-400">
          Loading reviewed alerts...
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/5 px-5 py-4">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-400" />
          <div>
            <p className="text-sm font-semibold text-rose-200">Could not load reviewed alerts.</p>
            <p className="mt-1 text-xs text-rose-300/80">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && <EmptyState />}

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
              <article key={item.alert_id} className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${RISK_DARK[risk] || RISK_DARK.MEDIUM}`}>
                    {risk}
                  </span>
                  <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                    {item.review_status || 'Approved'}
                  </span>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
                    item.matched
                      ? 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200'
                      : 'border-slate-700 bg-slate-900 text-slate-400'
                  }`}>
                    Relevance {item.score ?? 'n/a'}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-white">{item.title || 'Reviewed alert'}</h3>
                <p className="mt-1 text-xs text-slate-500">{item.market || item.jurisdiction || 'Market not specified'} · {item.source_name || 'Source not specified'}</p>
                <p className="mt-3 line-clamp-3 text-xs leading-relaxed text-slate-400">{item.executive_summary || 'No executive summary recorded.'}</p>
                {item.source_url && (
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-300 hover:text-cyan-200"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    Official source
                  </a>
                )}
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => handleSendPreviewAlert(item.alert_id)}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                      disabled
                        ? 'cursor-not-allowed border-slate-700 bg-slate-800/70 text-slate-500'
                        : 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200 hover:bg-cyan-400/15'
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
              </article>
            )
          })}
        </div>
      )}

      <p className="text-xs leading-relaxed text-slate-600">
        Monitoring intelligence only. Not legal advice. Users should verify official source material directly and consult qualified professionals before making regulatory decisions.
      </p>
    </div>
  )
}
