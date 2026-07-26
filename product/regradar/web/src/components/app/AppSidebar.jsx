import { LayoutDashboard, Globe, Bell, FileText, BarChart3, Plug, Settings, ChevronLeft, ChevronRight, LogOut, ShieldCheck, CreditCard, FlaskConical, ClipboardCheck, Activity } from 'lucide-react'

// Twelve destinations in one flat list, in three different capitalisation
// styles ("Monitoring health" beside "Review Queue"), several named after the
// machinery rather than the job ("Source Lab", "Monitoring Briefs"). An MLRO
// opening this for the first time cannot tell which of the twelve answers their
// question.
//
// Grouped by what the person is trying to DO, sentence case throughout, and
// named for the outcome. The ids are untouched — they are the routes.
const NAV_GROUPS = [
  {
    heading: null,
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    heading: 'Watch',
    items: [
      { id: 'sources',           label: 'Sources',        icon: Globe },
      { id: 'source-lab',        label: 'Add a source',   icon: FlaskConical },
      { id: 'monitoring-health', label: 'Source health',  icon: Activity },
    ],
  },
  {
    heading: 'Decide',
    items: [
      { id: 'review-queue', label: 'Review queue', icon: ClipboardCheck },
      { id: 'alerts',       label: 'Alerts',       icon: Bell },
      { id: 'evidence',     label: 'Evidence',     icon: ShieldCheck },
    ],
  },
  {
    heading: 'Report',
    items: [
      { id: 'briefs',  label: 'Briefs',  icon: FileText },
      { id: 'reports', label: 'Reports', icon: BarChart3 },
    ],
  },
  {
    heading: 'Account',
    items: [
      { id: 'integrations', label: 'Integrations', icon: Plug },
      { id: 'billing',      label: 'Billing',      icon: CreditCard },
      { id: 'settings',     label: 'Settings',     icon: Settings },
    ],
  },
]

function getWorkspace(currentUser) {
  try {
    const p = JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
    const company = p.company || currentUser?.company_name || 'Profile workspace'
    const displayName = currentUser?.full_name || company || currentUser?.email || 'Profile workspace'
    const email = currentUser?.email || p.email || ''
    return {
      company,
      displayName,
      email,
      markets: Array.isArray(p.markets) ? p.markets : [],
      initials: (displayName || 'P').charAt(0).toUpperCase(),
    }
  } catch {
    const displayName = currentUser?.full_name || currentUser?.company_name || currentUser?.email || 'Profile workspace'
    return {
      company: currentUser?.company_name || 'Profile workspace',
      displayName,
      email: currentUser?.email || '',
      markets: [],
      initials: displayName.charAt(0).toUpperCase(),
    }
  }
}

function planDisplay(planState) {
  if (planState?.plan_name === 'evidence_preview') return 'Source Readiness Review'
  return planState?.plan_display || 'Source Readiness Review'
}

export default function AppSidebar({ page, navigate, collapsed, onToggle, currentUser, planState, onSignOut }) {
  const ws = getWorkspace(currentUser)
  const planLabel = planDisplay(planState)

  return (
    <aside className={`flex-shrink-0 flex h-dvh min-h-dvh flex-col bg-[var(--bg-surface)] border-r border-[var(--border-muted)] transition-all duration-200 ${collapsed ? 'w-16' : 'w-64'}`}>

      {/* Logo */}
      <div className="flex items-center justify-between px-4 h-14 border-b border-[var(--border-muted)] flex-shrink-0">
        {!collapsed && (
          <button
            onClick={() => navigate('dashboard')}
            className="flex items-center gap-2 min-w-0"
          >
            <img src="/brand/regradar-logo-navbar.png" alt="" aria-hidden="true" className="h-7 w-auto flex-shrink-0" />
            <span className="sp-display text-sm font-extrabold text-white tracking-tight truncate">
              Statute<span className="text-[var(--accent)]">Proof</span>
            </span>
          </button>
        )}
        {collapsed && (
          <button
            type="button"
            onClick={() => navigate('dashboard')}
            aria-label="Go to dashboard"
            className="mx-auto flex items-center justify-center"
          >
            <img
              src="/brand/regradar-favicon-512.png"
              alt="StatuteProof"
              className="h-6 w-6 object-contain"
            />
          </button>
        )}
        <button
          onClick={onToggle}
          className="flex min-h-9 min-w-9 flex-shrink-0 items-center justify-center rounded text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed
            ? <ChevronRight className="w-3.5 h-3.5" />
            : <ChevronLeft className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto">
        {NAV_GROUPS.map((group, groupIndex) => (
          <div key={group.heading || 'primary'} className={groupIndex > 0 ? 'mt-5' : ''}>
            {/* Headings are hidden when the rail is collapsed: a truncated
                three-letter label is noise, and the icons still group visually
                through the spacing. */}
            {group.heading && !collapsed && (
              <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                {group.heading}
              </p>
            )}
            {group.items.map(({ id, label, icon: Icon }) => {
              const active = page === id
              return (
                <button
                  key={id}
                  onClick={() => navigate(id)}
                  aria-current={active ? 'page' : undefined}
                  title={collapsed ? label : undefined}
                  className={`relative flex min-h-11 w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                    active
                      ? 'bg-[var(--trust-badge)] text-[var(--accent)] border-r-2 border-[var(--accent)]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-raised)] border-r-2 border-transparent'
                  } ${collapsed ? 'justify-center' : ''}`}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 ${active ? 'text-[var(--accent)]' : ''}`} />
                  {!collapsed && <span className="truncate">{label}</span>}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Footer — user + sign out */}
      <div className="px-3 py-4 border-t border-[var(--border-muted)] flex-shrink-0">
        {!collapsed ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-full bg-[var(--trust-badge)] border border-[var(--trust-border)] flex items-center justify-center text-xs font-bold text-[var(--accent)] flex-shrink-0">
                {ws.initials}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-white truncate">{ws.displayName}</p>
                <p className="text-xs text-[var(--text-muted)] truncate">{ws.email || ws.company || planLabel}</p>
              </div>
            </div>

            <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-navy)] px-2.5 py-2 text-[11px]">
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="text-[var(--text-muted)]">Workspace</span>
                <span className="max-w-[140px] truncate rounded-full border border-[var(--trust-border)] bg-[var(--trust-badge)] px-2 py-0.5 font-semibold text-[var(--accent)]" title={planLabel}>
                  {planLabel}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-[var(--text-muted)]">Source map</span>
                <span className="text-[var(--text-secondary)]">{ws.markets.length ? 'Mapped' : 'Setup pending'}</span>
              </div>
            </div>

            <button
              onClick={onSignOut}
              className="flex min-h-10 w-full items-center gap-2 px-1 py-1 text-xs text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign out
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-7 h-7 rounded-full bg-[var(--trust-badge)] border border-[var(--trust-border)] flex items-center justify-center text-xs font-bold text-[var(--accent)]">
              {ws.initials}
            </div>
            <button
              onClick={onSignOut}
              className="flex min-h-10 min-w-10 items-center justify-center text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}
