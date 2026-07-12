// VerifyPage "Load a real record" — the one-click sample loader that fills the
// public verifier with a REAL evidence record of public regulator content
// (DFSA Rules and Standards) shipped as static assets under
// web/public/sample-record/, then runs the check. The fetch stub mirrors
// AlertRedline.test.jsx but serves the ACTUAL shipped assets read from disk, so
// these tests also pin the assets' own integrity (sha256(normalized) must equal
// the record's content.current_hash).
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import VerifyPage from '../components/VerifyPage'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const SAMPLE_DIR = path.resolve(HERE, '../../public/sample-record')

const RECORD_BYTES = readFileSync(path.join(SAMPLE_DIR, 'record.json'))
const RAW_BYTES = readFileSync(path.join(SAMPLE_DIR, 'raw.txt'))
const NORMALIZED_BYTES = readFileSync(path.join(SAMPLE_DIR, 'normalized.txt'))

const RECORD_TEXT = RECORD_BYTES.toString('utf-8')
const RAW_TEXT = RAW_BYTES.toString('utf-8')
const NORMALIZED_TEXT = NORMALIZED_BYTES.toString('utf-8')

const VERIFY_ENVELOPE = {
  ok: true,
  verified: true,
  checks: [
    { name: 'record_is_object', status: 'pass', detail: 'The submitted record is a JSON object of the expected shape.' },
    { name: 'hash_formats', status: 'pass', detail: 'All present hash fields are valid sha256:<64 lowercase hex>: current_hash, previous_hash.' },
    { name: 'record_hash_self_consistent', status: 'skipped', detail: 'The record carries no record_hash (e.g. a legacy record predating the content-sha256-v1 seal); nothing to self-check.' },
    { name: 'raw_bytes_match', status: 'skipped', detail: 'The record carries no raw_hash to compare the submitted raw.txt against.' },
    { name: 'normalized_bytes_match', status: 'pass', detail: "sha256(normalized.txt) matches the record's current_hash." },
    { name: 'normalization_reproducible', status: 'pass', detail: 'normalize_for_change_hash(raw.txt) reproduces normalized.txt byte-for-byte.' },
  ],
  spec_url: '/verify-spec',
  disclaimer:
    'Verification confirms the integrity of the submitted record only. Monitoring information only. Not legal advice.',
}

function mockFetch({ failAssets = false } = {}) {
  const verifyBodies = []
  globalThis.fetch = vi.fn((input, options = {}) => {
    const url = typeof input === 'string' ? input : String(input?.url || '')
    if (url.includes('/sample-record/')) {
      if (failAssets) {
        return Promise.resolve({ ok: false, status: 404, text: async () => 'not found' })
      }
      const body = url.endsWith('record.json')
        ? RECORD_TEXT
        : url.endsWith('raw.txt')
          ? RAW_TEXT
          : NORMALIZED_TEXT
      return Promise.resolve({ ok: true, status: 200, text: async () => body })
    }
    if (url.includes('/api/verify')) {
      verifyBodies.push(JSON.parse(options.body))
      return Promise.resolve({ ok: true, status: 200, json: async () => VERIFY_ENVELOPE })
    }
    return Promise.reject(new Error(`unexpected fetch in test: ${url}`))
  })
  return verifyBodies
}

afterEach(() => {
  vi.restoreAllMocks()
  window.location.hash = ''
})

