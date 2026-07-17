// 2.1 drift guard: the landing #evidence card claims to show a REAL sealed
// record — "nothing here is invented" — so every load-bearing field in
// App.jsx's REAL_RECORD must match the shipped asset public/sample-record/
// record.json (the same artifact /verify#sample loads and re-hashes). If the
// asset is ever refreshed, this test forces the card to follow.
import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'

function findFile(rels) {
  const path = rels.map(r => resolve(process.cwd(), r)).find(existsSync)
  if (!path) throw new Error(`not found; looked in: ${rels.join(', ')}`)
  return path
}

const record = JSON.parse(
  readFileSync(
    findFile(['public/sample-record/record.json', 'web/public/sample-record/record.json']),
    'utf8',
  ),
)
const normalized = readFileSync(
  findFile(['public/sample-record/normalized.txt', 'web/public/sample-record/normalized.txt']),
  'utf8',
)
const appSrc = readFileSync(findFile(['src/App.jsx', 'web/src/App.jsx']), 'utf8')

describe('landing REAL_RECORD is pinned to the shipped verifiable asset (2.1)', () => {
  it('shows the exact current_hash of the shipped record', () => {
    expect(appSrc).toContain(record.content.current_hash)
  })

  it('shows the exact capture timestamp of the shipped record', () => {
    expect(appSrc).toContain(record.run.timestamp)
  })

  it('names the same source', () => {
    expect(appSrc).toContain(record.source.source_id)
    expect(appSrc).toContain(record.source.official_url)
  })

  it('char count matches the shipped normalized bytes', () => {
    expect(appSrc).toContain(`normalized_chars: ${normalized.length}`)
  })

  it('the shipped record is a MODERN self-sealed record (no skipped hash checks)', () => {
    expect(String(record.record_hash || '')).toMatch(/^sha256:[a-f0-9]{64}$/)
    expect(record.record_hash_method).toBe('content-sha256-v1')
    expect(String(record.content.raw_hash || '')).toMatch(/^sha256:[a-f0-9]{64}$/)
    expect(record.content.captured_at).toBeTruthy()
    expect(record.content.source_url).toBeTruthy()
  })

  it('the shipped record itself is complete and self-sealed', () => {
    expect(record.record_status).toBe('complete')
    expect(record.integrity.integrity_status).toBe('VERIFIED')
  })

  it('the #evidence section no longer stamps SAMPLE / FAKE', () => {
    const evidenceSection = appSrc.slice(
      appSrc.indexOf('id="evidence"') - 400,
      appSrc.indexOf('id="evidence"') + 2400,
    )
    expect(evidenceSection).not.toMatch(/SAMPLE \/ FAKE/)
    expect(evidenceSection).toContain('REAL_RECORD')
  })
})

// LOW (qa re-score): the card's "Verified · SHA-256 match" line is driven by
// proof_chain.chain_verified — for this legacy record (no record_hash) it must
// mirror the shipped record's integrity verdict, never free-float.
describe('REAL_RECORD chain_verified mirrors the shipped integrity verdict', () => {
  it('record.json integrity.hash_verified is true when the card claims verified', () => {
    const claimsVerified = /proof_chain: \{ chain_verified: true/.test(appSrc)
    expect(claimsVerified).toBe(record.integrity.hash_verified === true)
  })
})
