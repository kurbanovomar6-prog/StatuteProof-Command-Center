import { useCallback, useEffect, useState } from 'react'
import { Loader2, UserPlus, X } from 'lucide-react'
import { team as teamApi } from '../../api'

// Seating a colleague used to require a founder SSH session. This is the door.
//
// The server is the control, not this component: member.manage is owner-only in
// the role matrix and every mutation goes through it. A non-owner who reaches
// this panel gets a 403 from the API, and the panel simply stops rendering the
// form rather than pretending the action is available.

const ROLES = [
  { value: 'auditor', label: 'Auditor', hint: 'Read evidence and reports' },
  { value: 'admin',   label: 'Admin',   hint: 'Manage sources and alerts' },
]

export default function TeamPanel() {
  const [members, setMembers] = useState(null)
  const [permitted, setPermitted] = useState(true)
  const [loading, setLoading] = useState(true)
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('auditor')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  // No setLoading(true): `loading` already starts true for the mount, and a
  // re-fetch after an add or revoke is covered by `busy`.
  const load = useCallback(async () => {
    try {
      const data = await teamApi.members()
      setMembers(data.members || [])
      setPermitted(true)
    } catch (err) {
      // 403 is the expected answer for a seated auditor, not a failure to report
      // as one — surfacing "something went wrong" there would be a lie.
      if (err?.status === 403) setPermitted(false)
      else setError(err?.message || 'Could not load the team list.')
    } finally {
      setLoading(false)
    }
  }, [])

  // Deferred rather than called straight from the effect body, matching
  // IntegrationsPage — a synchronous setState here cascades renders.
  useEffect(() => {
    const timer = window.setTimeout(() => { load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  async function handleAdd(event) {
    event.preventDefault()
    const address = email.trim()
    if (!address || busy) return
    setBusy(true); setError(''); setNotice('')
    try {
      await teamApi.add(address, role)
      setEmail('')
      setNotice(`${address} now has access to this workspace.`)
      await load()
    } catch (err) {
      setError(
        err?.status === 404
          ? `No StatuteProof account uses ${address} yet. Ask them to register first, then add them here.`
          : err?.message || 'Could not add that person.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function handleRevoke(address) {
    setBusy(true); setError(''); setNotice('')
    try {
      await teamApi.revoke(address)
      setNotice(`${address} no longer has access.`)
      await load()
    } catch (err) {
      setError(err?.message || 'Could not remove that person.')
    } finally {
      setBusy(false)
    }
  }

  if (!permitted) {
    return (
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5">
        <h2 className="text-sm font-semibold text-white mb-2">Team</h2>
        <p className="text-xs text-[var(--text-muted)] leading-relaxed">
          Only the workspace owner can add or remove people.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5">
      <h2 className="text-sm font-semibold text-white mb-1">Team</h2>
      <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-4">
        People you add can sign in with their own account and see this workspace&rsquo;s
        evidence. They must have registered first.
      </p>

      {loading ? (
        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
          Loading team&hellip;
        </div>
      ) : (
        <ul className="space-y-2 mb-4">
          {(members || []).map(member => (
            <li
              key={member.user_id}
              className="flex items-center justify-between gap-3 rounded-lg border border-[var(--border)] px-3 py-2"
            >
              <div className="min-w-0">
                <p className="text-xs text-white truncate">{member.email}</p>
                <p className="text-[11px] text-[var(--text-muted)] capitalize">{member.role}</p>
              </div>
              {member.role === 'owner' ? (
                <span className="text-[11px] text-[var(--text-muted)]">Owner</span>
              ) : (
                <button
                  type="button"
                  onClick={() => handleRevoke(member.email)}
                  disabled={busy}
                  aria-label={`Remove ${member.email}`}
                  className="text-[var(--text-muted)] hover:text-rose-400 transition-colors disabled:opacity-40"
                >
                  <X className="w-4 h-4" aria-hidden="true" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleAdd} className="flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="team-email">Colleague&rsquo;s email</label>
        <input
          id="team-email"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="colleague@yourfirm.com"
          className="flex-1 min-w-[12rem] bg-[var(--bg-base)] border border-[var(--border)] rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
        />
        <label className="sr-only" htmlFor="team-role">Role</label>
        <select
          id="team-role"
          value={role}
          onChange={e => setRole(e.target.value)}
          className="bg-[var(--bg-base)] border border-[var(--border)] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[var(--accent)]"
        >
          {ROLES.map(r => (
            <option key={r.value} value={r.value} title={r.hint}>{r.label}</option>
          ))}
        </select>
        <button
          type="submit"
          disabled={busy || !email.trim()}
          className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-1.5 rounded-lg bg-[var(--accent)] text-[var(--accent-contrast)] transition-opacity disabled:opacity-40"
        >
          {busy
            ? <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
            : <UserPlus className="w-3.5 h-3.5" aria-hidden="true" />}
          Add
        </button>
      </form>

      {error && <p role="alert" className="text-xs text-rose-400 mt-3">{error}</p>}
      {notice && <p role="status" className="text-xs text-emerald-400 mt-3">{notice}</p>}
    </div>
  )
}
