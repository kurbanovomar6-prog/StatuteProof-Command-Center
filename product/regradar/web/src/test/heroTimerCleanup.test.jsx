// Regression: the Hero EvidenceDossier rotates signal cards on a 5s interval,
// and each tick schedules a nested 300ms fade setTimeout. The interval was
// cleared on unmount but the nested timeout was NOT — so unmounting during the
// 300ms fade window left a pending timeout that fires setState on an unmounted
// component. The effect cleanup must clear BOTH timers.
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import Hero from '../components/Hero'

describe('Hero EvidenceDossier timer cleanup', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // Hero (and MonitoringStatusBadge) call fetch in an effect — stub it so the
    // component mounts without a real network call.
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ json: () => Promise.resolve({}) })),
    )
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('clears the nested fade timeout on unmount', () => {
    const setTimeoutSpy = vi.spyOn(globalThis, 'setTimeout')
    const clearTimeoutSpy = vi.spyOn(globalThis, 'clearTimeout')

    const { unmount } = render(<Hero />)

    // Fire the 5s rotation interval — this schedules the nested 300ms fade
    // setTimeout inside the running effect.
    act(() => {
      vi.advanceTimersByTime(5000)
    })

    // Find the id of the 300ms fade timeout that was just scheduled.
    const fadeIndex = setTimeoutSpy.mock.calls.findIndex((call) => call[1] === 300)
    expect(fadeIndex).toBeGreaterThanOrEqual(0)
    const fadeTimerId = setTimeoutSpy.mock.results[fadeIndex].value

    // Unmount DURING the fade window and assert the cleanup cleared that exact
    // timeout id. Without the fix, clearTimeout is never called with this id.
    unmount()
    expect(clearTimeoutSpy).toHaveBeenCalledWith(fadeTimerId)
  })
})
