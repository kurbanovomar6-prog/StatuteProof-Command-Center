// 2.3: the plan picked on the public pricing page, carried through
// registration + email verification via localStorage. Standalone module with
// zero component imports — RegisterPage and ChoosePlanPage are separate
// lazy() chunks, and importing this constant from one component inside the
// other would fuse their bundles (react review, finding 2).
export const PLAN_INTENT_KEY = 'sp_plan_intent'

export const PLAN_INTENT_LABELS = {
  starter_pilot: 'Founding Pilot',
  professional: 'UAE Monitor',
  consultant: 'Consultant',
}

// Read the carried intent synchronously (lazy useState initializer — reading
// in an effect would guarantee a second render and a banner pop-in a frame
// after first paint). Returns '' when absent, invalid, or storage is off.
export function readPlanIntent() {
  try {
    const stored = window.localStorage.getItem(PLAN_INTENT_KEY) || ''
    return PLAN_INTENT_LABELS[stored] ? stored : ''
  } catch {
    return ''
  }
}

// Capture ?plan= from the current URL (validated), persist it, and return the
// effective intent. Falls back to a previously persisted value.
export function capturePlanIntentFromUrl() {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get('plan') || ''
    if (fromUrl && PLAN_INTENT_LABELS[fromUrl]) {
      window.localStorage.setItem(PLAN_INTENT_KEY, fromUrl)
      return fromUrl
    }
  } catch {
    // Storage/URL access failed — fall through to the stored value.
  }
  return readPlanIntent()
}

export function clearPlanIntent() {
  try {
    window.localStorage.removeItem(PLAN_INTENT_KEY)
  } catch {
    // Ignore — the key is re-validated on every read.
  }
}
