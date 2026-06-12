import { useState, useEffect, useCallback } from 'react'
import { plan as planApi } from '../api'

const DEFAULT_STATE = {
  plan_name: 'evidence_preview',
  plan_display: 'Evidence Preview',
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

  useEffect(() => { load() }, [load])

  async function selectPlan(planName) {
    try {
      const data = await planApi.set(planName)
      if (data.ok && data.plan) {
        setPlanState(data.plan)
      }
      return data
    } catch (err) {
      throw err
    }
  }

  return { planState, loading, selectPlan, reload: load }
}
