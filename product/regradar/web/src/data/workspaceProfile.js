// Shared workspace profile utilities — read localStorage and filter mock data.

export function getWorkspaceProfile() {
  try {
    const p = JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
    return {
      company:       p.company       || 'Profile workspace',
      email:         p.email         || '',
      markets:       Array.isArray(p.markets)       ? p.markets       : [],
      industries:    Array.isArray(p.industries)    ? p.industries    : [],
      topics:        Array.isArray(p.topics)        ? p.topics        : [],
      customSources: Array.isArray(p.customSources) ? p.customSources : [],
      licenceTypes:  Array.isArray(p.licenceTypes)  ? p.licenceTypes  : [],
    }
  } catch {
    return { company: 'Profile workspace', email: '', markets: [], industries: [], topics: [], customSources: [], licenceTypes: [] }
  }
}

export function saveWorkspaceProfile(updates) {
  try {
    const current = JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
    localStorage.setItem(
      'regradar_workspace_profile',
      JSON.stringify({ ...current, ...updates }),
    )
  } catch (e) {
    if (import.meta.env?.DEV) console.warn('saveWorkspaceProfile failed', e)
  }
}

export function profileLabel(profile) {
  const m = profile.markets.join(' · ')
  const i = profile.industries.join(' · ')
  const t = profile.topics?.slice(0, 3).join(' · ')
  if (m && i) return `${m} | ${i}`
  if (m)      return m
  if (i)      return i
  if (t)      return t
  return 'Profile setup pending'
}

// Market name (onboarding) → COVERAGE_MARKETS code
const MARKET_TO_CODE = {
  UAE: 'AE',
  DIFC: 'AE',
  ADGM: 'AE',
  'Other UAE source': 'AE',
}

const UAE_PROFILE_MARKETS = new Set(['UAE', 'DIFC', 'ADGM', 'Other UAE source'])

function hasUaeProfile(profile) {
  return profile.markets.some(m => UAE_PROFILE_MARKETS.has(m))
}

export function filterAlerts(alerts, profile) {
  if (!profile.markets.length) return alerts
  if (hasUaeProfile(profile)) return alerts.filter(a => a.market === 'UAE')
  return alerts.filter(a => profile.markets.includes(a.market))
}

export function filterSources(sources, profile) {
  if (!profile.markets.length) return sources
  if (hasUaeProfile(profile)) return sources.filter(s => s.market === 'UAE')
  return sources.filter(s => profile.markets.includes(s.market))
}

export function filterReports(reports, profile) {
  if (!profile.markets.length) return reports
  if (hasUaeProfile(profile)) return reports.filter(r =>
    !r.marketList?.length ||
    r.marketList.includes('UAE')
  )
  return reports.filter(r =>
    !r.marketList?.length ||                               // "All markets" reports
    r.marketList.some(m => profile.markets.includes(m)),
  )
}

export function filterCoverage(markets, profile) {
  if (!profile.markets.length) return markets
  const codes = new Set(
    profile.markets.map(m => MARKET_TO_CODE[m]).filter(Boolean),
  )
  return markets.filter(m => codes.has(m.code))
}
