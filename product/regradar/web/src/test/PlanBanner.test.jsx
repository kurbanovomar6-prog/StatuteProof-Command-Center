// PlanBanner must advertise ONLY the entitlements the account has actually been
// activated to. A user who self-selects a paid tier (plan_name=professional)
// but is still pending manual activation keeps evidence_preview caps — the
// banner must render the ACTIVE caps (active_capabilities / active_plan_name),
// label the self-selected plan as pending, and never present the requested
// tier's Source limit / Users / retention as current.
import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import PlanBanner from '../components/app/PlanBanner'

const EVIDENCE_PREVIEW_CAPS = {
  liveMonitoring: false,
  sourceLimit: 0,
  customSources: 0,
  weeklyBriefs: false,
  auditExport: false,
  pdfExport: false,
  users: 1,
  retentionDays: 0,
}

const PROFESSIONAL_CAPS = {
  liveMonitoring: false,
  sourceLimit: 172,
  customSources: 2,
  weeklyBriefs: true,
  auditExport: true,
  pdfExport: true,
  users: 2,
  retentionDays: 180,
}

// A user who POSTed plan_name=professional but has NOT been activated: the
// backend keeps active_plan_name=evidence_preview and active_capabilities at
// the free tier, while capabilities/plan_display carry the requested plan.
const pendingProfessionalState = {
  plan_name: 'professional',
  plan_display: 'UAE Monitor',
  active_plan_name: 'evidence_preview',
  active_plan_display: 'Source Readiness Review',
  requested_plan: 'professional',
  requested_plan_display: 'UAE Monitor',
  status: 'pending_manual_activation',
  capabilities: PROFESSIONAL_CAPS,
  requested_capabilities: PROFESSIONAL_CAPS,
  active_capabilities: EVIDENCE_PREVIEW_CAPS,
}

function metric(label) {
  const labelNode = screen.getByText(label)
  return labelNode.parentElement.querySelector('p:last-child').textContent
}

describe('PlanBanner — pending manual activation', () => {
  it('renders ACTIVE caps, not the self-selected professional caps', () => {
    render(<PlanBanner planState={pendingProfessionalState} />)

    // Source limit / Users / retention must reflect the free active tier,
    // never the requested UAE Monitor caps (Custom / 2 / 180 days).
    expect(metric('Source limit')).toBe('—')
    expect(metric('Source limit')).not.toBe('Custom')
    expect(metric('Users')).toBe('1')
    expect(metric('Users')).not.toBe('2')
    expect(metric('Evidence retention')).toBe('—')
    expect(metric('Evidence retention')).not.toBe('180 days')

    // "Current plan" reflects the active (granted) tier, not the requested one.
    expect(metric('Current plan')).toBe('Source Readiness Review')
  })

  it('labels the self-selected plan as pending and shows a pending badge', () => {
    render(<PlanBanner planState={pendingProfessionalState} />)

    expect(screen.getByText('Pending activation')).toBeTruthy()
    // The requested tier is named as pending, not advertised as current.
    const pendingNote = screen.getByText(/pending manual activation/i)
    expect(pendingNote.textContent).toMatch(/UAE Monitor/)
  })

  it('renders requested caps once the plan is actually activated', () => {
    const activeState = {
      ...pendingProfessionalState,
      active_plan_name: 'professional',
      active_plan_display: 'UAE Monitor',
      requested_plan: null,
      requested_plan_display: null,
      status: 'active',
      active_capabilities: PROFESSIONAL_CAPS,
      requested_capabilities: null,
    }
    render(<PlanBanner planState={activeState} />)

    expect(metric('Current plan')).toBe('UAE Monitor')
    expect(metric('Source limit')).toBe('Custom')
    expect(metric('Users')).toBe('2')
    expect(metric('Evidence retention')).toBe('180 days')
    expect(screen.getByText('Plan enabled')).toBeTruthy()
    expect(screen.queryByText(/pending manual activation/i)).toBeNull()
  })
})
