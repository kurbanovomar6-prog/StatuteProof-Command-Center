// Shared risk-band metadata for the app surfaces that render a band.
//
// Colour-blind readers are ~8% of the audience and colour-alone fails them, so a
// band is NEVER just a colour: it always pairs the colour with a TEXT LABEL and a
// one-line REVIEW-PRIORITY definition. The definition is framed as suggested
// review urgency ("Priority: suggest same-day review") — it is deliberately NOT a
// legal severity, a compliance conclusion, or an obligation ("you must ...").
//
// Colours come from the design tokens in index.css (--risk-high/medium/low), never
// hardcoded hex, so every band stays consistent with the rest of the system.

export const RISK_BANDS = {
  HIGH: {
    label: 'High',
    color: 'var(--risk-high)',
    priority: 'Priority: suggest same-day review',
  },
  MEDIUM: {
    label: 'Medium',
    color: 'var(--risk-medium)',
    priority: 'Priority: suggest review this week',
  },
  LOW: {
    label: 'Low',
    color: 'var(--risk-low)',
    priority: 'Priority: review when convenient',
  },
}

// One-line legend shown wherever bands appear, so the colour + label is defined in
// review-priority terms and can never be read as a legal severity conclusion.
export const RISK_BAND_LEGEND =
  'Priority reflects suggested review urgency from monitoring, not a legal severity or compliance conclusion.'

/**
 * Resolve a risk level string to its band metadata, defaulting to MEDIUM.
 * @param {string} level
 * @returns {{ label: string, color: string, priority: string }}
 */
export function riskBand(level) {
  return RISK_BANDS[String(level || 'MEDIUM').toUpperCase()] || RISK_BANDS.MEDIUM
}
