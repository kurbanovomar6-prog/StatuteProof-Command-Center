// The detected-date calendar is a MONITORING view: it must render every date
// with the honest "detected in the changed text, verify against source" framing
// and the disclaimer, and its .ics export must never phrase a date as the
// reader's obligation ("you must", "deadline: ...").
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import EffectiveDatesCalendar from '../components/app/EffectiveDatesCalendar'
import {
  buildEffectiveDatesIcs,
  eventDescription,
  eventSummary,
} from '../utils/ics'

const DATE_ITEM = {
  date: '2026-09-01',
  detected_type: 'effective_date',
  type_label: 'effective date',
  raw_date_text: '1 September 2026',
  date_ambiguous: false,
  excerpt: 'The revised capital rules are effective from 1 September 2026.',
  source_id: 'cbuae',
  source_name: 'CBUAE Rulebook',
  regulator: 'CBUAE',
  official_url: 'https://www.cbuae.gov.ae/example',
  evidence_record_id: 'evr_cbuae_1',
  record_hash: 'sha256:sealedhashvalue0123',
  captured_at: '2026-07-01T09:00:00Z',
  days_until: 62,
  framing:
    'A date StatuteProof detected in the changed text of CBUAE Rulebook on 2026-07-01. ' +
    'This is a monitoring signal to help a reviewer decide what to check. Verify against the official source.',
  disclaimer: 'For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

const PAYLOAD = {
  ok: true,
  dates: [DATE_ITEM],
  count: 1,
  horizon: { from: '2026-07-01', to: '2026-09-29', days: 90 },
  framing: 'These are dates StatuteProof detected in the changed text of monitored official sources.',
  disclaimer: 'For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

function mockJson(payload, ok = true) {
  globalThis.fetch = vi.fn().mockResolvedValue({ ok, status: ok ? 200 : 500, json: async () => payload })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('EffectiveDatesCalendar', () => {
  it('renders detected dates with the honest framing and disclaimer', async () => {
    mockJson(PAYLOAD)
    render(<EffectiveDatesCalendar />)

    // The detected date + source render.
    expect(await screen.findByText('CBUAE Rulebook')).toBeInTheDocument()
    expect(screen.getByText(/effective date/i)).toBeInTheDocument()
    // The honest header framing is present (a monitoring signal, not the reader's
    // legal deadline).
    expect(screen.getByText(/not your legal deadline/i)).toBeInTheDocument()
    // The detected excerpt is shown as source-detected text.
    expect(screen.getByText(/detected in changed text/i)).toBeInTheDocument()
    // The verification pointer (sealed record) is surfaced.
    expect(screen.getByText(/evr_cbuae_1/)).toBeInTheDocument()
    expect(screen.getByText(/sha256:sealedhashval/)).toBeInTheDocument()
    // The disclaimer rides on the view.
    expect(
      screen.getByText(/not legal advice and not a guarantee of compliance/i),
    ).toBeInTheDocument()
  })

  it('shows an honest empty state that makes no completeness claim', async () => {
    mockJson({ ...PAYLOAD, dates: [], count: 0 })
    render(<EffectiveDatesCalendar />)

    expect(await screen.findByText(/no dates were detected/i)).toBeInTheDocument()
    expect(screen.getByText(/best-effort detection over monitored sources only/i)).toBeInTheDocument()
    // The export button is disabled when there is nothing to export.
    expect(screen.getByRole('button', { name: /export \.ics/i })).toBeDisabled()
  })

  it('shows an error state when the calendar request fails', async () => {
    mockJson({ ok: false, message: 'Internal server error.' }, false)
    render(<EffectiveDatesCalendar />)
    expect(await screen.findByText(/internal server error/i)).toBeInTheDocument()
  })

  it('exports a downloadable .ics on click', async () => {
    mockJson(PAYLOAD)
    const createUrl = vi.fn().mockReturnValue('blob:mock')
    const revokeUrl = vi.fn()
    globalThis.URL.createObjectURL = createUrl
    globalThis.URL.revokeObjectURL = revokeUrl
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    render(<EffectiveDatesCalendar />)
    await screen.findByText('CBUAE Rulebook')
    fireEvent.click(screen.getByRole('button', { name: /export \.ics/i }))

    expect(createUrl).toHaveBeenCalledTimes(1)
    expect(clickSpy).toHaveBeenCalledTimes(1)
  })
})

describe('buildEffectiveDatesIcs', () => {
  it('produces a standards-valid VCALENDAR with an all-day VEVENT', () => {
    const ics = buildEffectiveDatesIcs([DATE_ITEM])
    expect(ics.startsWith('BEGIN:VCALENDAR')).toBe(true)
    expect(ics).toContain('VERSION:2.0')
    expect(ics).toContain('PRODID:-//StatuteProof//Effective-Date Calendar//EN')
    expect(ics).toContain('BEGIN:VEVENT')
    expect(ics).toContain('DTSTART;VALUE=DATE:20260901')
    expect(ics).toContain('END:VEVENT')
    expect(ics).toContain('END:VCALENDAR')
    // CRLF line endings per RFC 5545.
    expect(ics.includes('\r\n')).toBe(true)
  })

  it('never phrases an event as the reader’s obligation', () => {
    // Unfold RFC 5545 continuation lines (CRLF + space/tab) before asserting on
    // content — folding is a transport encoding, not part of the text.
    const ics = buildEffectiveDatesIcs([DATE_ITEM]).replace(/\r\n[ \t]/g, '').toLowerCase()
    expect(ics).not.toContain('you must')
    expect(ics).not.toContain('deadline: you')
    expect(ics).not.toContain('action required')
    // The honest signal wording IS present.
    expect(ics).toContain('detected')
    // The disclaimer rides in the description.
    expect(ics).toContain('not legal advice and not a guarantee of compliance')
  })

  it('summary and description carry the honest framing', () => {
    expect(eventSummary(DATE_ITEM)).toBe('StatuteProof-detected effective date (verify) — CBUAE Rulebook')
    const desc = eventDescription(DATE_ITEM).toLowerCase()
    expect(desc).toContain('detected in the changed text')
    expect(desc).toContain('evidence record: evr_cbuae_1')
    expect(desc).toContain('record hash: sha256:sealedhashvalue')
    expect(desc).not.toContain('you must')
  })

  it('escapes RFC 5545 special characters and skips dateless items', () => {
    const tricky = { ...DATE_ITEM, source_name: 'A; B, C\\ D', date: '' }
    const ics = buildEffectiveDatesIcs([tricky, DATE_ITEM])
    // The dateless item is skipped — exactly one VEVENT survives.
    expect(ics.match(/BEGIN:VEVENT/g)).toHaveLength(1)
  })
})
