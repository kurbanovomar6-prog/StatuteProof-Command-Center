import { Menu, ShieldCheck } from 'lucide-react'

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

export default function AppTopbar({ page, onMenuClick, navigate, currentUser }) {
  const ws = getWorkspace(currentUser)

  return (
    <header className="flex-shrink-0 h-14 bg-[#07111F] border-b border-slate-800 flex items-center px-5 gap-4 sticky top-0 z-40">

      {/* Mobile menu toggle */}
      <button
        onClick={onMenuClick}
        className="lg:hidden p-1.5 rounded text-slate-400 hover:text-white transition-colors"
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
          <span className="hidden sm:block text-xs text-slate-500 truncate">
            {ws.company}
            {ws.markets.length ? ' · ' + ws.markets.slice(0, 2).join(', ') : ' · Profile setup'}
          </span>
        </div>

        <div className="hidden md:flex items-center gap-1.5 bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-semibold px-2.5 py-1 rounded-full">
          <ShieldCheck className="w-3 h-3" />
          Sources staged after validation
        </div>
      </div>

      {/* Right: workspace label + source review button + avatar */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <span className="hidden lg:block text-xs text-slate-500">
          Workspace: <span className="text-slate-300 font-medium">{ws.displayName}</span>
        </span>

        <button
          onClick={() => navigate('sources')}
          className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold text-[#16D9F5] bg-[#16D9F5]/10 hover:bg-[#16D9F5]/20 border border-[#16D9F5]/20 px-3 py-1.5 rounded-lg transition-colors"
        >
          Review source map
        </button>

        {/* User avatar */}
        <div className="w-8 h-8 rounded-full bg-[#16D9F5]/20 border border-[#16D9F5]/30 flex items-center justify-center text-xs font-bold text-[#16D9F5] flex-shrink-0 select-none">
          {ws.initials}
        </div>
      </div>
    </header>
  )
}
