import { lazy, Suspense, useState } from 'react'
import { appPageToPath } from '../../routeMap'
import AppSidebar from './AppSidebar'
import AppTopbar from './AppTopbar'

const DashboardHome   = lazy(() => import('./DashboardHome'))
const SourcesPage     = lazy(() => import('./SourcesPage'))
const SourceLabPage   = lazy(() => import('./SourceLabPage'))
const AlertsPage      = lazy(() => import('./AlertsPage'))
const AIBriefPage     = lazy(() => import('./AIBriefPage'))
const ReportsPage     = lazy(() => import('./ReportsPage'))
const ReviewQueuePage = lazy(() => import('./ReviewQueuePage'))
const IntegrationsPage = lazy(() => import('./IntegrationsPage'))
const SettingsPage    = lazy(() => import('./SettingsPage'))
const EvidencePage    = lazy(() => import('./EvidencePage'))
const BillingPage     = lazy(() => import('./BillingPage'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-full min-h-[300px]">
      <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-[#16D9F5]" />
    </div>
  )
}

export default function AppShell({ initialPage = 'dashboard', currentUser, onSignOut, planState, onChoosePlan }) {
  const [page, setPage]           = useState(initialPage)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  function navigate(target) {
    setPage(target)
    setMobileOpen(false)
    if (typeof window !== 'undefined') {
      const path = appPageToPath(target)
      if (window.location.pathname !== path) {
        window.history.pushState({}, '', path)
      }
    }
  }

  function renderPage() {
    switch (page) {
      case 'dashboard':    return <DashboardHome navigate={navigate} currentUser={currentUser} planState={planState} onChoosePlan={onChoosePlan} />
      case 'sources':      return <SourcesPage onAddCustomSource={() => navigate('source-lab')} />
      case 'source-lab':   return <SourceLabPage planState={planState} onChoosePlan={onChoosePlan} />
      case 'evidence':     return <EvidencePage />
      case 'alerts':       return <AlertsPage />
      case 'briefs':       return <AIBriefPage />
      case 'reports':      return <ReportsPage />
      case 'review-queue': return <ReviewQueuePage />
      case 'integrations': return <IntegrationsPage />
      case 'billing':      return <BillingPage planState={planState} />
      case 'settings':     return <SettingsPage onResetWorkspace={onSignOut} planState={planState} />
      default:             return <DashboardHome navigate={navigate} currentUser={currentUser} planState={planState} onChoosePlan={onChoosePlan} />
    }
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
          planState={planState}
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
          <Suspense fallback={<PageLoader />}>
            {renderPage()}
          </Suspense>
        </main>
      </div>
    </div>
  )
}