describe('sample-record static assets (shipped bytes)', () => {
  it('record.json is a real, well-formed evidence record of public regulator content', () => {
    const record = JSON.parse(RECORD_TEXT)
    expect(record.record_status).toBe('complete')
    expect(record.integrity?.integrity_status).toBe('VERIFIED')
    expect(record.source?.regulator).toBe('DFSA')
    expect(record.source?.official_url).toMatch(/^https:\/\/www\.dfsa\.ae\//)
    expect(record.content?.current_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
  })

  it('sha256(normalized.txt) equals the record content.current_hash — the shipped bytes really verify', () => {
    const record = JSON.parse(RECORD_TEXT)
    const digest = createHash('sha256').update(NORMALIZED_BYTES).digest('hex')
    expect(`sha256:${digest}`).toBe(record.content.current_hash)
  })

  it('assets stay within the static-asset budget (<200KB total)', () => {
    const total = RECORD_BYTES.length + RAW_BYTES.length + NORMALIZED_BYTES.length
    expect(total).toBeLessThan(200 * 1024)
    expect(RAW_BYTES.length).toBeGreaterThan(0)
  })
})

describe('VerifyPage sample loader', () => {
  it('renders the loader with honest real-record framing', () => {
    mockFetch()
    render(<VerifyPage onBack={() => {}} />)
    expect(screen.getByRole('button', { name: /load a real record/i })).toBeInTheDocument()
    expect(screen.getByText(/real evidence record of public regulator content/i)).toBeInTheDocument()
    expect(screen.getByText(/check the math yourself/i)).toBeInTheDocument()
  })

  it('loads the static record into the form and auto-runs the check', async () => {
    const verifyBodies = mockFetch()
    render(<VerifyPage onBack={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: /load a real record/i }))

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })

    // The form now holds the exact shipped bytes.
    const textarea = screen.getByLabelText('record.json')
    expect(textarea.value).toBe(RECORD_TEXT.trim())
    expect(screen.getByText('raw.txt')).toBeInTheDocument()
    expect(screen.getByText('normalized.txt')).toBeInTheDocument()

    // And POST /api/verify received the real record + raw + normalized bytes.
    expect(verifyBodies).toHaveLength(1)
    expect(verifyBodies[0].record).toEqual(JSON.parse(RECORD_TEXT))
    expect(verifyBodies[0].raw).toBe(RAW_TEXT)
    expect(verifyBodies[0].normalized).toBe(NORMALIZED_TEXT)

    // The short disclaimer renders near the result, as the page already does.
    expect(screen.getByText(/confirms the integrity of the submitted record only/i)).toBeInTheDocument()
  })

  it('deep link /verify#sample auto-loads the built-in record only', async () => {
    const verifyBodies = mockFetch()
    window.location.hash = '#sample'
    render(<VerifyPage onBack={() => {}} />)

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })
    expect(verifyBodies).toHaveLength(1)
    expect(verifyBodies[0].record).toEqual(JSON.parse(RECORD_TEXT))
  })

  it('does not auto-load without the #sample hash', async () => {
    const verifyBodies = mockFetch()
    render(<VerifyPage onBack={() => {}} />)
    // Give any (wrong) effect a tick to fire.
    await new Promise((resolve) => setTimeout(resolve, 20))
    expect(verifyBodies).toHaveLength(0)
    expect(screen.queryByText('Verified')).not.toBeInTheDocument()
  })

  it('shows an honest error when the static assets cannot be fetched', async () => {
    mockFetch({ failAssets: true })
    render(<VerifyPage onBack={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: /load a real record/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/could not be loaded/i)
    })
    expect(screen.queryByText('Verified')).not.toBeInTheDocument()
  })

  it('page copy carries no forbidden claims after the sample verifies', async () => {
    // Mirror AlertRedline.test.jsx: strings authored only in the JSX bypass the
    // server-side legal_safety gate, so guard them here.
    const FORBIDDEN = [
      'guarantee compliance',
      'guarantees compliance',
      'proves compliance',
      'prevent fines',
      'ai lawyer',
      '100% accurate',
      'never miss',
      'stay compliant automatically',
      'avoid all penalties',
      'proof of compliance',
      'tamper-proof',
      'tamper proof',
    ]
    mockFetch()
    const { container } = render(<VerifyPage onBack={() => {}} />)
    fireEvent.click(screen.getByRole('button', { name: /load a real record/i }))
    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })
    const text = container.textContent.toLowerCase()
    for (const phrase of FORBIDDEN) {
      expect(text, `forbidden phrase rendered: "${phrase}"`).not.toContain(phrase)
    }
  })
})
