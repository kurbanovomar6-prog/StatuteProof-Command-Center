// Honesty drift guard for the public landing surfaces (audit 2026-07-20,
// evidence_integrity + frontend_ux HIGHs):
//   - index.html meta description must not name CBUAE: commit c11c476 removed
//     CBUAE from the hero on purpose (rulebook.centralbank.ae 403s production
//     egress), so the meta description may not keep selling it.
//   - App.jsx / TrustLayer.jsx must not carry the UNCONDITIONAL present-tense
//     RFC 3161 claims ("chain head is anchored", "token ships in your evidence
//     exports") — app/rfc3161_anchor.py is dormant unless RFC3161_TSA_URL is
//     set, so the claims must be conditional ("supports ... when enabled").
//   - No public surface may name CBUAE inside a monitoring-SCOPE sentence
//     (Pricing.jsx, mockData.js, index.html): OnboardingPage.jsx and
//     Coverage.jsx disclose 0 fresh-alert-eligible CBUAE sources. Honest
//     remediation/limitation DISCLOSURES stay allowed — only scope claims fail.
//   - The /verify CHANGED sample must be described as a captured text
//     difference between two runs, not as a regulatory amendment.
//   - Cheap forbidden-claims sweep over the highest-traffic public files.
import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'

function findFile(rels) {
  const path = rels.map(r => resolve(process.cwd(), r)).find(existsSync)
  if (!path) throw new Error(`not found; looked in: ${rels.join(', ')}`)
  return path
}

const indexHtml = readFileSync(findFile(['index.html', 'web/index.html']), 'utf8')
const heroSrc = readFileSync(
  findFile(['src/components/Hero.jsx', 'web/src/components/Hero.jsx']),
  'utf8',
)
const appSrc = readFileSync(findFile(['src/App.jsx', 'web/src/App.jsx']), 'utf8')
const trustLayerSrc = readFileSync(
  findFile(['src/components/TrustLayer.jsx', 'web/src/components/TrustLayer.jsx']),
  'utf8',
)
const verifyPageSrc = readFileSync(
  findFile(['src/components/VerifyPage.jsx', 'web/src/components/VerifyPage.jsx']),
  'utf8',
)
const pricingSrc = readFileSync(
  findFile(['src/components/Pricing.jsx', 'web/src/components/Pricing.jsx']),
  'utf8',
)
const mockDataSrc = readFileSync(findFile(['src/data/mockData.js', 'web/src/data/mockData.js']), 'utf8')

// Strip JS comments: Hero.jsx legitimately mentions CBUAE ONLY in the comment
// explaining why it is excluded from the strip — that must not trip the guard.
function stripComments(src) {
  return src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|\s)\/\/.*$/gm, '$1')
}

// Collapse whitespace so JSX line wraps can't hide a phrase from a regex.
function flat(src) {
  return src.replace(/\s+/g, ' ')
}

// Comments-stripped, whitespace-collapsed source: what a reader actually sees.
function copyOf(src) {
  return flat(stripComments(src))
}

// Rough sentence split so a guard can judge one claim at a time: a limitation
// disclosed in one sentence must not excuse a scope claim in the next.
function sentences(src) {
  return copyOf(src)
    .split(/(?<=[.!?])\s+/)
    .filter(Boolean)
}

describe('index.html never claims CBUAE monitoring (hero honesty, c11c476)', () => {
  it('contains no CBUAE mention anywhere', () => {
    expect(indexHtml).not.toMatch(/CBUAE/i)
  })
})

describe('Hero.jsx claims no CBUAE outside comments', () => {
  it('code (comments stripped) contains no CBUAE', () => {
    expect(stripComments(heroSrc)).not.toMatch(/CBUAE/i)
  })
})

