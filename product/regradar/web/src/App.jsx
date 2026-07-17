import { useEffect, useState, lazy, Suspense } from 'react'
import { auth, profile, plan as planApi } from './api'
import { appPageToPath, pathToRoute, publicViewToPath } from './routeMap'
import Header from './components/Header'
import Hero from './components/Hero'
import Footer from './components/Footer'

const Problem               = lazy(() => import('./components/Problem'))
const HowItWorks            = lazy(() => import('./components/HowItWorks'))
const WithoutWith           = lazy(() => import('./components/WithoutWith'))
const Coverage              = lazy(() => import('./components/Coverage'))
const SourceTransparencyMatrix = lazy(() => import('./components/SourceTransparencyMatrix'))
const SampleBrief           = lazy(() => import('./components/SampleBrief'))
const TrustLayer            = lazy(() => import('./components/TrustLayer'))
const Pricing               = lazy(() => import('./components/Pricing'))
const Contact               = lazy(() => import('./components/Contact'))
const EvidenceCard          = lazy(() => import('./components/EvidenceCard'))
const SourceCoverageTable   = lazy(() => import('./components/SourceCoverageTable'))
const VendorTrustSection    = lazy(() => import('./components/VendorTrustSection'))
const LoginPage             = lazy(() => import('./components/auth/LoginPage'))
const RegisterPage          = lazy(() => import('./components/auth/RegisterPage'))
const ForgotPasswordPage    = lazy(() => import('./components/auth/ForgotPasswordPage'))
const ResetPasswordPage     = lazy(() => import('./components/auth/ResetPasswordPage'))
const OnboardingPage        = lazy(() => import('./components/app/OnboardingPage'))
const ChoosePlanPage        = lazy(() => import('./components/app/ChoosePlanPage'))
const AppShell              = lazy(() => import('./components/app/AppShell'))
const SourceReadinessReviewPage = lazy(() => import('./components/SourceReadinessReviewPage'))
const PricingPage           = lazy(() => import('./components/PricingPage'))
const LegalPage             = lazy(() => import('./components/LegalPage'))
const VerifyPage            = lazy(() => import('./components/VerifyPage'))
const RoomPage              = lazy(() => import('./components/RoomPage'))

function GlobalLoader() {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-[#07111F]">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--accent)]" />
    </div>
  )
}

// REAL sealed record — the exact VARA capture shipped at
// /sample-record/record.json, the same artifact /verify#sample loads and
// re-hashes. A MODERN self-sealed record (content-sha256-v1): record_hash,
// raw_hash and sealed capture metadata all verify — no skipped hash checks.
// Every field below is pinned to that asset by
// src/test/realRecordLanding.test.js. Nothing here is invented.
const REAL_RECORD = {
  source_id: 'AE-vara-compliance-risk-rulebook-html',
  regulator: 'VARA',
  jurisdiction: 'UAE — Virtual Assets Regulatory Authority',
  run_at: '2026-07-17T13:02:36.641964+00:00',
  change_status: 'FIRST_SEEN',
  extraction_quality: 'GOOD',
  normalized_chars: 93826,
  normalized_hash: 'sha256:ca42ff6e740d77c8e9da433fb5a5a6285767077ae688d4397e903f622edc2a2d',
  proof_chain: { chain_verified: true, captured_at: '2026-07-17T13:02:36.641964+00:00' },
  source_url: 'https://rulebooks.vara.ae/rulebook/compliance-and-risk-management-rulebook',
};

