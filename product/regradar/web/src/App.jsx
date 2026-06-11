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
import LoginPage from './components/auth/LoginPage'
import RegisterPage from './components/auth/RegisterPage'
import OnboardingPage from './components/app/OnboardingPage'
import AppShell from './components/app/AppShell'

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

  return (
    <div className="min-h-screen bg-[#07111F] text-slate-200">
      <Header
        onSignIn={() => setView('login')}
        onCreateWorkspace={() => setView('register')}
      />
      <main>
        <Hero
          onCreateWorkspace={() => setView('register')}
          onSignIn={() => setView('login')}
        />
        <Problem />
        <WithoutWith />
        <SampleBrief />
        <Coverage onCreateWorkspace={() => setView('register')} />
        <SourceTransparencyMatrix onCreateWorkspace={() => setView('register')} />
        <BuyerSourcePacks onCreateWorkspace={() => setView('register')} />
        <ConfiguredMonitoring />
        <TrustLayer />
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
