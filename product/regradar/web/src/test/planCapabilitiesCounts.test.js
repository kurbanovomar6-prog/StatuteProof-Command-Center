// Drift guard for the hand-maintained source counts in data/planCapabilities.js.
//
// planCapabilities.js opens with a "Source truth:" line that states how many
// records are enabled and how they split across monitoring modes. Nothing
// derives those numbers — they are typed by hand — and they had drifted to
// "246 enabled; 180 fresh-alert eligible" against a register holding 140
// enabled and 41 alert-eligible. That line is what the next author reads before
// writing plan and pricing copy, so a stale number there becomes a stale number
// on a customer-facing page.
//
// Same approach as data/sourceCounts.test.js: recompute every claim straight
// from product/regradar/sources.json and fail the build the moment the comment
// and the register disagree. The assertion message prints the recomputed truth
// so the fix is a copy-paste, not an investigation.
import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'

function findFile(rels) {
  const path = rels.map(r => resolve(process.cwd(), r)).find(existsSync)
  if (!path) throw new Error(`not found; looked in: ${rels.join(', ')}`)
  return path
}

const SOURCES = JSON.parse(
  readFileSync(
    findFile(['../sources.json', 'sources.json', '../../sources.json']),
    'utf8',
  ),
)
const planSrc = readFileSync(
  findFile(['src/data/planCapabilities.js', 'web/src/data/planCapabilities.js']),
  'utf8',
)

const enabled = SOURCES.filter(s => s.enabled === true)
const countMode = mode => enabled.filter(s => s.monitoring_mode === mode).length
const freshAlert = enabled.filter(
  s => s.monitoring_mode === 'fresh_alert' && s.alert_eligible === true,
).length

// The claim line, parsed rather than imported: it is a comment, so the only way
// to check it is to read the file the way a human does.
const CLAIM_LINE =
  /\/\/\s*Source truth:\s*(\d+)\s+enabled[^;]*;\s*(\d+)\s+fresh-alert eligible,\s*(\d+)\s+evidence-library,\s*(\d+)\s+candidate,\s*(\d+)\s+remediation/

describe('planCapabilities.js "Source truth" comment matches sources.json', () => {
  const match = CLAIM_LINE.exec(planSrc)

  it('still states a machine-checkable source-truth line', () => {
    expect(
      match,
      'planCapabilities.js no longer carries a parseable "Source truth: N enabled; ' +
        'N fresh-alert eligible, N evidence-library, N candidate, N remediation" line — ' +
        'either restore that shape or delete the numbers entirely; an unparseable ' +
        'claim is an unguarded claim',
    ).not.toBeNull()
  })

  const CLAIMS = [
    ['enabled', 1, () => enabled.length],
    ['fresh-alert eligible', 2, () => freshAlert],
    ['evidence-library', 3, () => countMode('evidence_library')],
    ['candidate', 4, () => countMode('candidate')],
    ['remediation', 5, () => countMode('remediation')],
  ]

  for (const [label, group, truth] of CLAIMS) {
    it(`claims the real ${label} count`, () => {
      if (!match) return
      expect(
        Number(match[group]),
        `planCapabilities.js claims ${match[group]} ${label}; sources.json has ${truth()}`,
      ).toBe(truth())
    })
  }

  it('never claims more alert-eligible sources than enabled sources', () => {
    if (!match) return
    expect(Number(match[2])).toBeLessThanOrEqual(Number(match[1]))
  })
})
