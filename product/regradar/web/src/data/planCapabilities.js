// Plan definitions — no Stripe, no payment processing.
// Billing is manually activated for founding pilots after source readiness review.
// Prices: Founding Pilot $199/mo | UAE Monitor $399/mo | Consultant custom
// Source count: 81 enabled UAE sources, 80 monitoring-active after proof/baseline gates

export const PLAN_NAMES = {
  EVIDENCE_PREVIEW: 'evidence_preview',
  STARTER_PILOT: 'starter_pilot',   // DB id kept as starter_pilot for backward compat
  PROFESSIONAL: 'professional',
  CONSULTANT: 'consultant',
}

export const PLAN_DISPLAY = {
  evidence_preview: 'Source Readiness Review',
  starter_pilot: 'Founding Pilot',
  professional: 'UAE Monitor',
  consultant: 'Compliance Consultant',
}

export const PLAN_PRICE = {
  evidence_preview: 'Free',
  starter_pilot: '$199',
  professional: '$399',
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
  auditExport: 'available',
  pdfExport: 'available',
  emailBrief: 'requires_activation',
  customSources: 'requires_activation',   // UAE Monitor only, needs onboarding
  whiteLabel: 'pilot_roadmap',
  multipleWorkspaces: 'pilot_roadmap',
  highRiskQueue: 'available',             // UAE Monitor+
  weeklyBrief: 'available',               // Telegram; email requires_activation
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
    sourceLimit: 3,            // 3 official UAE sources — manually curated per workspace
    customSources: 0,
    weeklyBriefs: 'status_only',  // source status summary; not full MLRO brief
    auditExport: false,
    pdfExport: false,
    users: 1,
    retentionDays: 30,
    multipleWorkspaces: false,
    whiteLabel: false,
    highRiskQueue: false,
    diffView: true,
  },
  professional: {
    liveMonitoring: true,
    sourceLimit: 80,           // 80 monitoring-active UAE sources after proof/baseline gates
    customSources: 2,          // requires activation
    weeklyBriefs: true,        // Telegram; email requires_activation
    auditExport: true,
    pdfExport: true,           // PDF audit pack for internal compliance files
    users: 2,
    retentionDays: 180,
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
    auditExport: true,
    pdfExport: true,           // PDF audit pack for internal compliance files
    users: 999,
    retentionDays: 999,
    multipleWorkspaces: false, // pilot_roadmap
    whiteLabel: false,         // pilot_roadmap
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
