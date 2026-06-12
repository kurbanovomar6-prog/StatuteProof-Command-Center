// Plan definitions — no Stripe, no payment processing.
// Billing is manually activated for founding pilots.

export const PLAN_NAMES = {
  EVIDENCE_PREVIEW: 'evidence_preview',
  STARTER_PILOT: 'starter_pilot',
  PROFESSIONAL: 'professional',
  CONSULTANT: 'consultant',
}

export const PLAN_DISPLAY = {
  evidence_preview: 'Evidence Preview',
  starter_pilot: 'Starter Pilot',
  professional: 'Professional',
  consultant: 'Compliance Consultant',
}

export const PLAN_PRICE = {
  evidence_preview: 'Free',
  starter_pilot: '$299',
  professional: '$799',
  consultant: 'From $1,500',
}

export const PLAN_PERIOD = {
  evidence_preview: '',
  starter_pilot: '/ month',
  professional: '/ month',
  consultant: '/ month or custom',
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
    sourceLimit: 3,
    customSources: 0,
    weeklyBriefs: 'limited',
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
    sourceLimit: 16,
    customSources: 3,
    weeklyBriefs: true,
    auditExport: true,
    pdfExport: true,
    users: 3,
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
    auditExport: true,
    pdfExport: true,
    users: 999,
    retentionDays: 999,
    multipleWorkspaces: true,
    whiteLabel: true,
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
  if (val === 'limited') return 'limited'
  return Boolean(val)
}
