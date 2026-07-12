// FirstRunBackfillPanel shows the latest ALREADY-SEALED changed records only
// while the alerts preview is empty — an honest "here is what the evidence
// trail looks like" first-run view, never retroactive-coverage framing, never
// sample data, and never a broken panel (both fetch failures collapse to the
// existing dashboard empty state by rendering nothing).
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import FirstRunBackfillPanel from '../components/app/FirstRunBackfillPanel'
import { BACKFILL_STRINGS } from '../components/app/firstRunBackfillStrings'

const CHANGED_RECORDS = [
  {
    run_id: 'run-3',
    source_id: 'AE-cbuae-rulebook',
    source_name: 'CBUAE Rulebook',
    change_status: 'CHANGED',
    normalized_hash: 'a'.repeat(64),
    timestamp_utc: '2026-07-12T09:00:00Z',
  },
  {
    run_id: 'run-2',
    source_id: 'AE-vara-rulebook',
    source_name: 'VARA Rulebook',
    change_status: 'CHANGED',
    normalized_hash: 'b'.repeat(64),
    timestamp_utc: '2026-07-11T09:00:00Z',
    change_summary: 'Threshold wording updated in section 4.2.',
  },
  {
    run_id: 'run-1',
    source_id: 'AE-sca-regulations',
    source_name: 'SCA Regulations',
    change_status: 'CHANGED',
    normalized_hash: 'c'.repeat(64),
    timestamp_utc: '2026-07-10T09:00:00Z',
  },
  {
    run_id: 'run-0',
    source_id: 'AE-moj-portal',
    source_name: 'MOJ Legislation Portal',
    change_status: 'CHANGED',
    normalized_hash: 'd'.repeat(64),
    timestamp_utc: '2026-07-01T09:00:00Z',
  },
  {
    run_id: 'run-u1',
    source_id: 'AE-uae-gazette',
    source_name: 'UAE Official Gazette',
    change_status: 'UNCHANGED',
    normalized_hash: 'e'.repeat(64),
    timestamp_utc: '2026-07-12T10:00:00Z',
  },
]

function mockFetch({ matches = [], evidence = [], failPreview = false, failEvidence = false } = {}) {
  globalThis.fetch = vi.fn(url => {
    const path = String(url)
    if (path.includes('/api/delivery/preview')) {
      if (failPreview) return Promise.reject(new Error('network down'))
      return Promise.resolve({ ok: true, json: async () => ({ ok: true, preview: { matches } }) })
    }
    if (path.includes('/api/evidence')) {
      if (failEvidence) return Promise.reject(new Error('network down'))
      return Promise.resolve({ ok: true, json: async () => ({ ok: true, evidence }) })
    }
    return Promise.reject(new Error(`unexpected fetch: ${path}`))
  })
}

async function waitForSettled({ expectEvidenceCall = true } = {}) {
  await waitFor(() => {
    const paths = globalThis.fetch.mock.calls.map(call => String(call[0]))
    expect(paths.some(p => p.includes('/api/delivery/preview'))).toBe(true)
    if (expectEvidenceCall) {
      expect(paths.some(p => p.includes('/api/evidence'))).toBe(true)
    }
  })
}

