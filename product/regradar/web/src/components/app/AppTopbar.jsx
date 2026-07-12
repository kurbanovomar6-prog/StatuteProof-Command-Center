import { useEffect, useState } from 'react'
import { Menu, RefreshCw, WifiOff } from 'lucide-react'

function getWorkspace(currentUser) {
  try {
    const p = JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
    const company = p.company || currentUser?.company_name || 'Profile workspace'
    const displayName = currentUser?.full_name || company || currentUser?.email || 'Profile workspace'
    return {
      company,
      displayName,
      markets: Array.isArray(p.markets) ? p.markets : [],
      initials: displayName.charAt(0).toUpperCase(),
    }
  } catch {
    const company = currentUser?.company_name || 'Profile workspace'
    const displayName = currentUser?.full_name || company || currentUser?.email || 'Profile workspace'
    return { company, displayName, markets: [], initials: displayName.charAt(0).toUpperCase() }
  }
}

const PAGE_LABELS = {
  dashboard:    'Dashboard',
  sources:      'Source Map',
  'source-lab': 'Source Lab',
  evidence:     'Evidence Records',
  'review-queue': 'Review Queue',
  alerts:       'Reviewed Alerts',
  briefs:       'Monitoring Briefs',
  reports:      'Audit Reports',
  integrations: 'Integrations',
  billing:      'Plan & Billing',
  settings:     'Settings',
}

function useApiHealth() {
  const [status, setStatus] = useState('ok') // 'ok' | 'degraded' | 'unreachable'
  const [checkKey, setCheckKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    fetch('/api/health')
      .then(r => r.json())
      .then(d => {
        // Health payload shape: {"ok": true, "db": "connected", ...}
        const healthy = d.ok === true || d.status === 'ok'
        if (!cancelled) setStatus(healthy ? 'ok' : 'degraded')
      })
      .catch(() => {
        if (cancelled) return
        setStatus('unreachable')
        // Developer hint only — never surfaced to customers.
        console.warn('[StatuteProof] Could not reach /api/health. If running locally, start the API with: python run.py api')
      })
    return () => { cancelled = true }
  }, [checkKey])

  return { status, recheck: () => setCheckKey(k => k + 1) }
}

export default function AppTopbar({ page, onMenuClick, navigate, currentUser }) {
  const ws = getWorkspace(currentUser)
  const { status: apiHealth, recheck: recheckHealth } = useApiHealth()

  return (
    <>
      <header className="sticky top-0 z-40 flex h-14 flex-shrink-0 items-center gap-4 border-b border-[var(--border-muted)] bg-[var(--bg-navy)] px-4 sm:px-5">

        {/* Mobile menu toggle */}
        <button
          onClick={onMenuClick}
          className="flex min-h-10 min-w-10 items-center justify-center rounded text-[var(--text-secondary)] transition-colors hover:text-white lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Left: page title + workspace sub */}
        <div className="min-w-0 flex items-center gap-4 flex-1">
          <div className="min-w-0">
            <span className="block text-sm font-semibold text-white">
              {PAGE_LABELS[page] || 'StatuteProof'}
            </span>
            <span className="hidden sm:block text-xs text-[var(--text-muted)] truncate">
              {ws.company}
              {ws.markets.length ? ' · ' + ws.markets.slice(0, 2).join(', ') : ' · Profile setup'}
            </span>
          </div>

        </div>

        {/* Right: workspace label + source review button + avatar */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <span className="hidden lg:block text-xs text-[var(--text-muted)]">
            Workspace: <span className="text-[var(--text-primary)] font-medium">{ws.displayName}</span>
          </span>

          <button
            onClick={() => navigate('sources')}
            className="hidden min-h-10 items-center gap-1.5 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-3 py-1.5 text-xs font-semibold text-[var(--accent)] transition-colors hover:bg-[var(--trust-badge)] sm:inline-flex"
          >
            Review source map
          </button>

          {/* User avatar */}
          <div className="w-8 h-8 rounded-full bg-[var(--trust-badge)] border border-[var(--trust-border)] flex items-center justify-center text-xs font-bold text-[var(--accent)] flex-shrink-0 select-none">
            {ws.initials}
          </div>
        </div>
      </header>

      {/* Connection notice — only shown when status is not ok. Plain,
          reassuring language for non-technical users; the developer hint
          goes to the console, never to the customer. */}
      {apiHealth !== 'ok' && (
        <div className="flex flex-wrap items-center gap-2 border-b border-amber-500/20 bg-amber-500/10 px-4 py-2 text-xs text-amber-200">
          <WifiOff className="h-3.5 w-3.5 flex-shrink-0" />
          <span>
            {apiHealth === 'unreachable'
              ? "We can't reach StatuteProof right now — your data is safe. Please retry in a moment."
              : "Some information may be delayed while a check finishes — your data is safe. Please retry in a moment."}
          </span>
          <button
            type="button"
            onClick={recheckHealth}
            className="ml-auto inline-flex min-h-8 items-center gap-1.5 rounded-md border border-amber-400/40 bg-amber-400/10 px-2.5 py-1 font-semibold text-amber-100 transition-colors hover:bg-amber-400/20"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </button>
        </div>
      )}
    </>
  )
}
