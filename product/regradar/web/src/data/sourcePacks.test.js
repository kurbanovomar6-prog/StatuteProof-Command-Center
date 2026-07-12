// Drift guard for the public "Source packs by licence type" section.
//
// This test reads the REAL product/regradar/sources.json and asserts that every
// source_id referenced by a pack layer exists AND that its declared status
// matches the source's actual monitoring state. If someone marks a source
// `active` that is not genuinely fresh-alert eligible (enabled + fresh_alert +
// alert_eligible), or references an id that no longer exists, the build fails.
//
// This is what prevents the public coverage claim from silently over-claiming.
import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'
import { SOURCE_PACKS } from './sourcePacks.js'

// vitest runs with cwd = the web/ package; sources.json lives one level up in
// product/regradar/. Try the expected path, then a couple of fallbacks so the
// test is robust to where the runner is launched from.
const CANDIDATES = [
  resolve(process.cwd(), '../sources.json'),
  resolve(process.cwd(), 'sources.json'),
  resolve(process.cwd(), '../../sources.json'),
]
const sourcesPath = CANDIDATES.find(existsSync)
if (!sourcesPath) {
  throw new Error(
    `sources.json not found; looked in: ${CANDIDATES.join(', ')}`,
  )
}
const SOURCES = JSON.parse(readFileSync(sourcesPath, 'utf8'))
const byId = new Map(SOURCES.map(s => [s.source_id, s]))

const isFreshAlert = s =>
  s.enabled === true &&
  s.monitoring_mode === 'fresh_alert' &&
  s.alert_eligible === true

// status => predicate the underlying source MUST satisfy
const STATUS_RULES = {
  active: s => isFreshAlert(s),
  // enabled but NOT yet a delivered fresh-alert source
  pending: s => s.enabled === true && !isFreshAlert(s),
  // configured but not activated
  roadmap: s => s.enabled === false,
  // geo-restricted / under remediation, documented not delivered
  geo_blocked: s =>
    s.enabled === false &&
    (s.status === 'geo_blocked' || s.monitoring_mode === 'remediation'),
  evidence_only: s => s.monitoring_mode === 'evidence_library',
  out_of_scope: s => s.enabled === false || s.monitoring_mode !== 'fresh_alert',
}

// Forbidden marketing claims (subset of CLAUDE.md) — never appear in copy.
const FORBIDDEN = [
  'guarantee compliance',
  'prevent fines',
  'ai lawyer',
  '100% accurate',
  'never miss',
  'stay compliant automatically',
  'avoid all penalties',
]

describe('source packs data integrity', () => {
  it('references only real source_ids from sources.json', () => {
    const missing = []
    for (const pack of SOURCE_PACKS) {
      for (const layer of pack.layers) {
        for (const id of layer.sourceIds) {
          if (!byId.has(id)) missing.push(`${pack.profile} :: ${id}`)
        }
      }
    }
    expect(missing, `unknown source_ids: ${missing.join(', ')}`).toEqual([])
  })

  it('never marks a non-fresh-alert source as active', () => {
    const overclaims = []
    for (const pack of SOURCE_PACKS) {
      for (const layer of pack.layers) {
        const rule = STATUS_RULES[layer.status]
        expect(rule, `no rule for status "${layer.status}"`).toBeTypeOf(
          'function',
        )
        for (const id of layer.sourceIds) {
          const src = byId.get(id)
          if (src && !rule(src)) {
            overclaims.push(
              `${pack.profile} :: "${layer.text}" claims ${layer.status} but ${id} is ` +
                `{enabled:${src.enabled}, mode:${src.monitoring_mode}, alert:${src.alert_eligible}, status:${src.status}}`,
            )
          }
        }
      }
    }
    expect(overclaims, overclaims.join('\n')).toEqual([])
  })

  it('every active layer traces to a genuinely fresh-alert eligible source', () => {
    for (const pack of SOURCE_PACKS) {
      for (const layer of pack.layers.filter(l => l.status === 'active')) {
        for (const id of layer.sourceIds) {
          expect(isFreshAlert(byId.get(id)), `${id} not fresh-alert`).toBe(true)
        }
      }
    }
  })

  it('contains no forbidden marketing claims', () => {
    const hits = []
    for (const pack of SOURCE_PACKS) {
      const blob = [
        pack.profile,
        pack.bestFor,
        pack.caveat || '',
        ...pack.layers.map(l => l.text),
      ]
        .join(' ')
        .toLowerCase()
      for (const phrase of FORBIDDEN) {
        if (blob.includes(phrase)) hits.push(`${pack.profile}: "${phrase}"`)
      }
    }
    expect(hits, hits.join(', ')).toEqual([])
  })

  it('every pack has at least one active source and a real profile', () => {
    for (const pack of SOURCE_PACKS) {
      expect(pack.profile.length).toBeGreaterThan(0)
      expect(pack.layers.some(l => l.status === 'active')).toBe(true)
    }
  })
})
