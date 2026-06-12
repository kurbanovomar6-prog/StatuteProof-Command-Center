import { useEffect, useState } from 'react'
import { auth, profile } from './api'
import Header from './components/Header'
import Hero from './components/Hero'
import Problem from './components/Problem'
import WithoutWith from './components/WithoutWith'
import DashboardPreview from './components/DashboardPreview'
import Coverage from './components/Coverage'
import SourceTransparencyMatrix from './components/SourceTransparencyMatrix'
import BuyerSourcePacks from './components/BuyerSourcePacks'
import ConfiguredMonitoring from './components/ConfiguredMonitoring'
import SampleBrief from './components/SampleBrief'
import TrustLayer from './components/TrustLayer'
import Pricing from './components/Pricing'
import Contact from './components/Contact'
import Footer from './components/Footer'
import EvidenceCard from './components/EvidenceCard'
import SourceCoverageTable from './components/SourceCoverageTable'
import DiffViewer from './components/DiffViewer'
import LoginPage from './components/auth/LoginPage'
import RegisterPage from './components/auth/RegisterPage'
import OnboardingPage from './components/app/OnboardingPage'
import AppShell from './components/app/AppShell'
import SourceReadinessReviewPage from './components/SourceReadinessReviewPage'

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

  async function handleAuthenticated(user) {
    setCurrentUser(user)
    try {
      const data = await profile.get()
      syncProfileToLocalStorage(data.profile)
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
      <LoginPage
        onLogin={handleAuthenticated}
        onRegister={() => setView('register')}
      />
    )
  }

  if (view === 'register') {
    return (
      <RegisterPage
        onRegister={handleAuthenticated}
        onLogin={() => setView('login')}
      />
    )
  }

  if (view === 'onboarding') {
    return <OnboardingPage navigate={() => setView('app')} currentUser={currentUser} />
  }

  if (view === 'app') {
    return (
      <AppShell
        currentUser={currentUser}
        onSignOut={handleSignOut}
      />
    )
  }

  if (view === 'source-readiness-review') {
    return (
      <SourceReadinessReviewPage onBack={() => setView('landing')} />
    )
  }

  return (
    <div className="min-h-screen bg-[#07111F] text-slate-200">
      <Header
        onSignIn={() => setView('login')}
        onCreateWorkspace={() => setView('register')}
        onSourceReview={() => setView('source-readiness-review')}
      />
      <main>
        <Hero
          onCreateWorkspace={() => setView('source-readiness-review')}
          onSignIn={() => setView('register')}
        />
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
            {/* Spec sample evidence alert card */}
            <div className="max-w-xl mx-auto mb-8">
              <div className="bg-[#0D1B2E] border border-slate-700 rounded-xl p-5 text-sm space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded">SAMPLE — NOT REAL REGULATORY DATA</span>
                  <span className="text-xs font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/30 px-2 py-0.5 rounded-full">CHANGED</span>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-0.5">Source</p>
                  <p className="text-sm font-semibold text-white">VARA Regulatory Framework</p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div><p className="text-slate-500 mb-0.5">Regulator</p><p className="text-slate-200">VARA</p></div>
                  <div><p className="text-slate-500 mb-0.5">Detected</p><p className="text-slate-200">2026-06-10 09:14:22 UTC [SAMPLE]</p></div>
                  <div><p className="text-slate-500 mb-0.5">Risk</p><p className="text-red-400 font-bold">HIGH</p></div>
                  <div><p className="text-slate-500 mb-0.5">Affected</p><p className="text-slate-200">VASP / MLRO / Compliance teams</p></div>
                  <div className="col-span-2"><p className="text-slate-500 mb-0.5">Official URL</p><a href="https://www.vara.ae/en/regulatory-framework/" target="_blank" rel="noopener noreferrer" className="text-[#16D9F5] hover:underline break-all">https://www.vara.ae/en/regulatory-framework/</a></div>
                  <div><p className="text-slate-500 mb-0.5">Old hash</p><p className="text-slate-400 font-mono">a3f8d9c2...</p></div>
                  <div><p className="text-slate-500 mb-0.5">New hash</p><p className="text-slate-400 font-mono">7b1e4a8f...</p></div>
                  <div><p className="text-slate-500 mb-0.5">Diff</p><p className="text-emerald-400">Available</p></div>
                  <div><p className="text-slate-500 mb-0.5">Snapshot</p><p className="text-slate-300">Saved</p></div>
                </div>
                <div className="flex items-center justify-between pt-1 border-t border-slate-800">
                  <span className="text-amber-400 text-xs font-semibold">Human review: Required</span>
                  <span className="text-xs text-slate-600">Not legal advice</span>
                </div>
              </div>
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
      </main>
      <Footer />
    </div>
  )
}