afterEach(() => {
  // NOTE: this jsdom env has NO localStorage global (getWorkspaceProfile's
  // try/catch absorbs that) — profile-dependent tests stub it per-test.
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('FirstRunBackfillPanel', () => {
  it('renders the 3 most recent CHANGED sealed records with hash and verify links', async () => {
    mockFetch({ matches: [], evidence: CHANGED_RECORDS })
    render(<FirstRunBackfillPanel />)

    await waitFor(() => {
      expect(screen.getByText('CBUAE Rulebook')).toBeInTheDocument()
    })
    expect(screen.getByText('VARA Rulebook')).toBeInTheDocument()
    expect(screen.getByText('SCA Regulations')).toBeInTheDocument()

    // Only the 3 most recent CHANGED records — the 4th CHANGED and the
    // UNCHANGED record must not render.
    expect(screen.queryByText('MOJ Legislation Portal')).not.toBeInTheDocument()
    expect(screen.queryByText('UAE Official Gazette')).not.toBeInTheDocument()

    // Short mono record hash (truncated, full value in the title attribute).
    const seal = screen.getByTitle(`sha256:${'a'.repeat(64)}`)
    expect(seal.textContent).toMatch(/^sha256:a+…$/)

    // Every card links to the public verifier.
    const verifyLinks = screen.getAllByRole('link', { name: BACKFILL_STRINGS.verifyLink })
    expect(verifyLinks).toHaveLength(3)
    for (const link of verifyLinks) {
      expect(link).toHaveAttribute('href', '/verify')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    }
  })

  it('renders a one-line change summary only when the record carries one', async () => {
    mockFetch({ matches: [], evidence: CHANGED_RECORDS })
    render(<FirstRunBackfillPanel />)

    await waitFor(() => {
      expect(screen.getByText('Threshold wording updated in section 4.2.')).toBeInTheDocument()
    })
    // Exactly one record in the fixture carries a summary.
    expect(screen.getAllByText(BACKFILL_STRINGS.changeNoteLabel)).toHaveLength(1)
  })

  it('always renders the honest framing and the short disclaimer', async () => {
    mockFetch({ matches: [], evidence: CHANGED_RECORDS })
    render(<FirstRunBackfillPanel />)

    await waitFor(() => {
      expect(screen.getByText(BACKFILL_STRINGS.disclaimer)).toBeInTheDocument()
    })
    expect(screen.getByText(BACKFILL_STRINGS.framing)).toBeInTheDocument()
    // The independence line must state plainly this is NOT retroactive coverage.
    expect(screen.getByText(/not monitoring coverage of any period before you signed up/i)).toBeInTheDocument()
    expect(screen.getByText(/independently of your account/i)).toBeInTheDocument()
  })

  it('shows the honest empty state (with disclaimer) when no CHANGED records exist', async () => {
    mockFetch({ matches: [], evidence: [CHANGED_RECORDS[4]] }) // UNCHANGED only
    render(<FirstRunBackfillPanel />)

    await waitFor(() => {
      expect(screen.getByText(BACKFILL_STRINGS.empty)).toBeInTheDocument()
    })
    expect(screen.getByText(BACKFILL_STRINGS.disclaimer)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: BACKFILL_STRINGS.verifyLink })).not.toBeInTheDocument()
  })

  it('renders nothing when the user already has alerts', async () => {
    mockFetch({ matches: [{ alert_id: 'a-1' }], evidence: CHANGED_RECORDS })
    const { container } = render(<FirstRunBackfillPanel />)

    await waitForSettled({ expectEvidenceCall: false })
    expect(container.firstChild).toBeNull()
    // It must not even fetch evidence when alerts exist.
    const paths = globalThis.fetch.mock.calls.map(call => String(call[0]))
    expect(paths.some(p => p.includes('/api/evidence'))).toBe(false)
  })

  it('renders nothing when the alerts preview fetch fails (quiet fallback)', async () => {
    mockFetch({ failPreview: true })
    const { container } = render(<FirstRunBackfillPanel />)

    await waitForSettled({ expectEvidenceCall: false })
    await waitFor(() => expect(container.firstChild).toBeNull())
  })

  it('renders nothing when the evidence fetch fails (quiet fallback, no broken panel)', async () => {
    mockFetch({ matches: [], failEvidence: true })
    const { container } = render(<FirstRunBackfillPanel />)

    await waitForSettled()
    await waitFor(() => expect(container.firstChild).toBeNull())
  })

  it('labels the scope honestly when no profile market is saved', async () => {
    mockFetch({ matches: [], evidence: CHANGED_RECORDS })
    render(<FirstRunBackfillPanel />)

    await waitFor(() => {
      expect(screen.getByText(BACKFILL_STRINGS.scopeFallback)).toBeInTheDocument()
    })
    expect(screen.queryByText(BACKFILL_STRINGS.scopeScoped)).not.toBeInTheDocument()
  })

  it('labels the scope as selected when the saved profile resolves to one market', async () => {
    vi.stubGlobal('localStorage', {
      getItem: () => JSON.stringify({ markets: ['UAE', 'DIFC'] }),
    })
    mockFetch({ matches: [], evidence: CHANGED_RECORDS })
    render(<FirstRunBackfillPanel />)

    await waitFor(() => {
      expect(screen.getByText(BACKFILL_STRINGS.scopeScoped)).toBeInTheDocument()
    })
    // The evidence request is filtered to the resolved market code.
    const evidenceCall = globalThis.fetch.mock.calls.map(call => String(call[0])).find(p => p.includes('/api/evidence'))
    expect(evidenceCall).toContain('market=AE')
  })

  it('carries no forbidden claims in ANY authored string or rendered output', async () => {
    // Project forbidden-claims list (CLAUDE.md) plus retroactive-coverage
    // phrases this specific panel must never drift into.
    const FORBIDDEN = [
      'guarantee compliance',
      'guarantees compliance',
      'prevent fines',
      'ai lawyer',
      '100% accurate',
      'never miss',
      'stay compliant automatically',
      'avoid all penalties',
      'proof of compliance',
      'we handle compliance',
      'replace lawyers',
      'automatic legal advice',
      'retroactive',
      'you were covered',
      'covered since',
      'full coverage',
    ]

    // Scan the full authored string set, including strings a given render
    // path might not show.
    for (const [key, value] of Object.entries(BACKFILL_STRINGS)) {
      const text = value.toLowerCase()
      for (const phrase of FORBIDDEN) {
        expect(text, `forbidden phrase in BACKFILL_STRINGS.${key}: "${phrase}"`).not.toContain(phrase)
      }
    }

    // And scan the populated render (record cards + framing + disclaimer).
    mockFetch({ matches: [], evidence: CHANGED_RECORDS })
    const { container } = render(<FirstRunBackfillPanel />)
    await waitFor(() => {
      expect(screen.getByText('CBUAE Rulebook')).toBeInTheDocument()
    })
    const rendered = container.textContent.toLowerCase()
    for (const phrase of FORBIDDEN) {
      expect(rendered, `forbidden phrase rendered: "${phrase}"`).not.toContain(phrase)
    }
  })
})
