import { LayoutDashboard, Globe, Bell, FileText, BarChart3, Plug, Settings, ChevronLeft, LogOut, ShieldCheck } from 'lucide-react'

const NAV = [
  { id: 'dashboard',    label: 'Dashboard',      icon: LayoutDashboard },
  { id: 'sources',      label: 'Sources',         icon: Globe },
  { id: 'evidence',     label: 'Evidence',        icon: ShieldCheck },
  { id: 'alerts',       label: 'Sample Alerts',   icon: Bell },
  { id: 'briefs',       label: 'Brief Previews',  icon: FileText },
  { id: 'reports',      label: 'Source Reports',  icon: BarChart3 },
  { id: 'integrations', label: 'Integrations',    icon: Plug },
  { id: 'settings',     label: 'Settings',        icon: Settings },
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
    return { company: currentUser?.company_name || 'Profile workspace', displayName, email: currentUser?.email || '', markets: [], initials: displayName.charAt(0).toUpperCase() }
  }
}

export default function AppSidebar({ page, navigate, collapsed, onToggle, currentUser, onSignOut }) {
  const ws = getWorkspace(currentUser)

  function handleSignOut() {
    if (onSignOut) onSignOut()
  }

  return (
    <aside className={`flex-shrink-0 flex flex-col bg-[#07111F] border-r border-slate-800 transition-all duration-200 h-screen ${collapsed ? 'w-16' : 'w-64'}`}>

      {/* Logo */}
      <div className="flex items-center justify-between px-4 h-16 border-b border-slate-800 flex-shrink-0">
        {!collapsed && (
          <div className="cursor-pointer" onClick={() => navigate('dashboard')}>
            <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-8 w-auto" />
          </div>
        )}
        {collapsed && (
          <img
            src="/brand/regradar-favicon-512.png"
            alt="StatuteProof"
            className="h-7 w-7 mx-auto cursor-pointer object-contain"
            onClick={() => navigate('dashboard')}
          />
        )}
        {!collapsed && (
          <button
            onClick={onToggle}
            className="p-1 rounded text-slate-500 hover:text-slate-300 transition-colors"
            title="Collapse sidebar"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-5 space-y-0.5 overflow-y-auto">
        {NAV.map(({ id, label, icon: Icon, badge }) => {
          const active = page === id
          return (
            <button
              key={id}
              onClick={() => navigate(id)}
              title={collapsed ? label : undefined}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all relative ${
                active
                  ? 'bg-[#16D9F5]/10 text-[#16D9F5]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 flex-shrink-0 ${active ? 'text-[#16D9F5]' : ''}`} />
                {!collapsed && <span className="truncate">{label}</span>}
              </div>
              {badge && !collapsed && (
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${active ? 'bg-[#16D9F5]/20 text-[#16D9F5]' : 'bg-rose-500/20 text-rose-400'}`}>
                  {badge}
                </span>
              )}
              {badge && collapsed && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full" />
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-800 flex-shrink-0 space-y-2">
        {!collapsed ? (
          <>
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-full bg-[#16D9F5]/20 border border-[#16D9F5]/30 flex items-center justify-center text-xs font-bold text-[#16D9F5] flex-shrink-0">
                {ws.initials}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-white truncate">{ws.displayName}</p>
                <p className="text-xs text-slate-500 truncate">{ws.email || ws.company || 'Founding pilot'}</p>
              </div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-2.5 py-2 text-[11px] leading-relaxed">
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="text-slate-500">Workspace</span>
                <span className="rounded-full border border-cyan-400/25 bg-cyan-400/10 px-2 py-0.5 font-semibold text-cyan-200">
                  Founding pilot
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-slate-500">Source map</span>
                <span className="text-slate-300">{ws.markets.length ? 'Mapped' : 'Setup pending'}</span>
              </div>
            </div>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-300 transition-colors w-full px-1 py-0.5"
            >
              <LogOut className="w-3.5 h-3.5" /> Sign out
            </button>
          </>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-[#16D9F5]/20 border border-[#16D9F5]/30 flex items-center justify-center text-xs font-bold text-[#16D9F5]">
              {ws.initials}
            </div>
            <button
              onClick={handleSignOut}
              className="text-slate-500 hover:text-slate-300 transition-colors"
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
