import { useEffect, useState } from 'react'
import { ShieldCheck, CheckCircle2, XCircle } from 'lucide-react'
import { admin } from '../../api'

const PLAN_DISPLAY = {
  evidence_preview: 'Source Readiness Review',
  starter_pilot: 'Founding Pilot',
  professional: 'UAE Monitor',
  consultant: 'Compliance Consultant',
}

const PLAN_OPTIONS = [
  'evidence_preview',
  'starter_pilot',
  'professional',
  'consultant',
]

// Pre-select the tier the founder most likely wants: the customer's own
// requested intent when an activation is pending, else the current activated tier.
function defaultPlanFor(account) {
  if (account.needs_activation && PLAN_OPTIONS.includes(account.plan_name)) {
    return account.plan_name
  }
  return account.activated_plan || 'evidence_preview'
}

function Badge({ ok, yes, no }) {
  return ok ? (
    <span className="inline-flex items-center gap-1 text-xs text-emerald-300">
      <CheckCircle2 className="w-3.5 h-3.5" /> {yes}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs text-[var(--text-secondary)]">
      <XCircle className="w-3.5 h-3.5" /> {no}
    </span>
  )
}

export default function AdminPage() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [available, setAvailable] = useState(true)
  const [selection, setSelection] = useState({})   // { [userId]: planName }
  const [confirming, setConfirming] = useState(null) // userId pending confirm
  const [busyId, setBusyId] = useState(null)
  const [outcome, setOutcome] = useState(null)      // { ok, message }

  function applyAccounts(data) {
    setAccounts(Array.isArray(data?.accounts) ? data.accounts : [])
    setAvailable(true)
    setLoading(false)
  }

  function applyUnavailable() {
    // A non-founder account is answered 403 server-side; show a plain
    // not-available state and never the roster.
    setAvailable(false)
    setAccounts([])
    setLoading(false)
  }

  // Initial load. No synchronous setState in the effect body — the state writes
  // happen only in the async callbacks, per react-hooks/set-state-in-effect.
  useEffect(() => {
    let active = true
    admin.listAccounts()
      .then((data) => { if (active) applyAccounts(data) })
      .catch(() => { if (active) applyUnavailable() })
    return () => { active = false }
  }, [])

  async function activate(account) {
    const planName = selection[account.id] || defaultPlanFor(account)
    setBusyId(account.id)
    setOutcome(null)
    try {
      const data = await admin.activatePlan({ userId: account.id, planName })
      setOutcome({ ok: true, message: data.message || 'Plan activated.' })
      const refreshed = await admin.listAccounts().catch(() => null)
      if (refreshed) applyAccounts(refreshed)
    } catch (err) {
      setOutcome({ ok: false, message: err?.message || 'Activation failed.' })
    } finally {
      setBusyId(null)
      setConfirming(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[300px]">
        <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-[var(--accent)]" />
      </div>
    )
  }

  if (!available) {
    return (
      <div className="mx-auto max-w-2xl p-6">
        <div className="sp-panel p-6 text-center">
          <ShieldCheck className="w-6 h-6 text-[var(--text-secondary)] mx-auto mb-3" />
          <h1 className="text-lg font-semibold text-white mb-1">Admin tools are not available</h1>
          <p className="text-sm text-[var(--text-secondary)]">
            This area is reserved for the StatuteProof operator. It is not available for your account.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5 p-6">
      <div>
        <div className="sp-kicker mb-3">Operator tools</div>
        <h1 className="text-2xl font-semibold text-white mb-1">Accounts &amp; activation</h1>
        <p className="max-w-2xl text-sm text-[var(--text-secondary)]">
          Activate or change a customer&apos;s billing plan after source readiness review. Activation grants a
          billing tier only — it never changes a user&apos;s role. Every activation is written to the immutable
          audit log. No payment is processed here.
        </p>
      </div>

      {outcome ? (
        <div
          role="status"
          className={`rounded-xl border p-4 text-sm ${
            outcome.ok
              ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
              : 'border-amber-400/30 bg-amber-400/10 text-amber-200'
          }`}
        >
          {outcome.message}
        </div>
      ) : null}

      <div className="sp-panel p-0 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--border-muted)] text-xs text-[var(--text-secondary)]">
              <th className="px-4 py-3 font-medium">Account</th>
              <th className="px-4 py-3 font-medium">Verified</th>
              <th className="px-4 py-3 font-medium">Telegram</th>
              <th className="px-4 py-3 font-medium">Intent</th>
              <th className="px-4 py-3 font-medium">Activated</th>
              <th className="px-4 py-3 font-medium">Change plan</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => {
              const selected = selection[a.id] || defaultPlanFor(a)
              const isConfirming = confirming === a.id
              return (
                <tr key={a.id} className="border-b border-[var(--border-muted)] last:border-0 align-top">
                  <td className="px-4 py-3">
                    <div className="text-[var(--text-primary)]">{a.email}</div>
                    <div className="text-xs text-[var(--text-secondary)]">
                      #{a.id}
                      {a.needs_activation ? (
                        <span className="ml-2 text-amber-300">needs activation</span>
                      ) : null}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge ok={a.email_verified} yes="Verified" no="Unverified" />
                  </td>
                  <td className="px-4 py-3">
                    <Badge ok={a.telegram_linked} yes="Linked" no="Not linked" />
                  </td>
                  <td className="px-4 py-3 text-xs text-[var(--text-secondary)]">
                    {PLAN_DISPLAY[a.plan_name] || a.plan_name}
                  </td>
                  <td className="px-4 py-3 text-xs text-[var(--text-primary)]">
                    {PLAN_DISPLAY[a.activated_plan] || a.activated_plan}
                  </td>
                  <td className="px-4 py-3">
                    {isConfirming ? (
                      <div className="flex flex-col gap-2">
                        <span className="text-xs text-amber-200">
                          Activate {PLAN_DISPLAY[selected] || selected} for {a.email}?
                        </span>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            className="sp-btn-primary text-xs py-1 px-3 disabled:opacity-50"
                            disabled={busyId === a.id}
                            onClick={() => activate(a)}
                          >
                            {busyId === a.id ? 'Activating…' : 'Confirm'}
                          </button>
                          <button
                            type="button"
                            className="sp-btn-secondary text-xs py-1 px-3"
                            onClick={() => setConfirming(null)}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <select
                          aria-label={`Plan for ${a.email}`}
                          value={selected}
                          onChange={(e) =>
                            setSelection((s) => ({ ...s, [a.id]: e.target.value }))
                          }
                          className="bg-[var(--bg-raised)] border border-[var(--border)] rounded-md text-xs text-[var(--text-primary)] px-2 py-1"
                        >
                          {PLAN_OPTIONS.map((p) => (
                            <option key={p} value={p}>
                              {PLAN_DISPLAY[p]}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          className="sp-btn-secondary text-xs py-1 px-3"
                          onClick={() => setConfirming(a.id)}
                        >
                          Activate
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-[var(--text-secondary)] text-center">
        Not legal advice. Activation records a billing tier for internal pilot management only.
      </p>
    </div>
  )
}
