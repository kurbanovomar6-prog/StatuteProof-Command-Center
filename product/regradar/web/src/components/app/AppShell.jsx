import { useState } from 'react'
import AppSidebar from './AppSidebar'
import AppTopbar from './AppTopbar'
import DashboardHome from './DashboardHome'
import SourcesPage from './SourcesPage'
import AlertsPage from './AlertsPage'
import AIBriefPage from './AIBriefPage'
import ReportsPage from './ReportsPage'
import IntegrationsPage from './IntegrationsPage'
import SettingsPage from './SettingsPage'

export default function AppShell({ initialPage = 'dashboard', currentUser, onSignOut }) {
  const [page, setPage]         = useState(initialPage)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  function navigate(target) {
    setPage(target)
    setMobileOpen(false)
  }

  const PAGE = {
    dashboard:    <DashboardHome navigate={navigate} currentUser={currentUser} />,
    sources:      <SourcesPage />,
    alerts:       <AlertsPage />,
    briefs:       <AIBriefPage />,
    reports:      <ReportsPage />,
    integrations: <IntegrationsPage />,
    settings:     <SettingsPage onResetWorkspace={onSignOut} />,
  }

  return (
    <div className="flex h-screen bg-[#07111F] overflow-hidden">

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-[#07111F]/70 z-30 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-40 lg:static lg:z-auto
        transition-transform duration-200
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <AppSidebar
          page={page}
          navigate={navigate}
          collapsed={collapsed}
          onToggle={() => setCollapsed(c => !c)}
          currentUser={currentUser}
          onSignOut={onSignOut}
        />
      </div>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <AppTopbar
          page={page}
          onMenuClick={() => setMobileOpen(o => !o)}
          navigate={navigate}
          currentUser={currentUser}
        />
        <main className="flex-1 overflow-y-auto">
          {PAGE[page] || PAGE.dashboard}
        </main>
      </div>
    </div>
  )
}