function syncProfileToLocalStorage(profileData) {
  const industries = Array.isArray(profileData?.industries) ? profileData.industries : []
  const cached = {
    company: profileData?.company_name || '',
    email: '',
    industry: industries[0] || '',
    industries,
    markets: Array.isArray(profileData?.markets) ? profileData.markets : [],
    customSources: Array.isArray(profileData?.custom_sources) ? profileData.custom_sources : [],
    topics: Array.isArray(profileData?.topics) ? profileData.topics : [],
    alertThreshold: profileData?.alert_threshold || 'MEDIUM',
    briefLanguage: profileData?.brief_language || 'en',
    weeklyBriefEnabled: Boolean(profileData?.weekly_brief_enabled),
    aiEnabled: Boolean(profileData?.ai_enabled),
    telegramAlertsEnabled: Boolean(profileData?.telegram_alerts_enabled),
    emailAlertsEnabled: Boolean(profileData?.email_alerts_enabled),
  }
  localStorage.setItem('regradar_workspace_profile', JSON.stringify(cached))
  if (profileData?.onboarding_completed) {
    localStorage.setItem('regradar_onboarding_complete', 'true')
  } else {
    localStorage.removeItem('regradar_onboarding_complete')
  }
}

function dashboardViewForProfile(profileData) {
  return profileData?.onboarding_completed ? 'app' : 'onboarding'
}

const initialRoute = pathToRoute(
  typeof window !== 'undefined' ? window.location.pathname : '/',
)

// Per-route document titles. Default (landing + everything unlisted) stays in
// sync with the <title> in index.html.
const DEFAULT_TITLE = 'StatuteProof — Official-source regulatory intelligence for UAE financial firms'
const ROUTE_TITLES = {
  verify: 'Verify a record — StatuteProof',
  pricing: 'Pricing — StatuteProof',
  'source-readiness-review': 'Source readiness review — StatuteProof',
}

const AUTH_REQUIRED_VIEWS = new Set(['app', 'choose-plan'])

