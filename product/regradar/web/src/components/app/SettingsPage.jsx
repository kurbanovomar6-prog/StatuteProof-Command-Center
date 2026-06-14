import { useState } from 'react'
import { ShieldCheck, AlertTriangle } from 'lucide-react'
import { profile as profileApi } from '../../api'

const MARKETS    = ['UAE', 'DIFC', 'ADGM', 'Other UAE source']
const INDUSTRIES = ['Fintech', 'Payments', 'Crypto / VASP', 'Banking', 'Legal & Compliance', 'Tax / Reporting', 'Consulting', 'Other']
const SOURCE_LAYERS = [
  'CBUAE',
  'VARA',
  'DFSA',
  'ADGM / FSRA',
  'UAE FIU',
  'Ministry of Finance',
  'UAE Legislation Portal',
  'DIFC Laws',
  'Ministry of Economy',
  'FTA',
  'Capital Market Authority / former SCA [Limited]',
  'Other',
]

function Toggle({ checked, onChange }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`relative w-9 h-5 rounded-full transition-colors ${checked ? 'bg-cyan-500' : 'bg-slate-700'}`}
    >
      <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-4' : ''}`} />
    </button>
  )
}

function Section({ title, children }) {
  return (
    <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5">
      <h2 className="text-sm font-semibold text-white mb-4">{title}</h2>
      {children}
    </div>
  )
}

