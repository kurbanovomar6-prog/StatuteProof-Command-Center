import { useEffect, useState, lazy, Suspense } from 'react'
import { auth, profile, plan as planApi } from './api'
import Header from './components/Header'
import Hero from './components/Hero'
import Footer from './components/Footer'

const Problem               = lazy(() => import('./components/Problem'))
const WithoutWith           = lazy(() => import('./components/WithoutWith'))
const DashboardPreview      = lazy(() => import('./components/DashboardPreview'))
const Coverage              = lazy(() => import('./components/Coverage'))
const SourceTransparencyMatrix = lazy(() => import('./components/SourceTransparencyMatrix'))
const BuyerSourcePacks      = lazy(() => import('./components/BuyerSourcePacks'))
const ConfiguredMonitoring  = lazy(() => import('./components/ConfiguredMonitoring'))
const SampleBrief           = lazy(() => import('./components/SampleBrief'))
const TrustLayer            = lazy(() => import('./components/TrustLayer'))
const Pricing               = lazy(() => import('./components/Pricing'))
const Contact               = lazy(() => import('./components/Contact'))
const EvidenceCard          = lazy(() => import('./components/EvidenceCard'))
const SourceCoverageTable   = lazy(() => import('./components/SourceCoverageTable'))
const DiffViewer            = lazy(() => import('./components/DiffViewer'))
const LoginPage             = lazy(() => import('./components/auth/LoginPage'))
const RegisterPage          = lazy(() => import('./components/auth/RegisterPage'))
const OnboardingPage        = lazy(() => import('./components/app/OnboardingPage'))
const ChoosePlanPage        = lazy(() => import('./components/app/ChoosePlanPage'))
const AppShell              = lazy(() => import('./components/app/AppShell'))
const SourceReadinessReviewPage = lazy(() => import('./components/SourceReadinessReviewPage'))
const PricingPage           = lazy(() => import('./components/PricingPage'))

function GlobalLoader() {
  return (
    <div className="flex items-center justify-center h-screen bg-[#07111F]">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#16D9F5]" />
    </div>
  )
}

const SAMPLE_RECORD = {
  _label: 'SAMPLE / FAKE',
  source_id: 'AE-central-bank-of-the-uae',
  regulator: 'CBUAE',
  jurisdiction: 'UAE',
  run_at: '2026-05-30T11:56:00Z',
  change_status: 'CHANGED',
  extraction_quality: 'GOOD',
  normalized_chars: 43717,
  normalized_hash: 'sha256:94d020105d4d...',
  diff_excerpt: '[SAMPLE] Content change detected in CBUAE official source. Nature of change requires human review before any compliance action.',
  proof_chain: { chain_verified: false },
};

const SAMPLE_DIFF = `- [previous content snapshot — 2026-05-29]\n+ [updated content snapshot — 2026-05-30]\n  [SAMPLE content — not a real regulatory change]\n  Human review required before any compliance action.`;

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

