// Drift guard for the PUBLIC coverage counts.
//
// The Source Coverage page and the Source Transparency Matrix show hard numbers
// ("116 enabled", "83 fresh-alert eligible", "25 CBUAE", "3 of 5 VARA", ...).
// Those are compliance-facing claims: if sources.json changes and a number is
// left stale, the site over- or under-claims coverage. This test recomputes
// every published number straight from product/regradar/sources.json and fails
// the build the moment a claim drifts from the truth.
import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'
import { SOURCE_TRUTH } from './sourceCounts.js'

const CANDIDATES = [
  resolve(process.cwd(), '../sources.json'),
  resolve(process.cwd(), 'sources.json'),
  resolve(process.cwd(), '../../sources.json'),
]
const sourcesPath = CANDIDATES.find(existsSync)
if (!sourcesPath) {
  throw new Error(`sources.json not found; looked in: ${CANDIDATES.join(', ')}`)
}
const SOURCES = JSON.parse(readFileSync(sourcesPath, 'utf8'))

const isEnabled = s => s.enabled === true
const isFreshAlert = s =>
  s.enabled === true &&
  s.monitoring_mode === 'fresh_alert' &&
  s.alert_eligible === true

// Regulator = the AE-<reg>-... prefix of the source_id. This is the only stable
// discriminator (the free-text `category` field is inconsistent).
const reg = s => {
  const m = /^AE-([a-z]+)-/.exec(s.source_id || '')
  return m ? m[1] : '?'
}
const freshOf = prefixes =>
  SOURCES.filter(s => prefixes.includes(reg(s)) && isFreshAlert(s)).length
const enabledOf = prefixes =>
  SOURCES.filter(s => prefixes.includes(reg(s)) && isEnabled(s)).length

describe('public coverage headline counts (SourceCoverageTable)', () => {
  it('SOURCE_TRUTH.enabled === count of enabled sources', () => {
    expect(SOURCE_TRUTH.enabled).toBe(SOURCES.filter(isEnabled).length)
  })

  it('SOURCE_TRUTH.readinessSupported === count of fresh-alert eligible sources', () => {
    expect(SOURCE_TRUTH.readinessSupported).toBe(
      SOURCES.filter(isFreshAlert).length,
    )
  })

  it('SOURCE_TRUTH.candidate === count of enabled candidate-mode sources', () => {
    const candidates = SOURCES.filter(
      s => isEnabled(s) && s.monitoring_mode === 'candidate',
    ).length
    expect(SOURCE_TRUTH.candidate).toBe(candidates)
  })

  it('never claims more fresh-alert sources than enabled sources', () => {
    expect(SOURCE_TRUTH.readinessSupported).toBeLessThanOrEqual(
      SOURCE_TRUTH.enabled,
    )
  })
})

// Each row here mirrors a numeric claim rendered by SourceTransparencyMatrix.jsx.
// If sources.json drifts, `actual` changes and the assertion fails, pointing the
// maintainer at the exact matrix row (and the coverage page) to reconcile.
describe('per-regulator matrix counts (SourceTransparencyMatrix)', () => {
  const CLAIMS = [
    { label: 'CBUAE: "25 fresh-alert eligible"', fresh: 25, prefixes: ['cbuae'] },
    { label: 'VARA: "3 fresh-alert eligible of 5 enabled"', fresh: 3, enabled: 5, prefixes: ['vara'] },
    { label: 'DIFC/DFSA: "20 fresh-alert eligible across DIFC/DFSA"', fresh: 20, prefixes: ['difc', 'dfsa'] },
    { label: 'ADGM/FSRA: "9 fresh-alert eligible of 14 enabled"', fresh: 9, enabled: 14, prefixes: ['adgm'] },
    { label: 'UAE CMA: "6 fresh-alert eligible"', fresh: 6, prefixes: ['sca'] },
    { label: 'Tax/corporate: "MoF 7 fresh-alert"', fresh: 7, prefixes: ['mof'] },
    // "Six FTA listing sources are enabled…" + "no FTA source is counted as
    // fresh-alert eligible today" — guard both the 6 and the 0.
    { label: 'Tax/corporate: "Six FTA listing sources are enabled", 0 fresh', fresh: 0, enabled: 6, prefixes: ['fta'] },
    // "Legislation / gazettes: 0 fresh-alert eligible" — MoJ (AE-ministry-…)
    // and the Dubai Legislation Portal (AE-dubai-…). If any of these ever
    // passes the fresh-alert gate, the matrix row must be rewritten.
    // minEnabled prevents a VACUOUS pass: 0===0 would also hold if the
    // prefixes stopped matching anything (e.g. after a source_id rename).
    { label: 'Legislation/gazettes: "0 fresh-alert eligible"', fresh: 0, minEnabled: 1, prefixes: ['ministry', 'dubai'] },
    // "Markets / free zones / other federal: 0 fresh-alert eligible — candidates"
    { label: 'Markets/free zones: "0 fresh-alert eligible — candidates"', fresh: 0, minEnabled: 1, prefixes: ['dfm', 'dmcc', 'jafza', 'icp', 'tdra', 'moccae'] },
  ]

  for (const claim of CLAIMS) {
    it(`matches the truth — ${claim.label}`, () => {
      expect(freshOf(claim.prefixes), `${claim.label}: fresh drift`).toBe(
        claim.fresh,
      )
      if (typeof claim.enabled === 'number') {
        expect(enabledOf(claim.prefixes), `${claim.label}: enabled drift`).toBe(
          claim.enabled,
        )
      }
      if (typeof claim.minEnabled === 'number') {
        expect(
          enabledOf(claim.prefixes),
          `${claim.label}: prefixes match no enabled source — vacuous guard`,
        ).toBeGreaterThanOrEqual(claim.minEnabled)
      }
    })
  }
})