function ChipSelect({ options, selected, onToggle, error }) {
  return (
    <>
      <div className="flex flex-wrap gap-2 mt-1">
        {options.map(o => (
          <button
            key={o}
            type="button"
            onClick={() => onToggle(o)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              selected.includes(o)
                ? 'bg-[#16D9F5]/10 border-[#16D9F5]/50 text-[#16D9F5]'
                : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white'
            }`}
          >
            {o}
          </button>
        ))}
      </div>
      {error && <p className="text-rose-400 text-xs mt-1">{error}</p>}
    </>
  )
}

function loadProfile() {
  try {
    return JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
  } catch {
    return {}
  }
}

function thresholdToggles(threshold) {
  const value = String(threshold || 'MEDIUM').toUpperCase()
  return {
    high: true,
    medium: value === 'LOW' || value === 'MEDIUM',
    low: value === 'LOW',
  }
}

function languageLabel() {
  return 'English'
}

function languageCode() {
  return 'en'
}

function thresholdFromToggles({ mediumAlerts, lowAlerts }) {
  if (lowAlerts) return 'LOW'
  if (mediumAlerts) return 'MEDIUM'
  return 'HIGH'
}

function displayPlanName(planState) {
  if (planState?.plan_name === 'evidence_preview') return 'Source Readiness Review'
  return planState?.plan_display || 'Source Readiness Review'
}

export default function SettingsPage({ onResetWorkspace, planState }) {
  const profile = loadProfile()
  const thresholds = thresholdToggles(profile.alertThreshold)
  const planLabel = displayPlanName(planState)

  const [workspace,  setWorkspace]  = useState(profile.company || 'Profile workspace')
  const [markets,    setMarkets]    = useState(Array.isArray(profile.markets)    ? profile.markets    : [])
  const [industries, setIndustries] = useState(Array.isArray(profile.industries) ? profile.industries : [])
  const [topics,     setTopics]     = useState(Array.isArray(profile.topics)     ? profile.topics     : [])

  const [highAlerts,    setHighAlerts]    = useState(thresholds.high)
  const [mediumAlerts,  setMediumAlerts]  = useState(thresholds.medium)
  const [lowAlerts,     setLowAlerts]     = useState(thresholds.low)
  const [tgEnabled,     setTgEnabled]     = useState(Boolean(profile.telegramAlertsEnabled))
  const [emailEnabled,  setEmailEnabled]  = useState(Boolean(profile.emailAlertsEnabled))
  const [aiEnabled,     setAiEnabled]     = useState(profile.aiEnabled !== false)
  const [reviewFlag,    setReviewFlag]    = useState(true)
  const [language,      setLanguage]      = useState(languageLabel(profile.briefLanguage))
  const [saved,         setSaved]         = useState(false)
  const [saving,        setSaving]        = useState(false)
  const [saveError,     setSaveError]     = useState('')
  const [showResetConfirm, setShowResetConfirm] = useState(false)

  function toggleMarket(m) {
    setMarkets(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])
  }

  function toggleIndustry(i) {
    setIndustries(prev => prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i])
  }

  function toggleTopic(t) {
    setTopics(prev => prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t])
  }

  async function handleSave() {
    setSaving(true)
    setSaveError('')
    try {
      const response = await profileApi.update({
        company_name: workspace,
        markets,
        industries,
        topics,
        alert_threshold: thresholdFromToggles({ mediumAlerts, lowAlerts }),
        brief_language: languageCode(language),
        weekly_brief_enabled: true,
        ai_enabled: aiEnabled,
        telegram_alerts_enabled: tgEnabled,
        email_alerts_enabled: emailEnabled,
      })
      const p = response.profile
      localStorage.setItem('regradar_workspace_profile', JSON.stringify({
        ...profile,
        company: p.company_name || '',
        email: '',
        industry: p.industries?.[0] || '',
        industries: p.industries || [],
        markets: p.markets || [],
        topics: p.topics || [],
        customSources: p.custom_sources || [],
        alertThreshold: p.alert_threshold || 'MEDIUM',
        briefLanguage: p.brief_language || 'en',
        weeklyBriefEnabled: Boolean(p.weekly_brief_enabled),
        aiEnabled: Boolean(p.ai_enabled),
        telegramAlertsEnabled: Boolean(p.telegram_alerts_enabled),
        emailAlertsEnabled: Boolean(p.email_alerts_enabled),
      }))
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setSaveError(err.message || 'Could not save settings.')
    } finally {
      setSaving(false)
    }
  }

  function handleReset() {
    localStorage.removeItem('regradar_user_registered')
    localStorage.removeItem('regradar_onboarding_complete')
    localStorage.removeItem('regradar_workspace_profile')
    if (onResetWorkspace) onResetWorkspace()
  }

  return (
    <div className="p-5 space-y-4 max-w-2xl">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-white mb-1">Settings</h1>
        <p className="text-sm text-slate-400">Manage your account-owned workspace profile and notification preferences.</p>
      </div>

      {/* Workspace */}
      <Section title="Workspace">
        <div className="space-y-3 text-xs">
          <div>
            <label className="block text-slate-400 mb-1.5">Workspace name</label>
            <input
              type="text"
              value={workspace}
              onChange={e => setWorkspace(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div className="flex justify-between items-center py-1">
            <span className="text-slate-400">Plan</span>
            <span className="text-cyan-400 font-medium">{planLabel}</span>
          </div>
        </div>
      </Section>

      {/* Monitoring Profile */}
      <Section title="Monitoring Profile">
        <div className="space-y-5">
          <div>
            <p className="text-xs text-slate-400 mb-1.5">Target markets</p>
            <ChipSelect options={MARKETS} selected={markets} onToggle={toggleMarket} />
            {markets.length === 0 && (
              <p className="text-xs text-slate-600 mt-1.5">No markets selected — dashboard will show setup previews until your profile is saved.</p>
            )}
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1.5">Industries</p>
            <ChipSelect options={INDUSTRIES} selected={industries} onToggle={toggleIndustry} />
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1.5">UAE source layers</p>
            <ChipSelect options={SOURCE_LAYERS} selected={topics} onToggle={toggleTopic} />
            {topics.length === 0 && (
              <p className="text-xs text-slate-600 mt-1.5">No source layers selected — reviewed alert routing will rely on markets and industries only.</p>
            )}
          </div>
        </div>
      </Section>

      {/* Alert thresholds */}
      <Section title="Alert Thresholds">
        <div className="space-y-3">
          {[
            { label: 'HIGH risk alerts',   sub: 'Immediate review required', checked: highAlerts,   set: setHighAlerts },
            { label: 'MEDIUM risk alerts', sub: 'Review within 3 days',      checked: mediumAlerts, set: setMediumAlerts },
            { label: 'LOW risk alerts',    sub: 'Monitor only',              checked: lowAlerts,    set: setLowAlerts },
          ].map(({ label, sub, checked, set }) => (
            <div key={label} className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-200">{label}</p>
                <p className="text-xs text-slate-500">{sub}</p>
              </div>
              <Toggle checked={checked} onChange={set} />
            </div>
          ))}
        </div>
      </Section>

      {/* AI brief settings */}
      <Section title="AI Brief Settings">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">AI briefs enabled</p>
              <p className="text-xs text-slate-500">Prepare structured brief previews for reviewed pilot outputs</p>
            </div>
            <Toggle checked={aiEnabled} onChange={setAiEnabled} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">Human review flag</p>
              <p className="text-xs text-slate-500">Flag alerts that require human legal review</p>
            </div>
            <Toggle checked={reviewFlag} onChange={setReviewFlag} />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Brief language</label>
            <select
              value={language}
              onChange={e => setLanguage(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
            >
              <option>English</option>
              <option disabled>Arabic support planned</option>
            </select>
            <p className="text-xs text-slate-600 mt-1">
              English is the MVP brief language. Arabic support can be scoped during pilot setup.
            </p>
          </div>
        </div>
      </Section>

      {/* Notifications */}
      <Section title="Notification Preferences">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">Telegram alerts</p>
              <p className="text-xs text-slate-500">Telegram delivery requires connection in Integrations.</p>
            </div>
            <Toggle checked={tgEnabled} onChange={setTgEnabled} />
          </div>
          <div className="flex items-center justify-between opacity-50">
            <div>
              <p className="text-sm text-slate-200">Email digest</p>
              <p className="text-xs text-slate-500">Coming soon</p>
            </div>
            <Toggle checked={emailEnabled} onChange={setEmailEnabled} />
          </div>
        </div>
      </Section>

      {/* Legal Acknowledgement */}
      <div className="bg-[#0D1B2E] border border-cyan-400/20 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-4 h-4 text-[#16D9F5] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-white mb-2">Legal Acknowledgement</p>
            <p className="text-xs text-slate-400 leading-relaxed mb-3">
              StatuteProof provides monitoring intelligence only and does not provide legal advice.
              Reports are generated from monitored official-source records and are provided for information
              and compliance review support only. They do not constitute legal advice, regulatory advice,
              compliance determination, or a legal opinion.
            </p>
            <p className="text-xs text-slate-500 leading-relaxed">
              StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or
              other professional advisers. Users should verify official source material directly and consult
              qualified professionals before making regulatory, filing, operational, or customer decisions.
            </p>
            <div className="mt-3 pt-3 border-t border-slate-800">
              <p className="text-[10px] text-slate-600 leading-relaxed">
                Billing: manual activation terms. Advance notice will be given of any pricing changes.
                Contact the StatuteProof team to review your subscription or access level.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Save */}
      <div className="flex flex-col items-end gap-2">
        {saved && (
          <span className="inline-flex items-center rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
            Saved to your account
          </span>
        )}
        <button
          onClick={handleSave}
          disabled={saving}
          className={`text-sm font-semibold px-5 py-2 rounded-lg transition-colors ${
            saved
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
              : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950'
          } disabled:opacity-60`}
        >
          {saving ? 'Saving…' : saved ? 'Saved ✓' : 'Save settings'}
        </button>
      </div>
      {saveError && (
        <div className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
          {saveError}
        </div>
      )}

      {/* Reset workspace */}
      <div className="bg-[#0D1B2E] border border-rose-500/20 rounded-xl p-5 mt-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-semibold text-rose-400 mb-1">Reset workspace</p>
            <p className="text-xs text-slate-500 leading-relaxed mb-3">
              Clears all local workspace data including onboarding state. You will be signed out and returned to the landing page.
            </p>
            {showResetConfirm ? (
              <div className="flex gap-2">
                <button
                  onClick={handleReset}
                  className="text-xs font-semibold px-4 py-1.5 rounded-lg bg-rose-500 hover:bg-rose-400 text-white transition-colors"
                >
                  Confirm reset
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="text-xs font-medium px-4 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowResetConfirm(true)}
                className="text-xs font-medium px-4 py-1.5 rounded-lg border border-rose-500/30 text-rose-400 hover:border-rose-500/60 transition-colors"
              >
                Reset workspace
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