export default function App() {
  const [view, setView] = useState(initialRoute.view)
  const [appPage, setAppPage] = useState(initialRoute.appPage)
  const [currentUser, setCurrentUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [planState, setPlanState] = useState(null)

  useEffect(() => {
    document.title = ROUTE_TITLES[view] || DEFAULT_TITLE
  }, [view])

  function updatePath(path, replace = false) {
    if (typeof window === 'undefined') return
    const current = `${window.location.pathname}${window.location.search}`
    if (current === path) return
    window.history[replace ? 'replaceState' : 'pushState']({}, '', path)
  }

  function navigatePublic(nextView, options = {}) {
    const { replace = false, query = '' } = options
    setView(nextView)
    if (nextView !== 'app') setAppPage('dashboard')
    updatePath(`${publicViewToPath(nextView)}${query}`, replace)
  }

  function navigateRegister(planId) {
    const query = planId ? `?plan=${encodeURIComponent(planId)}` : ''
    navigatePublic('register', { query })
  }

  function navigateAppPage(nextPage, options = {}) {
    setAppPage(nextPage)
    setView('app')
    updatePath(appPageToPath(nextPage), options.replace)
  }

  useEffect(() => {
    function handlePopState() {
      const route = pathToRoute(window.location.pathname)
      setAppPage(route.appPage)
      if (!currentUser && (route.view === 'app' || route.view === 'choose-plan')) {
        setView('login')
        return
      }
      setView(route.view)
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [currentUser])

  useEffect(() => {
    function handleExpired() {
      localStorage.removeItem('regradar_user_registered')
      localStorage.removeItem('regradar_onboarding_complete')
      localStorage.removeItem('regradar_workspace_profile')
      const route = pathToRoute(window.location.pathname)
      setCurrentUser(null)
      if (route.view === 'app' || route.view === 'choose-plan') {
        setAppPage(route.appPage || 'dashboard')
        setView('login')
        updatePath('/login', true)
        return
      }
      if (['landing', 'login', 'register', 'pricing', 'source-readiness-review', 'verify', 'room', 'terms', 'privacy', 'disclaimer'].includes(route.view)) {
        setView(route.view)
        return
      }
      setView('landing')
      setAppPage('dashboard')
      updatePath('/', true)
    }
    window.addEventListener('auth:expired', handleExpired)
    return () => window.removeEventListener('auth:expired', handleExpired)
  }, [])

  useEffect(() => {
    let active = true

    async function bootstrapAuth() {
      const route = pathToRoute(window.location.pathname)
      setAppPage(route.appPage)
      if (!AUTH_REQUIRED_VIEWS.has(route.view)) {
        if (!active) return
        setCurrentUser(null)
        setView(route.view)
        setAuthLoading(false)
        return
      }
      try {
        const authData = await auth.me()
        let profileData = null
        try {
          const profileResponse = await profile.get()
          profileData = profileResponse.profile
          syncProfileToLocalStorage(profileData)
        } catch (err) {
          if (err.message === 'Unauthenticated.') throw err
          profileData = { onboarding_completed: false }
        }
        if (!active) return
        setCurrentUser(authData.user)
        loadPlan()
        if (route.view === 'app') {
          setView(dashboardViewForProfile(profileData))
          return
        }
        if (route.view === 'choose-plan') {
          setView('choose-plan')
          return
        }
        if (route.view === 'login' || route.view === 'register') {
          setView(dashboardViewForProfile(profileData))
          updatePath('/app/dashboard', true)
          return
        }
        if (['landing', 'pricing', 'source-readiness-review', 'verify', 'room', 'terms', 'privacy', 'disclaimer'].includes(route.view)) {
          setView(route.view)
          return
        }
        setView(dashboardViewForProfile(profileData))
      } catch {
        if (!active) return
        setCurrentUser(null)
        if (route.view === 'app' || route.view === 'choose-plan') {
          setView('login')
          updatePath('/login', true)
        } else {
          setView(route.view)
        }
      } finally {
        if (active) setAuthLoading(false)
      }
    }

    bootstrapAuth()
    return () => { active = false }
  }, [])

  async function loadPlan() {
    try {
      const data = await planApi.get()
      if (data.ok && data.plan) setPlanState(data.plan)
    } catch {
      // Silent fallback
    }
  }

  async function handleAuthenticated(user) {
    setCurrentUser(user)
    try {
      const data = await profile.get()
      syncProfileToLocalStorage(data.profile)
      loadPlan()
      if (dashboardViewForProfile(data.profile) === 'app') {
        navigateAppPage(appPage || 'dashboard', { replace: true })
      } else {
        setView('onboarding')
        updatePath('/app/dashboard', true)
      }
    } catch {
      setView('onboarding')
      updatePath('/app/dashboard', true)
    }
  }

  async function handleSignOut() {
    try {
      await auth.logout()
    } catch {
      // Local state is cleared even if the API server is temporarily unavailable.
    }
    localStorage.removeItem('regradar_user_registered')
    localStorage.removeItem('regradar_onboarding_complete')
    localStorage.removeItem('regradar_workspace_profile')
    setCurrentUser(null)
    navigatePublic('landing', { replace: true })
  }

  function handleViewSampleEvidence() {
    updatePath('/#evidence')
    document.getElementById('evidence')?.scrollIntoView({ behavior: 'smooth' })
  }

  if (authLoading) {
    return <div className="min-h-dvh bg-[#07111F]" />
  }

  if (view === 'login') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <LoginPage
          onLogin={handleAuthenticated}
          onRegister={() => navigateRegister()}
          onForgotPassword={() => navigatePublic('forgot-password')}
        />
      </Suspense>
    )
  }

  if (view === 'forgot-password') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <ForgotPasswordPage onBack={() => navigatePublic('login')} />
      </Suspense>
    )
  }

  if (view === 'reset-password') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <ResetPasswordPage onDone={() => navigatePublic('login')} />
      </Suspense>
    )
  }

  if (view === 'register') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <RegisterPage
          onRegister={handleAuthenticated}
          onLogin={() => navigatePublic('login')}
        />
      </Suspense>
    )
  }

  if (view === 'onboarding') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <OnboardingPage navigate={() => navigatePublic('choose-plan')} currentUser={currentUser} />
      </Suspense>
    )
  }

  if (view === 'choose-plan') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <ChoosePlanPage
          onContinue={() => navigateAppPage('dashboard')}
          selectPlan={async (planName) => {
            const data = await planApi.set(planName)
            if (data.ok && data.plan) setPlanState(data.plan)
            return data
          }}
        />
      </Suspense>
    )
  }

  if (view === 'app') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <AppShell
          key={appPage}
          initialPage={appPage}
          currentUser={currentUser}
          onSignOut={handleSignOut}
          planState={planState}
          onChoosePlan={() => navigatePublic('choose-plan')}
        />
      </Suspense>
    )
  }

  if (view === 'pricing') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <PricingPage
          onBack={() => navigatePublic('landing')}
          onCreateWorkspace={() => navigateRegister()}
          onSourceReview={() => navigatePublic('source-readiness-review')}
          onSelectPlan={navigateRegister}
        />
      </Suspense>
    )
  }

  if (view === 'source-readiness-review') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <SourceReadinessReviewPage onBack={() => navigatePublic('landing')} />
      </Suspense>
    )
  }

  if (view === 'verify') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <VerifyPage onBack={() => navigatePublic('landing')} />
      </Suspense>
    )
  }

  if (view === 'room') {
    // Public examiner-facing Auditor Evidence Room; the page reads its token
    // from the /room/<token> path itself.
    return (
      <Suspense fallback={<GlobalLoader />}>
        <RoomPage />
      </Suspense>
    )
  }

  if (view === 'terms' || view === 'privacy' || view === 'disclaimer') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <LegalPage type={view} onBack={() => navigatePublic('landing')} />
      </Suspense>
    )
  }

  return (
    <div className="min-h-dvh bg-[#07111F] text-slate-200">
      <Header
        onSignIn={() => navigatePublic('login')}
        onCreateWorkspace={() => navigateRegister()}
        onSourceReview={() => navigatePublic('source-readiness-review')}
        onPricing={() => navigatePublic('pricing')}
      />
      <main>
        <Hero
          onCreateWorkspace={() => navigatePublic('source-readiness-review')}
          onViewSample={handleViewSampleEvidence}
          onVerify={() => navigatePublic('verify', { query: '#sample' })}
        />
        <Suspense fallback={<div className="py-20" />}>
          {/* Evidence Section — a REAL sealed record (same asset /verify#sample loads) */}
          <section className="py-16 px-4 bg-[#07111F]" id="evidence">
            <div className="max-w-5xl mx-auto">
              <div className="text-center mb-10">
                <p className="text-xs font-semibold text-cyan-300 uppercase tracking-wider mb-2 bg-cyan-400/10 border border-cyan-300/20 inline-block px-3 py-1 rounded-full">
                  Real record — public regulator content
                </p>
                <h2 className="text-2xl font-bold text-white mt-4 mb-3">
                  This is a real sealed record. Check the math yourself.
                </h2>
                <p className="text-slate-400 max-w-xl mx-auto text-sm">
                  The full VARA Compliance &amp; Risk Management Rulebook
                  (including the AML/CFT part), captured from the official
                  rulebook site and sealed under SHA-256 with a self-sealing
                  record hash. Sealed records are chained, and the chain head
                  is anchored with a third-party RFC 3161 timestamp. The
                  verifier re-hashes the exact bytes you load — no account, no
                  trust in us required. Verification confirms record integrity
                  only; not legal advice.
                </p>
              </div>
              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <EvidenceCard record={REAL_RECORD} />
                <SourceCoverageTable />
              </div>
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => navigatePublic('verify', { query: '#sample' })}
                  className="sp-btn-primary justify-center px-6"
                >
                  Verify these hashes yourself — 60 seconds, no account
                </button>
              </div>
            </div>
          </section>
          <Problem />
          <HowItWorks />
          <WithoutWith />
          <SampleBrief />
          <Coverage onCreateWorkspace={() => navigatePublic('source-readiness-review')} />
          <SourceTransparencyMatrix onCreateWorkspace={() => navigateRegister()} />
          <VendorTrustSection />
          <TrustLayer onVerify={() => navigatePublic('verify', { query: '#sample' })} />

          <Pricing
            onCreateWorkspace={() => navigateRegister()}
            onSourceReview={() => navigatePublic('source-readiness-review')}
            onSelectPlan={navigateRegister}
          />
          <Contact
            onCreateWorkspace={() => navigateRegister()}
            onSignIn={() => navigatePublic('login')}
          />
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}
