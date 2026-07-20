// VerifyPage sample loaders — the one-click loaders that fill the public
// verifier with REAL evidence records of public regulator content, shipped as
// static assets, then run the check:
//   - web/public/sample-record/          — baseline (FIRST_SEEN) VARA record
//   - web/public/sample-record-changed/  — CHANGED DIFC record WITH its sealed
//     diff, so /verify#sample demonstrates the diff_bytes_match check
// The fetch stub mirrors AlertRedline.test.jsx but serves the ACTUAL shipped
// assets read from disk, so these tests also pin the assets' own integrity
// (sha256(normalized) must equal the record's content.current_hash, and for the
// changed sample sha256(diff)/sha256(raw) must equal diff_hash/raw_hash).
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import VerifyPage from '../components/VerifyPage'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const SAMPLE_DIR = path.resolve(HERE, '../../public/sample-record')
const CHANGED_DIR = path.resolve(HERE, '../../public/sample-record-changed')

const RECORD_BYTES = readFileSync(path.join(SAMPLE_DIR, 'record.json'))
const RAW_BYTES = readFileSync(path.join(SAMPLE_DIR, 'raw.txt'))
const NORMALIZED_BYTES = readFileSync(path.join(SAMPLE_DIR, 'normalized.txt'))

const CHANGED_RECORD_BYTES = readFileSync(path.join(CHANGED_DIR, 'record.json'))
const CHANGED_RAW_BYTES = readFileSync(path.join(CHANGED_DIR, 'raw.txt'))
const CHANGED_NORMALIZED_BYTES = readFileSync(path.join(CHANGED_DIR, 'normalized.txt'))
const CHANGED_DIFF_BYTES = readFileSync(path.join(CHANGED_DIR, 'diff.txt'))
const CHANGED_TOKEN_BYTES = readFileSync(path.join(CHANGED_DIR, 'token.tsr'))
const CHANGED_TOKEN_B64 = CHANGED_TOKEN_BYTES.toString('base64')

const RECORD_TEXT = RECORD_BYTES.toString('utf-8')
const RAW_TEXT = RAW_BYTES.toString('utf-8')
const NORMALIZED_TEXT = NORMALIZED_BYTES.toString('utf-8')

const CHANGED_RECORD_TEXT = CHANGED_RECORD_BYTES.toString('utf-8')
const CHANGED_RAW_TEXT = CHANGED_RAW_BYTES.toString('utf-8')
const CHANGED_NORMALIZED_TEXT = CHANGED_NORMALIZED_BYTES.toString('utf-8')
const CHANGED_DIFF_TEXT = CHANGED_DIFF_BYTES.toString('utf-8')

