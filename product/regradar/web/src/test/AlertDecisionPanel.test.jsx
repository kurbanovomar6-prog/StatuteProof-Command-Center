// The sealed decision panel renders the reviewer's OWN sign-off timeline for one
// alert (their words verbatim, sealed server-side into an append-only chain),
// gates sealing behind an explicit irreversibility confirm step, supports
// corrections as NEW linked entries, and degrades honestly to read-only when the
// caller's role may not seal (403). All framing is server-authored copy rendered
// verbatim; the fallback here matches app/decision_records.py FRAMING.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'

import AlertDecisionPanel from '../components/app/AlertDecisionPanel'

const ALERT = 'draft-cbuae001'

const FRAMING = {
  title: 'Your decision record',
  subtitle:
    'Seal your own review decision for this change into the evidence record. You author the wording; StatuteProof records and time-stamps it, unchanged.',
  empty:
    'No sealed decisions yet. When you have reviewed this change, you can record your own decision and seal it into the evidence record.',
  statement_label: 'Your decision, in your own words',
  statement_placeholder: 'Record what you reviewed and the decision you are making.',
  kind_label: 'How you want to log this',
  seal_button: 'Seal my decision',
  confirm_title: 'Seal this decision?',
  confirm_body:
    'Once sealed, this decision is time-stamped and cannot be edited. If you need to correct it later, you can add a new, linked entry — the original stays in the record.',
  amend_button: 'Record a correction',
  amend_note:
    'This adds a new sealed entry that references the earlier one. The earlier decision remains unchanged in the record.',
  who_note:
    'Your name and account are recorded with the decision so the record shows who reviewed it.',
  disclaimer:
    'You author this decision; StatuteProof records your words without changing them and does not review, suggest, or assess the decision. For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

const KINDS = ['reviewed', 'acknowledged', 'escalated', 'no_change_needed', 'action_recorded']

function decisionRecord({ id = 'dec_1_1_abcdef1234567890abcd', statement = 'I reviewed the diff against our licence scope.', kind = 'reviewed', supersedes = null, reason = null } = {}) {
  return {
    schema_version: '1.0',
    decision_id: id,
    record_hash: 'sha256:' + 'a'.repeat(64),
    record_hash_method: 'content-sha256-v1',
    content: {
      decision_id: id,
      org_id: 1,
      chain_seq: 1,
      prev_decision_hash: '',
      decided_by: { user_id: 7, display_name: 'A. Rahman' },
      decided_at_utc: '2026-07-12T09:30:00.000000Z',
      reviewed: { alert_id: ALERT },
      decision: { kind, statement, checklist_ref: null },
      supersedes_decision_id: supersedes,
      amendment_reason: reason,
    },
  }
}

function mockFetch({ decisions = [], onSeal, sealStatus = 201, sealResponse } = {}) {
  globalThis.fetch = vi.fn((url, options = {}) => {
    const method = (options.method || 'GET').toUpperCase()
    if (String(url).includes('/api/alerts/decisions') && method === 'POST') {
      const body = JSON.parse(options.body || '{}')
      if (onSeal) onSeal(body)
      if (sealStatus >= 400) {
        return Promise.resolve({
          ok: false,
          status: sealStatus,
          json: async () => sealResponse || { ok: false, message: 'Your role does not permit this action.' },
        })
      }
      return Promise.resolve({
        ok: true,
        status: sealStatus,
        json: async () => ({
          ok: true,
          decision: decisionRecord({
            id: 'dec_1_2_feedfacefeedfacefeed',
            statement: body.statement,
            kind: body.kind,
            supersedes: body.supersedes_decision_id || null,
            reason: body.amendment_reason || null,
          }),
        }),
      })
    }
    // GET list
    return Promise.resolve({
      ok: true,
      status: 200,
      json: async () => ({ ok: true, decisions, framing: FRAMING, kinds: KINDS, chain: null }),
    })
  })
}

function openPanel() {
  fireEvent.click(screen.getByRole('button', { name: /your decision record/i }))
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AlertDecisionPanel', () => {
  it('mounts lazily — nothing is fetched until the panel is opened', async () => {
    mockFetch({ decisions: [] })
    render(<AlertDecisionPanel alertId={ALERT} />)
    expect(globalThis.fetch).not.toHaveBeenCalled()

    openPanel()
    expect(await screen.findByText(/no sealed decisions yet/i)).toBeInTheDocument()
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
  })

  it('renders a sealed entry: kind label, verbatim statement, reviewer, short hash, verify link', async () => {
    mockFetch({ decisions: [decisionRecord()] })
    render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()

    const entry = (
      await screen.findByText('I reviewed the diff against our licence scope.')
    ).closest('li')
    expect(within(entry).getByText('Reviewed')).toBeInTheDocument()
    expect(within(entry).getByText('A. Rahman')).toBeInTheDocument()
    expect(within(entry).getByText(`sha256:${'a'.repeat(19)}…`)).toBeInTheDocument()
    const verify = screen.getByRole('link', { name: /verify independently/i })
    expect(verify).toHaveAttribute('href', '/verify')
    expect(verify).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('always renders the server framing and disclaimer verbatim', async () => {
    mockFetch({ decisions: [] })
    render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()

    expect(await screen.findByText(FRAMING.subtitle)).toBeInTheDocument()
    expect(screen.getByText(FRAMING.disclaimer)).toBeInTheDocument()
    expect(screen.getByText(FRAMING.who_note)).toBeInTheDocument()
  })

  it('sealing requires the explicit irreversibility confirm step, then posts', async () => {
    const sealed = []
    mockFetch({ decisions: [], onSeal: body => sealed.push(body) })
    render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText(/no sealed decisions yet/i)

    fireEvent.change(screen.getByLabelText(FRAMING.statement_label), {
      target: { value: 'Reviewed; no licence impact identified.' },
    })
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))

    // Nothing posted yet — the confirm step is shown first.
    expect(sealed).toEqual([])
    expect(screen.getByText(FRAMING.confirm_title)).toBeInTheDocument()
    expect(screen.getByText(FRAMING.confirm_body)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))
    await waitFor(() =>
      expect(sealed).toEqual([
        { alert_id: ALERT, kind: 'reviewed', statement: 'Reviewed; no licence impact identified.' },
      ]),
    )
    expect(await screen.findByText('Reviewed; no licence impact identified.')).toBeInTheDocument()
  })

  it('"Go back" cancels the confirm step without posting', async () => {
    const sealed = []
    mockFetch({ decisions: [], onSeal: body => sealed.push(body) })
    render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText(/no sealed decisions yet/i)

    fireEvent.change(screen.getByLabelText(FRAMING.statement_label), {
      target: { value: 'A statement I am not ready to seal.' },
    })
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))
    fireEvent.click(screen.getByRole('button', { name: /go back/i }))

    expect(sealed).toEqual([])
    expect(screen.queryByText(FRAMING.confirm_title)).not.toBeInTheDocument()
  })

  it('recording a correction posts supersedes + the reason, and keeps the original', async () => {
    const sealed = []
    mockFetch({ decisions: [decisionRecord()], onSeal: body => sealed.push(body) })
    render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText('I reviewed the diff against our licence scope.')

    fireEvent.click(screen.getByRole('button', { name: FRAMING.amend_button }))
    expect(screen.getByText(FRAMING.amend_note)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText(FRAMING.statement_label), {
      target: { value: 'Section 4 does affect our reporting form.' },
    })
    fireEvent.change(
      screen.getByLabelText(/your reason for the correction, in your own words/i),
      { target: { value: 'I misread the scope of section 4.' } },
    )
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))

    await waitFor(() =>
      expect(sealed).toEqual([
        {
          alert_id: ALERT,
          kind: 'reviewed',
          statement: 'Section 4 does affect our reporting form.',
          supersedes_decision_id: 'dec_1_1_abcdef1234567890abcd',
          amendment_reason: 'I misread the scope of section 4.',
        },
      ]),
    )
    // The original entry stays; the correction is appended and linked.
    expect(screen.getByText('I reviewed the diff against our licence scope.')).toBeInTheDocument()
    expect(await screen.findByText('Section 4 does affect our reporting form.')).toBeInTheDocument()
    expect(screen.getByText(/a later correction references this entry/i)).toBeInTheDocument()
  })

  it('a 403 on seal switches the panel to an honest read-only state', async () => {
    mockFetch({ decisions: [decisionRecord()], sealStatus: 403 })
    render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText('I reviewed the diff against our licence scope.')

    fireEvent.change(screen.getByLabelText(FRAMING.statement_label), {
      target: { value: 'An auditor attempting to seal.' },
    })
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))

    expect(
      await screen.findByText(/this decision record is read-only for your role/i),
    ).toBeInTheDocument()
    // The compose form is gone; the sealed timeline stays readable.
    expect(screen.queryByLabelText(FRAMING.statement_label)).not.toBeInTheDocument()
    expect(screen.getByText('I reviewed the diff against our licence scope.')).toBeInTheDocument()
  })

  it('a validation failure keeps the form and shows the server message', async () => {
    mockFetch({
      decisions: [],
      sealStatus: 400,
      sealResponse: { ok: false, message: 'The decision could not be sealed. Nothing was recorded — check the entry and try again.' },
    })
    render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText(/no sealed decisions yet/i)

    fireEvent.change(screen.getByLabelText(FRAMING.statement_label), {
      target: { value: 'A statement the server rejects.' },
    })
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))

    expect(await screen.findByText(/nothing was recorded/i)).toBeInTheDocument()
    expect(screen.getByLabelText(FRAMING.statement_label)).toBeInTheDocument()
  })

  it('an over-limit statement blocks sealing — the words are never truncated', async () => {
    const sealed = []
    mockFetch({ decisions: [], onSeal: body => sealed.push(body) })
    render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText(/no sealed decisions yet/i)

    fireEvent.change(screen.getByLabelText(FRAMING.statement_label), {
      target: { value: 'x'.repeat(4001) },
    })
    expect(screen.getByRole('button', { name: FRAMING.seal_button })).toBeDisabled()
    expect(screen.getByText(/your words are never shortened for you/i)).toBeInTheDocument()
    expect(sealed).toEqual([])
  })

  it('a drafted statement never carries over to another alert', async () => {
    // A sealed record is irreversible — words typed for one alert must be
    // cleared when the panel is re-bound to a different alert.
    mockFetch({ decisions: [] })
    const { rerender } = render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText(/no sealed decisions yet/i)

    fireEvent.change(screen.getByLabelText(FRAMING.statement_label), {
      target: { value: 'Words meant for the first alert.' },
    })

    rerender(<AlertDecisionPanel alertId="draft-other002" />)
    openPanel() // the panel collapsed on the alert change; open it again
    await screen.findByText(/no sealed decisions yet/i)
    expect(screen.getByLabelText(FRAMING.statement_label)).toHaveValue('')
  })

  it('frontend-only strings carry no forbidden claims', async () => {
    // Server copy is guarded at import (app/legal_safety); the strings authored
    // only in this JSX bypass that gate, so guard them here (legal-review
    // process note, 2026-07-12 — mirrors AlertRedline.test.jsx).
    const FORBIDDEN = [
      'guarantee compliance',
      'prevent fines',
      'ai lawyer',
      '100% accurate',
      'never miss',
      'stay compliant automatically',
      'avoid all penalties',
      'proof of compliance',
    ]
    mockFetch({
      decisions: [
        decisionRecord(),
        decisionRecord({
          id: 'dec_1_2_feedfacefeedfacefeed',
          statement: 'Corrected entry.',
          supersedes: 'dec_1_1_abcdef1234567890abcd',
          reason: 'Earlier entry misread the scope.',
        }),
      ],
    })
    const { container } = render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText('Corrected entry.')
    fireEvent.click(screen.getAllByRole('button', { name: FRAMING.amend_button })[0])

    const text = container.textContent.toLowerCase()
    for (const phrase of FORBIDDEN) {
      expect(text, `forbidden phrase rendered: "${phrase}"`).not.toContain(phrase)
    }
  })

  it('app-authored copy never recommends, suggests, or scores a decision', async () => {
    // Iron legal guardrail (CLAUDE.md): StatuteProof records the reviewer's OWN
    // words and NEVER prescribes, suggests, scores, or assesses the decision. The
    // forbidden-claims sweep above catches banned marketing phrases; this asserts
    // the panel's own copy carries no PRESCRIPTIVE / advisory framing that would
    // read as the app steering the decision. Phrases are imperative recommendation
    // forms only — the disclaimer's negated "does not review, suggest, or assess"
    // is legitimate and must not trip this, so we never test the bare words
    // "suggest" / "assess" / "score" in isolation.
    const RECOMMENDATION_STYLE = [
      'we recommend',
      'you should',
      'we suggest',
      'we advise',
      'advise you',
      'recommended action',
      'suggested action',
      'our recommendation',
      'you must',
      'best course',
      'the right decision',
      'the correct decision',
    ]
    mockFetch({
      decisions: [
        decisionRecord(),
        decisionRecord({
          id: 'dec_1_2_feedfacefeedfacefeed',
          statement: 'Corrected entry.',
          supersedes: 'dec_1_1_abcdef1234567890abcd',
          reason: 'Earlier entry misread the scope.',
        }),
      ],
    })
    const { container } = render(<AlertDecisionPanel alertId={ALERT} />)
    openPanel()
    await screen.findByText('Corrected entry.')

    // Reveal the compose + irreversibility-confirm copy too (both app-authored).
    fireEvent.change(screen.getByLabelText(FRAMING.statement_label), {
      target: { value: 'Reviewed; recording my own decision.' },
    })
    fireEvent.click(screen.getByRole('button', { name: FRAMING.seal_button }))
    expect(screen.getByText(FRAMING.confirm_title)).toBeInTheDocument()

    const text = container.textContent.toLowerCase()
    for (const phrase of RECOMMENDATION_STYLE) {
      expect(text, `recommendation-style copy rendered: "${phrase}"`).not.toContain(phrase)
    }
  })
})
