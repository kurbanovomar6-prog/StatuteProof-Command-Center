// The word the customer reads before deciding whether they are covered.
//
// `statusFromApiSource` used to fall through to "Readiness supported" for any
// source with a successful run, regardless of when that run happened. Measured
// 2026-07-25: every alert-eligible source asserted MONITOR_OK with a median
// recorded check age of 36 days, so "Readiness supported" was being shown for
// checks over a month old.
//
// These tests pin the two properties the fix has to keep: a stale check never
// reads as supported, and the age is stated rather than implied.

import { describe, it, expect } from 'vitest'
import { statusFromApiSource, checkAgeLabel } from '../components/app/SourcesPage'

const RECENT = '2026-07-25T09:00:00Z'

describe('statusFromApiSource', () => {
  it('reports a freshly checked source as supported', () => {
    expect(statusFromApiSource({
      source_id: 'AE-x', last_run_at: RECENT, change_status: 'UNCHANGED', freshness: 'FRESH',
    })).toBe('Readiness supported')
  })

  it('never calls a stale check "Readiness supported"', () => {
    const label = statusFromApiSource({
      source_id: 'AE-x', last_run_at: '2026-06-19T09:00:00Z',
      change_status: 'UNCHANGED', freshness: 'STALE',
    })
    expect(label).toBe('Check overdue')
    expect(label).not.toBe('Readiness supported')
  })

  it('treats an unreadable check date as overdue, not as supported', () => {
    expect(statusFromApiSource({
      source_id: 'AE-x', last_run_at: 'garbage', change_status: 'UNCHANGED', freshness: 'UNKNOWN',
    })).toBe('Check overdue')
  })

  it('reports a source that has never run as not started', () => {
    expect(statusFromApiSource({
      source_id: 'AE-x', last_run_at: null, change_status: 'NOT_RUN', freshness: 'NEVER_RUN',
    })).toBe('Monitoring not started')
  })

  it('keeps remediation ahead of freshness — a broken source is not merely overdue', () => {
    expect(statusFromApiSource({
      source_id: 'AE-x', last_run_at: RECENT, change_status: 'FAILED', freshness: 'FRESH',
    })).toBe('Needs remediation')
  })
})

describe('checkAgeLabel', () => {
  it('states how many days ago the check happened', () => {
    expect(checkAgeLabel({ last_run_age_days: 36 })).toBe('checked 36 days ago')
  })

  it('says today rather than "0 days ago"', () => {
    expect(checkAgeLabel({ last_run_age_days: 0.2 })).toBe('checked today')
  })

  it('uses the singular for one day', () => {
    expect(checkAgeLabel({ last_run_age_days: 1.2 })).toBe('checked 1 day ago')
  })

  it('returns nothing when the age is unknown, rather than inventing one', () => {
    expect(checkAgeLabel({ last_run_age_days: null })).toBeNull()
    expect(checkAgeLabel({})).toBeNull()
  })
})