const VERIFY_ENVELOPE = {
  ok: true,
  verified: true,
  checks: [
    { name: 'record_is_object', status: 'pass', detail: 'The submitted record is a JSON object of the expected shape.' },
    { name: 'hash_formats', status: 'pass', detail: 'All present hash fields are valid sha256:<64 lowercase hex>: current_hash, previous_hash.' },
    { name: 'record_hash_self_consistent', status: 'pass', detail: "Recomputing the canonical content hash reproduces the record's record_hash." },
    { name: 'raw_bytes_match', status: 'pass', detail: "sha256(raw.txt) matches the record's raw_hash." },
    { name: 'normalized_bytes_match', status: 'pass', detail: "sha256(normalized.txt) matches the record's current_hash." },
    { name: 'diff_bytes_match', status: 'pass', detail: "sha256(diff.txt) matches the record's diff_hash — the sealed redline is intact." },
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
    // Branch on '-changed' FIRST: substring matching must never hand the
    // changed loader the baseline bytes (or vice versa).
    if (url.includes('/sample-record-changed/')) {
      if (failAssets) {
        return Promise.resolve({ ok: false, status: 404, text: async () => 'not found' })
      }
      if (url.endsWith('token.tsr')) {
        // Binary asset: the component reads it via arrayBuffer().
        const buf = CHANGED_TOKEN_BYTES.buffer.slice(
          CHANGED_TOKEN_BYTES.byteOffset,
          CHANGED_TOKEN_BYTES.byteOffset + CHANGED_TOKEN_BYTES.byteLength,
        )
        return Promise.resolve({ ok: true, status: 200, arrayBuffer: async () => buf })
      }
      const body = url.endsWith('record.json')
        ? CHANGED_RECORD_TEXT
        : url.endsWith('raw.txt')
          ? CHANGED_RAW_TEXT
          : url.endsWith('diff.txt')
            ? CHANGED_DIFF_TEXT
            : CHANGED_NORMALIZED_TEXT
      return Promise.resolve({ ok: true, status: 200, text: async () => body })
    }
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
    expect(record.source?.regulator).toBe('VARA')
    expect(record.source?.official_url).toMatch(/^https:\/\/rulebooks\.vara\.ae\//)
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

describe('sample-record-changed static assets (shipped bytes)', () => {
  const record = JSON.parse(CHANGED_RECORD_TEXT)

  it('record.json is a real CHANGED evidence record of public regulator content', () => {
    expect(record.run?.status).toBe('CHANGED')
    expect(record.record_status).toBe('complete')
    expect(record.integrity?.integrity_status).toBe('VERIFIED')
    expect(record.source?.regulator).toBe('DIFC')
    expect(record.source?.official_url).toMatch(/^https:\/\/www\.difc\.ae\//)
  })

  it('carries a modern self-seal (record_hash, content-sha256-v1)', () => {
    expect(record.record_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
    expect(record.record_hash_method).toBe('content-sha256-v1')
  })

  it('sha256(normalized.txt) equals content.current_hash', () => {
    const digest = createHash('sha256').update(CHANGED_NORMALIZED_BYTES).digest('hex')
    expect(`sha256:${digest}`).toBe(record.content.current_hash)
  })

  it('sha256(raw.txt) equals content.raw_hash', () => {
    const digest = createHash('sha256').update(CHANGED_RAW_BYTES).digest('hex')
    expect(`sha256:${digest}`).toBe(record.content.raw_hash)
  })

  it('sha256(diff.txt) equals content.diff_hash — the sealed redline ships', () => {
    const digest = createHash('sha256').update(CHANGED_DIFF_BYTES).digest('hex')
    expect(`sha256:${digest}`).toBe(record.content.diff_hash)
  })

  it('carries previous_hash — the change is anchored to the prior capture', () => {
    expect(record.content.previous_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
  })

  it('ships a real RFC 3161 token within the UI upload limit (64KB)', () => {
    expect(CHANGED_TOKEN_BYTES.length).toBeGreaterThan(0)
    expect(CHANGED_TOKEN_BYTES.length).toBeLessThan(64 * 1024)
  })

  it('assets stay within the static-asset budget (<200KB total)', () => {
    const total =
      CHANGED_RECORD_BYTES.length +
      CHANGED_RAW_BYTES.length +
      CHANGED_NORMALIZED_BYTES.length +
      CHANGED_DIFF_BYTES.length
    expect(total).toBeLessThan(200 * 1024)
    expect(CHANGED_DIFF_BYTES.length).toBeGreaterThan(0)
  })
})

describe('VerifyPage sample loaders', () => {
  it('renders both loaders with honest real-record framing', () => {
    mockFetch()
    render(<VerifyPage onBack={() => {}} />)
    expect(
      screen.getByRole('button', { name: /load a real changed record/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /load a real baseline record/i }),
    ).toBeInTheDocument()
    expect(screen.getByText(/real evidence record of public regulator content/i)).toBeInTheDocument()
    expect(screen.getByText(/check the math yourself/i)).toBeInTheDocument()
  })

  it('loads the CHANGED record with its sealed diff and auto-runs the check', async () => {
    const verifyBodies = mockFetch()
    render(<VerifyPage onBack={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: /load a real changed record/i }))

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })

    // The form now holds the exact shipped bytes, including the diff.
    const textarea = screen.getByLabelText('record.json')
    expect(textarea.value).toBe(CHANGED_RECORD_TEXT.trim())
    expect(screen.getByText('diff.txt')).toBeInTheDocument()

    // POST /api/verify received record + raw + normalized + diff bytes, plus
    // the real TSA token attesting the record's own record_hash.
    expect(verifyBodies).toHaveLength(1)
    expect(verifyBodies[0].record).toEqual(JSON.parse(CHANGED_RECORD_TEXT))
    expect(verifyBodies[0].raw).toBe(CHANGED_RAW_TEXT)
    expect(verifyBodies[0].normalized).toBe(CHANGED_NORMALIZED_TEXT)
    expect(verifyBodies[0].diff).toBe(CHANGED_DIFF_TEXT)
    expect(verifyBodies[0].timestamp_token).toBe(CHANGED_TOKEN_B64)
    expect(verifyBodies[0].timestamp_digest).toBe(JSON.parse(CHANGED_RECORD_TEXT).record_hash)
  })

  it('loads the baseline record into the form and auto-runs the check (no diff)', async () => {
    const verifyBodies = mockFetch()
    render(<VerifyPage onBack={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: /load a real baseline record/i }))

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })

    const textarea = screen.getByLabelText('record.json')
    expect(textarea.value).toBe(RECORD_TEXT.trim())
    expect(screen.getByText('raw.txt')).toBeInTheDocument()
    expect(screen.getByText('normalized.txt')).toBeInTheDocument()

    expect(verifyBodies).toHaveLength(1)
    expect(verifyBodies[0].record).toEqual(JSON.parse(RECORD_TEXT))
    expect(verifyBodies[0].raw).toBe(RAW_TEXT)
    expect(verifyBodies[0].normalized).toBe(NORMALIZED_TEXT)
    expect(verifyBodies[0].diff).toBeUndefined()

    // The short disclaimer renders near the result, as the page already does.
    expect(screen.getByText(/confirms the integrity of the submitted record only/i)).toBeInTheDocument()
  })

  it('loading the baseline after the changed sample clears the staged DIFC diff', async () => {
    const verifyBodies = mockFetch()
    render(<VerifyPage onBack={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: /load a real changed record/i }))
    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: /load a real baseline record/i }))
    await waitFor(() => {
      expect(verifyBodies).toHaveLength(2)
    })
    // The baseline run must NOT silently pair the DIFC diff with the VARA record.
    expect(verifyBodies[1].record).toEqual(JSON.parse(RECORD_TEXT))
    expect(verifyBodies[1].diff).toBeUndefined()
    expect(screen.queryByText('diff.txt')).not.toBeInTheDocument()
  })

  it('deep link /verify#sample auto-loads the CHANGED record with its diff', async () => {
    const verifyBodies = mockFetch()
    window.location.hash = '#sample'
    render(<VerifyPage onBack={() => {}} />)

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })
    expect(verifyBodies).toHaveLength(1)
    expect(verifyBodies[0].record).toEqual(JSON.parse(CHANGED_RECORD_TEXT))
    expect(verifyBodies[0].diff).toBe(CHANGED_DIFF_TEXT)
  })

  it('deep link /verify#sample-baseline auto-loads the baseline record', async () => {
    const verifyBodies = mockFetch()
    window.location.hash = '#sample-baseline'
    render(<VerifyPage onBack={() => {}} />)

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })
    expect(verifyBodies).toHaveLength(1)
    expect(verifyBodies[0].record).toEqual(JSON.parse(RECORD_TEXT))
    expect(verifyBodies[0].diff).toBeUndefined()
  })

  it('does not auto-load without a #sample hash', async () => {
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

    fireEvent.click(screen.getByRole('button', { name: /load a real changed record/i }))

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
    fireEvent.click(screen.getByRole('button', { name: /load a real changed record/i }))
    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeInTheDocument()
    })
    const text = container.textContent.toLowerCase()
    for (const phrase of FORBIDDEN) {
      expect(text, `forbidden phrase rendered: "${phrase}"`).not.toContain(phrase)
    }
  })
})
