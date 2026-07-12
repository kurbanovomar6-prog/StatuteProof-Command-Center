// The per-alert review checklist is the user's OWN to-do list: it renders their
// items, ticking toggles an item done, adding an action posts and appends it, and
// the empty state + disclaimer frame it honestly as monitoring workflow (never
// StatuteProof-authored compliance advice).
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'

import AlertChecklistPanel from '../components/app/AlertChecklistPanel'

const ALERT = 'draft-cbuae001'

const FRAMING = {
  title: 'Your review checklist',
  subtitle: 'Review actions you choose to track for this alert.',
  add_label: 'Add a review action',
  add_placeholder: 'Describe a review step you want to track',
  empty: 'No review actions yet. Add the steps you choose to track for this alert.',
  disclaimer:
    'You author these items. For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

function item(overrides = {}) {
  return {
    id: 1,
    alert_id: ALERT,
    text: 'Review the reporting form change',
    assignee: 'MLRO',
    due_date: '2026-09-01',
    status: 'open',
    created_at: '2026-07-12T10:00:00Z',
    updated_at: '2026-07-12T10:00:00Z',
    ...overrides,
  }
}

function mockFetch({ items = [], onAdd, onUpdate } = {}) {
  globalThis.fetch = vi.fn((url, options = {}) => {
    const target = String(url)
    const method = (options.method || 'GET').toUpperCase()
    if (target.includes('/api/alerts/checklist/update')) {
      const body = JSON.parse(options.body || '{}')
      if (onUpdate) onUpdate(body)
      if (body.delete) return Promise.resolve({ ok: true, json: async () => ({ ok: true, deleted: body.item_id }) })
      return Promise.resolve({
        ok: true,
        json: async () => ({ ok: true, item: { ...item(), ...body, status: body.status || 'open' } }),
      })
    }
    if (target.includes('/api/alerts/checklist') && method === 'POST') {
      const body = JSON.parse(options.body || '{}')
      if (onAdd) onAdd(body)
      return Promise.resolve({
        ok: true,
        json: async () => ({ ok: true, item: item({ id: 99, text: body.text, assignee: body.assignee, due_date: body.due_date }) }),
      })
    }
    // GET list
    return Promise.resolve({ ok: true, json: async () => ({ ok: true, items, framing: FRAMING }) })
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AlertChecklistPanel', () => {
  it('renders the user\'s own items with assignee and due date', async () => {
    mockFetch({ items: [item()] })
    render(<AlertChecklistPanel alertId={ALERT} />)

    expect(await screen.findByText('Review the reporting form change')).toBeInTheDocument()
    expect(screen.getByText('MLRO')).toBeInTheDocument()
    expect(screen.getByText('2026-09-01')).toBeInTheDocument()
    expect(screen.getByText('Your review checklist')).toBeInTheDocument()
  })

  it('shows the honest empty state when there are no items', async () => {
    mockFetch({ items: [] })
    render(<AlertChecklistPanel alertId={ALERT} />)

    expect(
      await screen.findByText('No review actions yet. Add the steps you choose to track for this alert.'),
    ).toBeInTheDocument()
    // Framing describes the USER's own actions — no prescriptive compliance copy.
    expect(screen.getByText('Review actions you choose to track for this alert.')).toBeInTheDocument()
  })

  it('always renders the monitoring-only disclaimer', async () => {
    mockFetch({ items: [] })
    render(<AlertChecklistPanel alertId={ALERT} />)

    expect(
      await screen.findByText(/for monitoring information only\. not legal advice and not a guarantee of compliance\./i),
    ).toBeInTheDocument()
  })

  it('ticking an item toggles it to done', async () => {
    const updates = []
    mockFetch({ items: [item()], onUpdate: body => updates.push(body) })
    render(<AlertChecklistPanel alertId={ALERT} />)

    const checkbox = await screen.findByRole('checkbox', { name: /mark .* as done/i })
    expect(checkbox).toHaveAttribute('aria-checked', 'false')
    fireEvent.click(checkbox)

    await waitFor(() => expect(updates).toEqual([{ item_id: 1, status: 'done' }]))
    await waitFor(() =>
      expect(screen.getByRole('checkbox', { name: /mark .* as not done/i })).toHaveAttribute('aria-checked', 'true'),
    )
  })

  it('adding an action posts it and appends it to the list', async () => {
    const added = []
    mockFetch({ items: [], onAdd: body => added.push(body) })
    render(<AlertChecklistPanel alertId={ALERT} />)

    await screen.findByText(/no review actions yet/i)
    fireEvent.change(screen.getByLabelText('Add a review action'), {
      target: { value: 'Check the effective date' },
    })
    fireEvent.click(screen.getByRole('button', { name: /add action/i }))

    await waitFor(() =>
      expect(added).toEqual([
        { alert_id: ALERT, text: 'Check the effective date', assignee: '', due_date: '' },
      ]),
    )
    expect(await screen.findByText('Check the effective date')).toBeInTheDocument()
  })

  it('deleting an item removes it from the list', async () => {
    const updates = []
    mockFetch({ items: [item()], onUpdate: body => updates.push(body) })
    render(<AlertChecklistPanel alertId={ALERT} />)

    const row = (await screen.findByText('Review the reporting form change')).closest('li')
    fireEvent.click(within(row).getByRole('button', { name: /delete/i }))

    await waitFor(() => expect(updates).toEqual([{ item_id: 1, delete: true }]))
    await waitFor(() =>
      expect(screen.queryByText('Review the reporting form change')).not.toBeInTheDocument(),
    )
  })
})
