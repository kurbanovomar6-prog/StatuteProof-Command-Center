import { useState, useEffect, useCallback } from 'react'
import { plan as planApi } from '../api'

const DEFAULT_STATE = {
  plan_name: 'evidence_preview',
  plan_display: 'Source Readiness Review',
  trial_active: false,
  trial_expired: false,
  days_remaining: 7,
  status: 'evidence_preview',
  capabilities: {
    liveMonitoring: false,
    sourceLimit: 0,
    customSources: 0,
    weeklyBriefs: false,
    auditExport: false,
    pdfExport: false,
    users: 1,
    retentionDays: 0,
  },
}

export function usePlan() {
  const [planState, setPlanState] = useState(DEFAULT_STATE)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const data = await planApi.get()
      if (data.ok && data.plan) {
        setPlanState(data.plan)
      }
    } catch {
      // Silent fallback — use default evidence_preview state
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => { load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  async function selectPlan(planName) {
    const data = await planApi.set(planName)
    if (data.ok && data.plan) {
      setPlanState(data.plan)
    }
    return data
  }

  return { planState, loading, selectPlan, reload: load }
}
