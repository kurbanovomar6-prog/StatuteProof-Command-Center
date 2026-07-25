// Seating a colleague used to require a founder SSH session. This panel is the
// door. The tests below pin the two things that would silently make it a lie:
// a non-owner must be told they cannot manage the team rather than shown a form
// that 403s, and an address with no account must say so rather than reading as
// success and leaving the owner waiting for a colleague who was never added.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

import TeamPanel from '../components/app/TeamPanel'

const mocks = vi.hoisted(() => ({
  members: vi.fn(),
  add: vi.fn(),
  revoke: vi.fn(),
}))

vi.mock('../api', () => ({
  team: {
    members: mocks.members,
    add: mocks.add,
    revoke: mocks.revoke,
  },
}))

function roster(members) {
  return { ok: true, org_id: 2, members }
}

const OWNER = { user_id: 1, email: 'owner@firm.example', role: 'owner' }
const MATE = { user_id: 2, email: 'mate@firm.example', role: 'auditor' }

function refused(status) {
  const err = new Error('Not permitted.')
  err.status = status
  return err
}

afterEach(() => {
  vi.clearAllMocks()
})

describe('TeamPanel', () => {
  it('lists the workspace members', async () => {
    mocks.members.mockResolvedValue(roster([OWNER, MATE]))

    render(<TeamPanel />)

    expect(await screen.findByText('owner@firm.example')).toBeInTheDocument()
    expect(screen.getByText('mate@firm.example')).toBeInTheDocument()
  })

  it('tells a non-owner they cannot manage the team, with no form', async () => {
    mocks.members.mockRejectedValue(refused(403))

    render(<TeamPanel />)

    expect(
      await screen.findByText(/only the workspace owner can add or remove people/i),
    ).toBeInTheDocument()
    expect(screen.queryByPlaceholderText(/colleague@/i)).not.toBeInTheDocument()
  })

  it('adds a colleague and refreshes the roster', async () => {
    mocks.members
      .mockResolvedValueOnce(roster([OWNER]))
      .mockResolvedValueOnce(roster([OWNER, MATE]))
    mocks.add.mockResolvedValue({ ok: true, user_id: 2, role: 'auditor' })

    render(<TeamPanel />)
    await screen.findByText('owner@firm.example')

    fireEvent.change(screen.getByPlaceholderText(/colleague@/i), {
      target: { value: 'mate@firm.example' },
    })
    fireEvent.click(screen.getByRole('button', { name: /add/i }))

    await waitFor(() =>
      expect(mocks.add).toHaveBeenCalledWith('mate@firm.example', 'auditor'),
    )
    expect(await screen.findByText('mate@firm.example')).toBeInTheDocument()
  })

  it('says an unregistered address must sign up first', async () => {
    mocks.members.mockResolvedValue(roster([OWNER]))
    mocks.add.mockRejectedValue(refused(404))

    render(<TeamPanel />)
    await screen.findByText('owner@firm.example')

    fireEvent.change(screen.getByPlaceholderText(/colleague@/i), {
      target: { value: 'nobody@firm.example' },
    })
    fireEvent.click(screen.getByRole('button', { name: /add/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/register first/i)
  })

  it('offers no way to remove the owner', async () => {
    mocks.members.mockResolvedValue(roster([OWNER, MATE]))

    render(<TeamPanel />)
    await screen.findByText('owner@firm.example')

    expect(
      screen.queryByRole('button', { name: /remove owner@firm\.example/i }),
    ).not.toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /remove mate@firm\.example/i }),
    ).toBeInTheDocument()
  })

  it('revokes a seat', async () => {
    mocks.members
      .mockResolvedValueOnce(roster([OWNER, MATE]))
      .mockResolvedValueOnce(roster([OWNER]))
    mocks.revoke.mockResolvedValue({ ok: true, removed: true })

    render(<TeamPanel />)
    await screen.findByText('mate@firm.example')

    fireEvent.click(screen.getByRole('button', { name: /remove mate@firm\.example/i }))

    await waitFor(() =>
      expect(mocks.revoke).toHaveBeenCalledWith('mate@firm.example'),
    )
    await waitFor(() =>
      expect(screen.queryByText('mate@firm.example')).not.toBeInTheDocument(),
    )
  })
})
