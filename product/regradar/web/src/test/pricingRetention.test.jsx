import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import PricingPage from '../components/PricingPage'
import { PLAN_CAPABILITIES } from '../data/planCapabilities'

// Drift guard for the evidence-retention finding: the /pricing page used to
// claim 90 days (Founding Pilot) and 12 months (UAE Monitor) while the product
// enforces 30 and 180 days, and the privacy policy promises 30/180. Retention
// copy is now DERIVED from PLAN_CAPABILITIES.retentionDays, so this test pins
// that the rendered strings track the enforced source of truth and that the old
// overclaims never come back.

function expectedLabel(days) {
  if (!days || days <= 0) return 'Sample only'
  if (days >= 900) return 'Custom (extended) — export on demand'
  return `${days} days`
}

describe('PricingPage evidence retention', () => {
  it('renders retention derived from enforced plan capabilities', () => {
    render(<PricingPage onBack={() => {}} />)
    // Founding Pilot (starter_pilot) = 30 days, UAE Monitor (professional) = 180 days.
    expect(
      screen.getAllByText(expectedLabel(PLAN_CAPABILITIES.starter_pilot.retentionDays)).length,
    ).toBeGreaterThan(0)
    expect(
      screen.getAllByText(expectedLabel(PLAN_CAPABILITIES.professional.retentionDays)).length,
    ).toBeGreaterThan(0)
  })

  it('no longer overclaims retention (no 90 days / 12 months)', () => {
    render(<PricingPage onBack={() => {}} />)
    expect(screen.queryByText('90 days')).toBeNull()
    expect(screen.queryByText('12 months')).toBeNull()
  })
})

describe('PricingPage comparison table', () => {
  it('shows Diff view as included on the UAE Monitor (Recommended) plan', () => {
    // Regression for the label-prefix matcher bug: "Evidence records + full diff
    // view" must resolve the "Diff view" comparison row to included, not ✗.
    const { container } = render(<PricingPage onBack={() => {}} />)
    const rows = Array.from(container.querySelectorAll('tbody tr'))
    const diffRow = rows.find((r) => r.textContent.trim().startsWith('Diff view'))
    expect(diffRow).toBeTruthy()
    // 5 cells: label + 4 plans (free, starter, professional, consultant).
    const cells = diffRow.querySelectorAll('td')
    // Professional is the 3rd plan column (index 3 after the label cell).
    const professionalCell = cells[3]
    // Included renders a CheckCircle svg (lucide) rather than the X icon.
    expect(professionalCell.querySelector('svg')).toBeTruthy()
    // The "not included" X uses text-slate-600; included uses text-emerald-400.
    expect(professionalCell.innerHTML).toContain('text-emerald-400')
  })
})
