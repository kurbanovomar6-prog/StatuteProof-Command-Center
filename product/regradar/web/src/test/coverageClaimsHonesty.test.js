// DH-1/DH-2/DH-8 drift guard for the two hardcoded coverage surfaces that
// mockDataHonesty.test.js did NOT cover:
//   - OnboardingPage SOURCE_READINESS_PREVIEW (the per-regulator "N fresh-alert
//     eligible" claims shown at the moment a customer picks source layers), and
//   - SourceCoverageTable SOURCES (the ACTIVE / "Fresh-alert eligible" badges).
// Both are compliance-facing claims. This recomputes the truth from
// product/regradar/sources.json and fails the build if either surface over-claims.
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
  readFileSync(findFile(['../sources.json', 'sources.json', '../../sources.json']), 'utf8'),
)
const modeOf = new Map(SOURCES.map(s => [s.source_id, s.monitoring_mode]))
const reg = s => (/^AE-([a-z]+)-/.exec(s.source_id || '') || [])[1] || '?'
const freshOf = prefixes =>
  SOURCES.filter(
    s => prefixes.includes(reg(s)) && s.enabled === true &&
      s.monitoring_mode === 'fresh_alert' && s.alert_eligible === true,
  ).length

const onboarding = readFileSync(
  findFile(['src/components/app/OnboardingPage.jsx', 'web/src/components/app/OnboardingPage.jsx']),
  'utf8',
)
const coverageTable = readFileSync(
  findFile(['src/components/SourceCoverageTable.jsx', 'web/src/components/SourceCoverageTable.jsx']),
  'utf8',
)

// Pull the leading "N fresh-alert eligible <FAMILY>" integer from a preview block.
function previewFresh(block) {
  const m = /(\d+)\s+fresh-alert eligible/.exec(block)
  return m ? Number(m[1]) : null
}

describe('OnboardingPage source-readiness preview never over-claims coverage (DH-1)', () => {
  const cases = [
    { family: 'VARA', key: 'VARA', prefixes: ['vara'] },
    { family: 'ADGM/FSRA', key: "'ADGM / FSRA'", prefixes: ['adgm'] },
  ]
  for (const { family, key, prefixes } of cases) {
    it(`${family} fresh-alert count matches the registry`, () => {
      // Grab the object block for this regulator key.
      const re = new RegExp(`${key.replace(/[/\\^$*+?.()|[\]{}]/g, '\\$&')}\\s*:\\s*\\{([\\s\\S]*?)\\}`)
      const block = re.exec(onboarding)
      expect(block, `preview block for ${family} not found`).toBeTruthy()
      const claimed = previewFresh(block[1])
      expect(claimed, `no "N fresh-alert eligible" number for ${family}`).not.toBeNull()
      expect(claimed).toBe(freshOf(prefixes))
    })
  }

  it('does not still claim the old "25 fresh-alert eligible VARA" number', () => {
    expect(/25\s+fresh-alert eligible VARA/.test(onboarding)).toBe(false)
  })
})

describe('SourceCoverageTable never badges a non-fresh-alert source as ACTIVE (DH-2)', () => {
  // Parse (source_id, status) pairs; source_id always precedes status per object.
  const rows = [...coverageTable.matchAll(/source_id:\s*'([^']+)'[\s\S]*?status:\s*'([^']+)'/g)]
    .map(m => ({ source_id: m[1], status: m[2] }))

  it('parsed at least the known rows', () => {
    expect(rows.length).toBeGreaterThan(5)
  })

  for (const row of rows) {
    it(`${row.source_id} is ACTIVE only when the registry mode is fresh_alert`, () => {
      if (row.status !== 'ACTIVE') return
      const mode = modeOf.get(row.source_id)
      // Unknown ids (not in the registry) are allowed as ACTIVE (representative
      // official sources); a KNOWN id badged ACTIVE must genuinely be fresh_alert.
      if (mode !== undefined) {
        expect(mode, `${row.source_id} is badged ACTIVE/"Fresh-alert eligible" but registry mode=${mode}`)
          .toBe('fresh_alert')
      }
    })
  }
})
