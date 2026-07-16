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
import { SOURCE_QUALITY_SUMMARY, SAFE_CLAIMS, AUDIT_META } from '../data/sourceQualityAudit.ts'

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

// DH-3: the SAFE_CLAIMS / recommendedSalesClaim strings are labelled as sales
// copy — they must match the summary's own fresh-alert number and never carry a
// stale figure. (This file had a stale "83" against a header of 74.)
describe('sourceQualityAudit sales claims match the summary (DH-3)', () => {
  const n = SOURCE_QUALITY_SUMMARY.freshAlertEligible

  it('no SAFE_CLAIM or the recommendedSalesClaim carries the stale "83"', () => {
    for (const claim of SAFE_CLAIMS) expect(claim).not.toMatch(/\b83\b/)
    expect(AUDIT_META.recommendedSalesClaim).not.toMatch(/\b83\b/)
  })

  it('the headline fresh-alert claim states the summary number', () => {
    expect(SAFE_CLAIMS[0]).toContain(`${n} fresh-alert-eligible`)
    expect(AUDIT_META.recommendedSalesClaim).toContain(`${n} fresh-alert-eligible`)
  })

  it('FIU is never claimed to have fresh-alert sources', () => {
    const joined = SAFE_CLAIMS.join(' ')
    expect(/FIU has \d+ fresh-alert/.test(joined)).toBe(false)
  })
})

// DH-6: no id hardcoded as "Needs remediation" on the dashboard may actually be
// fresh_alert in the registry (that under-claims and contradicts the public site).
const dashboardHome = readFileSync(
  findFile(['src/components/app/DashboardHome.jsx', 'web/src/components/app/DashboardHome.jsx']),
  'utf8',
)
describe('DashboardHome remediation set has no promoted source (DH-6)', () => {
  const block = /REMEDIATION_SOURCE_IDS\s*=\s*new Set\(\[([\s\S]*?)\]\)/.exec(dashboardHome)
  const ids = block ? [...block[1].matchAll(/'([^']+)'/g)].map(m => m[1]) : []
  it('parsed the remediation set', () => expect(ids.length).toBeGreaterThan(0))
  for (const id of ids) {
    it(`${id} is not fresh_alert in the registry`, () => {
      const mode = modeOf.get(id)
      if (mode !== undefined) expect(mode, `${id} is hardcoded remediation but registry mode=${mode}`).not.toBe('fresh_alert')
    })
  }
})

// LG-5: the landing samples must not model obligation / legal-advice voice.
describe('landing samples avoid obligation voice (LG-5)', () => {
  const banned = [
    /\bmust update\b/i,
    /must be reconfigured/i,
    /constitutes a reportable compliance gap/i,
    /triggers a mandatory STR obligation/i,
    /must .{0,40}immediately/i,
  ]
  const files = [
    ['SampleBrief', readFileSync(findFile(['src/components/SampleBrief.jsx', 'web/src/components/SampleBrief.jsx']), 'utf8')],
    ['AIInsightSection', readFileSync(findFile(['src/components/AIInsightSection.jsx', 'web/src/components/AIInsightSection.jsx']), 'utf8')],
  ]
  for (const [name, txt] of files) {
    for (const re of banned) {
      it(`${name} avoids ${re}`, () => expect(re.test(txt), `${name} contains obligation-voice ${re}`).toBe(false))
    }
  }
})

// 2.4: the plan-selection screen (the moment money changes hands) must never
// sell a regulator in the "fresh-alert source pack" line that has ZERO
// fresh-alert eligible sources in the registry. Regression: it sold "UAE FIU"
// while the pricing FAQ and onboarding honestly disclose FIU as geo-blocked.
describe('ChoosePlanPage fresh-alert pack claim matches the registry (2.4)', () => {
  const choosePlan = readFileSync(
    findFile(['src/components/app/ChoosePlanPage.jsx', 'web/src/components/app/ChoosePlanPage.jsx']),
    'utf8',
  )
  const packLine = (choosePlan.match(/'Selected ([^']+) fresh-alert source pack'/) || [])[1] || ''

  it('has a fresh-alert pack feature line to check', () => {
    expect(packLine.length).toBeGreaterThan(0)
  })

  it('does not sell UAE FIU as fresh-alert', () => {
    expect(/FIU/i.test(packLine)).toBe(false)
  })

  const famOfToken = { VARA: ['vara'], CBUAE: ['cbuae'], DFSA: ['dfsa'], ADGM: ['adgm'], SCA: ['sca'], DIFC: ['difc'], EOCN: ['eocn'], MoF: ['mof'] }
  const tokens = packLine.split('/').map(t => t.trim()).filter(Boolean)
  for (const token of tokens) {
    const fams = famOfToken[token]
    it(`"${token}" has fresh-alert eligible sources in the registry`, () => {
      expect(fams, `unknown regulator token "${token}" on the plan line — extend famOfToken`).toBeDefined()
      expect(freshOf(fams), `"${token}" is sold as fresh-alert but registry has 0`).toBeGreaterThan(0)
    })
  }
})
