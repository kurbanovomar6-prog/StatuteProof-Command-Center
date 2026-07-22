// The consultant tier ("Talk to us") is a REAL backend plan
// (app/plan.py PLAN_NAMES). Selecting it must route through selectPlan so the
// intent is persisted (api_plan set_plan_intent) and the founder is paged —
// exactly like the paid tiers. Before the fix the consultant branch showed a
// green "our team will contact you" confirmation but returned WITHOUT calling
// selectPlan, so it was a dead-end claiming an action the code never performed.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChoosePlanPage from '../components/app/ChoosePlanPage'

function consultantCard() {
  return screen.getByRole('heading', { name: 'Compliance Consultant' }).closest('div')
}

describe('ChoosePlanPage — consultant tier is not a dead-end', () => {
  it('routes the consultant selection through selectPlan', async () => {
    const user = userEvent.setup()
    const selectPlan = vi.fn().mockResolvedValue(undefined)
    const onContinue = vi.fn()
    render(<ChoosePlanPage selectPlan={selectPlan} onContinue={onContinue} />)

    await user.click(within(consultantCard()).getByRole('button', { name: 'Talk to us' }))

    expect(selectPlan).toHaveBeenCalledTimes(1)
    expect(selectPlan).toHaveBeenCalledWith('consultant')
  })

  it('confirms with honest, forbidden-claim-free copy after intent is recorded', async () => {
    const user = userEvent.setup()
    const selectPlan = vi.fn().mockResolvedValue(undefined)
    render(<ChoosePlanPage selectPlan={selectPlan} onContinue={() => {}} />)

    await user.click(within(consultantCard()).getByRole('button', { name: 'Talk to us' }))

    const confirm = await screen.findByText(/contact you to discuss your requirements/i)
    const text = confirm.textContent
    expect(text).toMatch(/No payment has been processed/i)
    // Forbidden-claims guard (CLAUDE.md): the confirmation must never promise
    // compliance outcomes.
    expect(text).not.toMatch(/guarantee compliance/i)
    expect(text).not.toMatch(/prevent fines/i)
    expect(text).not.toMatch(/never miss/i)
    expect(text).not.toMatch(/stay compliant/i)
  })

  it('surfaces an error and does not claim success when selectPlan fails', async () => {
    const user = userEvent.setup()
    const selectPlan = vi.fn().mockRejectedValue(new Error('network'))
    render(<ChoosePlanPage selectPlan={selectPlan} onContinue={() => {}} />)

    await user.click(within(consultantCard()).getByRole('button', { name: 'Talk to us' }))

    expect(await screen.findByText(/Could not save plan selection/i)).toBeTruthy()
    expect(screen.queryByText(/contact you to discuss your requirements/i)).toBeNull()
  })

  it('still routes the paid professional tier through selectPlan', async () => {
    const user = userEvent.setup()
    const selectPlan = vi.fn().mockResolvedValue(undefined)
    render(<ChoosePlanPage selectPlan={selectPlan} onContinue={() => {}} />)

    await user.click(screen.getByRole('button', { name: 'Request UAE Monitor activation' }))

    expect(selectPlan).toHaveBeenCalledWith('professional')
    expect(await screen.findByText(/activate your founding pilot/i)).toBeTruthy()
  })
})