describe('RFC 3161 claims stay conditional (anchor is dormant-by-default)', () => {
  // Shape-based, not phrase-based: any present-tense assertion that anchoring
  // already happens fails unless the same sentence carries the "only when
  // enabled" qualifier that app/rfc3161_anchor.py actually requires.
  const UNCONDITIONAL = [
    /\b(is|are|gets?|get)\s+(automatically\s+)?anchored\b/i,
    /\b(is|are)\s+(RFC ?3161[- ])?timestamped\b/i,
    /\btokens?\s+ships?\b/i,
    /\b(every|each|all)\b[^.]{0,80}\b(includes?|ships? with|carries|contains?)\s+(an?\s+)?(RFC ?3161|timestamp token|\.tsr)/i,
  ]
  const CONDITIONAL = /\b(when|once|if)\s+(it is |they are )?(enabled|configured|switched on)|\bsupports?\b|\bcan be\b|\boptional\b/i
  const files = [
    ['App.jsx', appSrc],
    ['TrustLayer.jsx', trustLayerSrc],
  ]
  for (const [name, src] of files) {
    it(`${name} states no unconditional RFC 3161 anchoring claim`, () => {
      const offenders = sentences(src).filter(
        s => UNCONDITIONAL.some(re => re.test(s)) && !CONDITIONAL.test(s),
      )
      expect(offenders, `${name} unconditional anchoring claim(s)`).toEqual([])
    })
  }
})

// A monitoring-SCOPE sentence sells what we watch. CBUAE may only appear on a
// public surface as a disclosed limitation, never inside a scope claim.
const SCOPE_CLAIM = [
  /monitoring scope/i,
  /(regulatory |official )?sources?[^.]{0,40}\bacross\b/i,
  /source pack across/i,
  /checked on a defined schedule/i,
  /\bwe monitor\b/i,
]
const LIMITATION = /remediation|not counted|not currently counted|blocked|403|geo-?restricted|geo-?ip|unreachable|not (currently )?(monitored|available|eligible)|limitation|excluded/i

describe('no public surface sells CBUAE monitoring scope', () => {
  const files = [
    ['Pricing.jsx', pricingSrc],
    ['mockData.js', mockDataSrc],
    ['index.html', indexHtml],
  ]
  for (const [name, src] of files) {
    it(`${name} names CBUAE in no monitoring-scope sentence`, () => {
      const offenders = sentences(src).filter(
        s => /CBUAE/i.test(s) && SCOPE_CLAIM.some(re => re.test(s)) && !LIMITATION.test(s),
      )
      expect(offenders, `${name} CBUAE monitoring-scope claim(s)`).toEqual([])
    })
  }
})

describe('the /verify CHANGED sample is described as what it is', () => {
  it('VerifyPage.jsx does not call the sample a change the monitor captured', () => {
    expect(copyOf(verifyPageSrc)).not.toMatch(
      /is a change\s+(our|the)\s+monitor\s+captured|captured a (regulatory )?(change|amendment) (on|to) the official/i,
    )
  })
  it('VerifyPage.jsx discloses extraction variance between consecutive runs', () => {
    expect(copyOf(verifyPageSrc)).toMatch(/extraction variance/i)
  })
  it('VerifyPage.jsx names the sealed diff as the authoritative change count', () => {
    expect(copyOf(verifyPageSrc)).toMatch(/sealed diff[^.]{0,120}authoritative/i)
  })
})

describe('public landing files carry no forbidden claims', () => {
  const FORBIDDEN = [
    /never miss/i,
    /guarantee[sd]? compliance/i,
    /prevent fines/i,
    /100% accurate/i,
    /stay compliant automatically/i,
    /certified by (the )?(DFSA|VARA|ADGM|CBUAE|SCA|CMA|DIFC)/i,
  ]
  const files = [
    ['index.html', indexHtml],
    ['Hero.jsx', heroSrc],
    ['App.jsx', appSrc],
    ['TrustLayer.jsx', trustLayerSrc],
    ['VerifyPage.jsx', verifyPageSrc],
  ]
  for (const [name, src] of files) {
    for (const re of FORBIDDEN) {
      it(`${name} avoids ${re}`, () => {
        expect(re.test(copyOf(src)), `${name} contains forbidden claim ${re}`).toBe(false)
      })
    }
  }
})
