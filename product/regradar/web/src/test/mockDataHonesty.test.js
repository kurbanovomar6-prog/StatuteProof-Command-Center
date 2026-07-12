// Legal-honesty regression: the sample dashboard must not contradict the site's
// own coverage disclosure. The site discloses (Coverage.jsx, sourcePacks.js,
// SourceTransparencyMatrix.jsx) that the UAE FIU portal is geo-IP restricted
// from outside the UAE and NO FIU source is fresh-alert eligible today. The
// sample data previously showed "UAE FIU Publications Hub" as
// readiness_supported / Accessible — a contradiction. It must read as
// geo-restricted / not monitored.
import { describe, it, expect } from 'vitest'
import { sourceHealthRows, coverage } from '../data/mockData'

describe('sample dashboard data honesty (UAE FIU)', () => {
  it('shows the UAE FIU Publications Hub row as geo-restricted, not fresh-alert eligible', () => {
    const fiu = sourceHealthRows.find((r) => r.name === 'UAE FIU Publications Hub')
    expect(fiu).toBeTruthy()
    expect(fiu.status).toBe('geo_blocked')
    expect(fiu.quality).toBe('geo_blocked')
    // Must NOT claim readiness/accessibility for a geo-blocked source.
    expect(fiu.status).not.toBe('readiness_supported')
    expect(fiu.quality).not.toBe('readiness_supported')
    expect(fiu.access).not.toBe('Accessible')
    expect(fiu.verdict).not.toBe('READINESS')
  })

  it('marks the UAE FIU Publications Hub as geo_blocked in the coverage list', () => {
    const uae = coverage.find((c) => c.region === 'UAE')
    expect(uae).toBeTruthy()
    const fiu = uae.sources.find((s) => s.name === 'UAE FIU Publications Hub')
    expect(fiu).toBeTruthy()
    expect(fiu.status).toBe('geo_blocked')
    expect(fiu.status).not.toBe('readiness_supported')
  })
})
