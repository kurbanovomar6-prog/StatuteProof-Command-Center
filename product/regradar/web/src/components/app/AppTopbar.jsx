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
      industries: Array.isArray(p.industries) ? p.industries : [],
      initials: displayName.charAt(0).toUpperCase(),
    }
  } catch {
    const company = currentUser?.company_name || 'Profile workspace'
    const displayName = currentUser?.full_name || company || currentUser?.email || 'Profile workspace'
    return { company, displayName, markets: [], industries: [], initials: displayName.charAt(0).toUpperCase() }
  }
}

export default function AppTopbar({ page, onMenuClick, navigate, currentUser }) {
  const ws = getWorkspace(currentUser)
  const labels = {
    dashboard:    'Dashboard',
    sources:      'Source Map',
    evidence:     'Evidence Records',
    alerts:       'Sample Alerts',
    briefs:       'Brief Previews',
    reports:      'Source Reports',
    integrations: 'Integrations',
    settings:     'Settings',
  }

  return (
    <header className="flex-shrink-0 h-16 bg-[#07111F]/80 backdrop-blur-md border-b border-slate-800 flex items-center px-6 gap-4 sticky top-0 z-40">

      {/* Mobile menu toggle */}
      <button onClick={onMenuClick} className="lg:hidden p-1.5 rounded text-slate-400 hover:text-white">
        <Menu className="w-5 h-5" />
      </button>

      {/* Left: workspace name + pilot status */}
      <div className="min-w-0 flex items-center gap-4">
        <div className="min-w-0">
          <span className="block text-white font-medium text-sm">{labels[page] || 'StatuteProof'}</span>
          <span className="hidden sm:block text-xs text-slate-500 truncate">
            {ws.company} · {ws.markets.length ? ws.markets.slice(0, 2).join(', ') : 'Profile setup'}
          </span>
        </div>
        <div className="hidden md:flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/20 text-cyan-200 text-xs font-semibold px-2.5 py-1 rounded">
          <ShieldCheck className="w-3 h-3" />
          Sources staged after validation
        </div>
      </div>

      <div className="ml-auto flex items-center gap-4">
        <span className="hidden lg:block text-xs text-slate-400">
          Workspace: <span className="text-slate-300">{ws.displayName}</span>
        </span>

        <button
          onClick={() => navigate('sources')}
          className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors"
        >
          Review source map
        </button>

        {/* User avatar */}
        <div className="w-8 h-8 rounded-full bg-[#16D9F5]/20 border border-[#16D9F5]/30 flex items-center justify-center text-xs font-bold text-[#16D9F5] flex-shrink-0">
          {ws.initials}
        </div>
      </div>
    </header>
  )
}
