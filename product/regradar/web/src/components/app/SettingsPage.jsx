import { useState } from 'react'
import { ShieldCheck, AlertTriangle, Download, Loader2 } from 'lucide-react'
import { account as accountApi, profile as profileApi } from '../../api'
import TeamPanel from './TeamPanel'

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
  'UAE Capital Market Authority (UAE CMA) [Limited]',
  'Other',
]

// A switch, announced as one. This was a bare <button> whose only child was an
// empty <span>: no name, no state, no type. Five of them on this page, and axe
// rates each one critical — someone using a screen reader had five unlabelled
// buttons and no way to know what any of them controlled or whether it was on.
// The jsdom suite could not see it; the browser run did.
function Toggle({ checked, onChange, label, disabled = false }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative w-9 h-5 rounded-full transition-colors disabled:opacity-70 ${checked ? 'bg-[var(--accent)]' : 'bg-[var(--bg-tooltip)]'}`}
    >
      <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-4' : ''}`} />
    </button>
  )
}

function Section({ title, children }) {
  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5">
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
                ? 'bg-[var(--trust-badge)] border-[var(--trust-border)] text-[var(--accent)]'
                : 'bg-[var(--bg-elevated)] border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border)] hover:text-white'
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

  const [mediumAlerts,  setMediumAlerts]  = useState(thresholds.medium)
  const [lowAlerts,     setLowAlerts]     = useState(thresholds.low)
  const [tgEnabled,     setTgEnabled]     = useState(Boolean(profile.telegramAlertsEnabled))
  // Round-tripped from the saved profile unchanged — no UI control edits
  // this value yet (tracked in DEFECT_LOG D3 note).
  const [emailEnabled]  = useState(Boolean(profile.emailAlertsEnabled))
  const [aiEnabled,     setAiEnabled]     = useState(profile.aiEnabled !== false)
  const [language,      setLanguage]      = useState(languageLabel(profile.briefLanguage))
  const [saved,         setSaved]         = useState(false)
  const [saving,        setSaving]        = useState(false)
  const [saveError,     setSaveError]     = useState('')
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [exporting,     setExporting]     = useState(false)
  const [exportError,   setExportError]   = useState('')
  const [exportMessage, setExportMessage] = useState('')

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

  async function handleExportData() {
    setExporting(true)
    setExportError('')
    setExportMessage('')
    try {
      const { blob, filename } = await accountApi.exportData()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      const kb = (blob.size / 1024).toFixed(1)
      setExportMessage(`Export downloaded — ${filename} (${kb} KB)`)
    } catch (err) {
      setExportError(err.message || 'Could not export your account data.')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="p-5 space-y-4 max-w-2xl">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-white mb-1">Settings</h1>
        <p className="text-sm text-[var(--text-secondary)]">Manage your account-owned workspace profile and notification preferences.</p>
      </div>

      {/* Workspace */}
      <Section title="Workspace">
        <div className="space-y-3 text-xs">
          <div>
            <label htmlFor="settings-workspace-name" className="block text-[var(--text-secondary)] mb-1.5">Workspace name</label>
            <input
              id="settings-workspace-name"
              type="text"
              value={workspace}
              onChange={e => setWorkspace(e.target.value)}
              className="w-full bg-[var(--bg-raised)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--trust-border)]"
            />
          </div>
          <div className="flex justify-between items-center py-1">
            <span className="text-[var(--text-secondary)]">Plan</span>
            <span className="text-[var(--accent)] font-medium">{planLabel}</span>
          </div>
        </div>
      </Section>

      {/* Monitoring Profile */}
      <Section title="Monitoring Profile">
        <div className="space-y-5">
          <div>
            <p className="text-xs text-[var(--text-secondary)] mb-1.5">Target markets</p>
            <ChipSelect options={MARKETS} selected={markets} onToggle={toggleMarket} />
            {markets.length === 0 && (
              <p className="text-xs text-[var(--text-muted)] mt-1.5">No markets selected — dashboard will show setup previews until your profile is saved.</p>
            )}
          </div>
          <div>
            <p className="text-xs text-[var(--text-secondary)] mb-1.5">Industries</p>
            <ChipSelect options={INDUSTRIES} selected={industries} onToggle={toggleIndustry} />
          </div>
          <div>
            <p className="text-xs text-[var(--text-secondary)] mb-1.5">UAE source layers</p>
            <ChipSelect options={SOURCE_LAYERS} selected={topics} onToggle={toggleTopic} />
            {topics.length === 0 && (
              <p className="text-xs text-[var(--text-muted)] mt-1.5">No source layers selected — reviewed alert routing will rely on markets and industries only.</p>
            )}
          </div>
        </div>
      </Section>

      {/* Alert thresholds */}
      <Section title="Alert Thresholds">
        <div className="space-y-3">
          {/* HIGH-risk changes always alert — this floor is not user-configurable
              (mandatory review posture), so it is shown as a fixed fact, not a
              non-functional toggle. */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-[var(--text-primary)]">HIGH risk alerts</p>
              <p className="text-xs text-[var(--text-muted)]">Immediate review required</p>
            </div>
            <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300">
              Always on
            </span>
          </div>
          {[
            { label: 'MEDIUM risk alerts', sub: 'Review within 3 days',      checked: mediumAlerts, set: setMediumAlerts },
            { label: 'LOW risk alerts',    sub: 'Monitor only',              checked: lowAlerts,    set: setLowAlerts },
          ].map(({ label, sub, checked, set }) => (
            <div key={label} className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-primary)]">{label}</p>
                <p className="text-xs text-[var(--text-muted)]">{sub}</p>
              </div>
              <Toggle checked={checked} onChange={set} label={label} />
            </div>
          ))}
        </div>
      </Section>

      {/* AI brief settings */}
      <Section title="AI Brief Settings">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-[var(--text-primary)]">AI briefs enabled</p>
              <p className="text-xs text-[var(--text-muted)]">Prepare structured brief previews for reviewed pilot outputs</p>
            </div>
            <Toggle checked={aiEnabled} onChange={setAiEnabled} label="AI-assisted brief drafting" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-[var(--text-primary)]">Human review of high-risk changes</p>
              <p className="text-xs text-[var(--text-muted)]">High-risk / low-confidence changes are held for human review before delivery — this is mandatory and cannot be disabled.</p>
            </div>
            <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300">
              Always on
            </span>
          </div>
          <div>
            <label htmlFor="settings-brief-language" className="block text-xs text-[var(--text-secondary)] mb-1.5">Brief language</label>
            <select
              id="settings-brief-language"
              value={language}
              onChange={e => setLanguage(e.target.value)}
              className="w-full bg-[var(--bg-raised)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--trust-border)]"
            >
              <option>English</option>
              <option disabled>Arabic support planned</option>
            </select>
            <p className="text-xs text-[var(--text-muted)] mt-1">
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
              <p className="text-sm text-[var(--text-primary)]">Telegram alerts</p>
              <p className="text-xs text-[var(--text-muted)]">Telegram delivery requires connection in Integrations.</p>
            </div>
            <Toggle checked={tgEnabled} onChange={setTgEnabled} label="Telegram alerts" />
          </div>
          <div
            aria-disabled="true"
            className="flex items-center justify-between opacity-70 cursor-not-allowed"
            title="Email digest is not yet available in this pilot"
          >
            <div>
              <p className="text-sm text-[var(--text-primary)]">Email digest</p>
              <p className="text-xs text-[var(--text-muted)]">Not available in pilot — Telegram delivery is active</p>
            </div>
            <Toggle checked={false} onChange={() => {}} disabled label="Email alerts (not yet available)" />
          </div>
        </div>
      </Section>

      {/* Legal Acknowledgement */}
      <div className="bg-[var(--bg-elevated)] border border-[var(--trust-border)] rounded-xl p-5">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-4 h-4 text-[var(--accent)] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-white mb-2">Legal Acknowledgement</p>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-3">
              StatuteProof provides monitoring intelligence only and does not provide legal advice.
              Reports are generated from monitored official-source records and are provided for information
              and compliance review support only. They do not constitute legal advice, regulatory advice,
              compliance determination, or a legal opinion.
            </p>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or
              other professional advisers. Users should verify official source material directly and consult
              qualified professionals before making regulatory, filing, operational, or customer decisions.
            </p>
            <div className="mt-3 pt-3 border-t border-[var(--border-muted)]">
              <p className="text-[10px] text-[var(--text-muted)] leading-relaxed">
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
              : 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)]'
          } disabled:opacity-70`}
        >
          {saving ? 'Saving…' : saved ? 'Saved' : 'Save settings'}
        </button>
      </div>
      {saveError && (
        <div className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
          {saveError}
        </div>
      )}

      {/* Export my data — self-service exit portability */}
      <div className="sp-card mt-4">
        <div className="flex items-start gap-3">
          <Download className="w-4 h-4 text-[var(--accent)] flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-semibold text-white mb-1">Export my data</p>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-2">
              Download everything your account owns as one JSON file: account profile,
              workspace monitoring profile, notification preferences, your review
              checklist items, your organisation&rsquo;s sealed decision records, and
              your Telegram link.
            </p>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-3">
              Sealed decision records remain independently verifiable without
              StatuteProof — each carries its own SHA-256 record hash and can be
              checked with the public verifier or standard tools. For monitoring
              information only. Not legal advice and not a guarantee of compliance.
            </p>
            <button
              type="button"
              onClick={handleExportData}
              disabled={exporting}
              className="inline-flex items-center gap-2 text-xs font-medium text-[var(--accent)] border border-[var(--trust-border)] hover:border-[var(--trust-border)] px-3 py-2 rounded-lg transition-colors disabled:opacity-70"
            >
              {exporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
              {exporting ? 'Preparing export…' : 'Download my data (JSON)'}
            </button>
            {exportMessage && (
              <p className="mt-2 text-xs text-emerald-300">{exportMessage}</p>
            )}
            {exportError && (
              <p className="mt-2 text-xs text-rose-300">{exportError}</p>
            )}
          </div>
        </div>
      </div>

      {/* Reset workspace */}
      <div className="mt-4">
        <TeamPanel />
      </div>

      <div className="bg-[var(--bg-elevated)] border border-rose-500/20 rounded-xl p-5 mt-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-semibold text-rose-400 mb-1">Reset workspace</p>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-3">
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
                  className="text-xs font-medium px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-white transition-colors"
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