export default function App() {
  const [view, setView] = useState('landing')
  const [currentUser, setCurrentUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [planState, setPlanState] = useState(null)

  useEffect(() => {
    function handleExpired() {
      localStorage.removeItem('regradar_user_registered')
      localStorage.removeItem('regradar_onboarding_complete')
      localStorage.removeItem('regradar_workspace_profile')
      setCurrentUser(null)
      setView('landing')
    }
    window.addEventListener('auth:expired', handleExpired)
    return () => window.removeEventListener('auth:expired', handleExpired)
  }, [])

  useEffect(() => {
    let active = true

    async function bootstrapAuth() {
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
        setView(dashboardViewForProfile(profileData))
      } catch {
        if (!active) return
        setCurrentUser(null)
        setView('landing')
      } finally {
        if (active) setAuthLoading(false)
      }
    }

    bootstrapAuth()
    return () => { active = false }
  }, [])

  async function goToDashboard() {
    if (currentUser) {
      try {
        const data = await profile.get()
        syncProfileToLocalStorage(data.profile)
        setView(dashboardViewForProfile(data.profile))
      } catch {
        setView('onboarding')
      }
      return
    }
    try {
      const data = await auth.me()
      setCurrentUser(data.user)
      const profileResponse = await profile.get()
      syncProfileToLocalStorage(profileResponse.profile)
      setView(dashboardViewForProfile(profileResponse.profile))
    } catch {
      setView('login')
    }
  }

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
      setView(dashboardViewForProfile(data.profile))
    } catch {
      setView('onboarding')
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
    setView('landing')
  }

  if (authLoading) {
    return <div className="min-h-screen bg-[#07111F]" />
  }

  if (view === 'login') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <LoginPage
          onLogin={handleAuthenticated}
          onRegister={() => setView('register')}
        />
      </Suspense>
    )
  }

  if (view === 'register') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <RegisterPage
          onRegister={handleAuthenticated}
          onLogin={() => setView('login')}
        />
      </Suspense>
    )
  }

  if (view === 'onboarding') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <OnboardingPage navigate={() => setView('choose-plan')} currentUser={currentUser} />
      </Suspense>
    )
  }

  if (view === 'choose-plan') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <ChoosePlanPage
          onContinue={() => setView('app')}
          selectPlan={async (planName) => {
            try {
              const data = await planApi.set(planName)
              if (data.ok && data.plan) setPlanState(data.plan)
              return data
            } catch (err) {
              throw err
            }
          }}
        />
      </Suspense>
    )
  }

  if (view === 'app') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <AppShell
          currentUser={currentUser}
          onSignOut={handleSignOut}
          planState={planState}
          onChoosePlan={() => setView('choose-plan')}
        />
      </Suspense>
    )
  }

  if (view === 'pricing') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <PricingPage onBack={() => setView('landing')} onCreateWorkspace={() => setView('register')} />
      </Suspense>
    )
  }

  if (view === 'source-readiness-review') {
    return (
      <Suspense fallback={<GlobalLoader />}>
        <SourceReadinessReviewPage onBack={() => setView('landing')} />
      </Suspense>
    )
  }

  return (
    <div className="min-h-screen bg-[#07111F] text-slate-200">
      <Header
        onSignIn={() => setView('login')}
        onCreateWorkspace={() => setView('register')}
        onSourceReview={() => setView('source-readiness-review')}
        onPricing={() => setView('pricing')}
      />
      <main>
        <Hero
          onCreateWorkspace={() => setView('source-readiness-review')}
          onSignIn={() => setView('register')}
        />
        <Suspense fallback={<div className="py-20" />}>
          <Problem />
          <WithoutWith />
          <SampleBrief />
          <Coverage onCreateWorkspace={() => setView('register')} />
          <SourceTransparencyMatrix onCreateWorkspace={() => setView('register')} />
          <BuyerSourcePacks onCreateWorkspace={() => setView('register')} />
          <ConfiguredMonitoring />
          <TrustLayer />
          {/* Evidence Demo Section — SAMPLE / FAKE */}
          <section className="py-16 px-4 bg-[#07111F]" id="evidence">
            <div className="max-w-5xl mx-auto">
              <div className="text-center mb-10">
                <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2 bg-amber-400/10 border border-amber-400/20 inline-block px-3 py-1 rounded-full">SAMPLE / FAKE — demonstration only</p>
                <h2 className="text-2xl font-bold text-white mt-4 mb-3">Evidence-backed monitoring</h2>
                <p className="text-slate-400 max-w-xl mx-auto text-sm">
                  Detected changes are cryptographically hashed, timestamped, and stored for human review.
                  Not legal advice. For monitoring information only.
                </p>
              </div>
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <EvidenceCard record={SAMPLE_RECORD} />
                <SourceCoverageTable />
              </div>
              <DiffViewer
                diffText={SAMPLE_DIFF}
                sourceId="AE-cbuae-homepage"
                detectedAt="2026-05-30"
              />
            </div>
          </section>
          <DashboardPreview />
          <Pricing onCreateWorkspace={() => setView('register')} />
          <Contact
            onCreateWorkspace={() => setView('register')}
            onSignIn={() => setView('login')}
          />
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}
