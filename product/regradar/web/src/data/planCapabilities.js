// Plan definitions — no Stripe, no payment processing.
// Billing is manually activated for founding pilots.
// Prices: Monitor $349/mo | Professional $749/mo | Consultant custom
// Source count: 13 validated UAE sources total (honest count as of 2026-06)

export const PLAN_NAMES = {
  EVIDENCE_PREVIEW: 'evidence_preview',
  STARTER_PILOT: 'starter_pilot',   // DB id kept as starter_pilot for backward compat
  PROFESSIONAL: 'professional',
  CONSULTANT: 'consultant',
}

export const PLAN_DISPLAY = {
  evidence_preview: 'Evidence Preview',
  starter_pilot: 'Monitor',         // Display name updated from "Starter Pilot"
  professional: 'Professional',
  consultant: 'Compliance Consultant',
}

export const PLAN_PRICE = {
  evidence_preview: 'Free',
  starter_pilot: '$349',
  professional: '$749',
  consultant: 'Talk to us',
}

export const PLAN_PERIOD = {
  evidence_preview: '',
  starter_pilot: '/ month',
  professional: '/ month',
  consultant: '',
}

// Feature availability labels
// 'available' | 'requires_activation' | 'pilot_roadmap' | false
export const PLAN_FEATURE_STATUS = {
  auditExport: 'pilot_roadmap',
  pdfExport: 'requires_activation',
  emailBrief: 'requires_activation',
  customSources: 'requires_activation',   // professional only, needs onboarding
  whiteLabel: 'pilot_roadmap',
  multipleWorkspaces: 'pilot_roadmap',
}

export const PLAN_CAPABILITIES = {
  evidence_preview: {
    liveMonitoring: false,
    sourceLimit: 0,
    customSources: 0,
    weeklyBriefs: false,
    auditExport: false,
    pdfExport: false,
    users: 1,
    retentionDays: 0,
    multipleWorkspaces: false,
    whiteLabel: false,
    highRiskQueue: false,
    diffView: false,
  },
  starter_pilot: {
    liveMonitoring: true,
    sourceLimit: 5,
    customSources: 0,
    weeklyBriefs: 'status_only',   // source status summary, not full MLRO brief
    auditExport: false,
    pdfExport: false,
    users: 1,
    retentionDays: 90,
    multipleWorkspaces: false,
    whiteLabel: false,
    highRiskQueue: false,
    diffView: true,
  },
  professional: {
    liveMonitoring: true,
    sourceLimit: 13,               // honest count — 13 validated sources in sources.json
    customSources: 3,              // requires activation
    weeklyBriefs: true,            // Telegram; email requires_activation
    auditExport: false,            // pilot_roadmap — not yet built
    pdfExport: false,              // requires_activation
    users: 2,
    retentionDays: 365,
    multipleWorkspaces: false,
    whiteLabel: false,
    highRiskQueue: true,
    diffView: true,
  },
  consultant: {
    liveMonitoring: true,
    sourceLimit: 999,
    customSources: 999,
    weeklyBriefs: true,
    auditExport: false,            // pilot_roadmap
    pdfExport: false,              // pilot_roadmap
    users: 999,
    retentionDays: 999,
    multipleWorkspaces: false,     // pilot_roadmap
    whiteLabel: false,             // pilot_roadmap
    highRiskQueue: true,
    diffView: true,
  },
}

export const TRIAL_DAYS = 7

export function getPlanCaps(planName) {
  return PLAN_CAPABILITIES[planName] || PLAN_CAPABILITIES.evidence_preview
}

export function canDo(planName, capability) {
  const caps = getPlanCaps(planName)
  const val = caps[capability]
  if (val === 'status_only') return 'limited'
  if (val === 'limited') return 'limited'
  return Boolean(val)
}

export function featureLabel(featureKey) {
  return PLAN_FEATURE_STATUS[featureKey] || 'available'
}
