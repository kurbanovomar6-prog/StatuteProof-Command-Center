// Every customer-visible string authored for FirstRunBackfillPanel, in one
// module so the legal/forbidden-claims test can scan the FULL set — not only
// the strings a particular render path happens to show. Kept out of the
// component file so it stays a component-only module (react-refresh rule).
//
// Legal framing requirements (do not weaken when editing):
// - These are DETECTED changes already captured and sealed before the user's
//   first alert — the copy must say that plainly.
// - It must NOT imply the user was covered retroactively.
// - The short disclaimer must stay attached to the panel.
export const BACKFILL_STRINGS = {
  heading: 'Latest sealed changes from monitored official sources',
  framing:
    'Recent changes our monitor captured and sealed — before your first alert arrives, this is what the evidence trail looks like.',
  independence:
    'These records were captured by monitoring runs independently of your account. They are a preview of the evidence trail — not alerts issued for your workspace, and not monitoring coverage of any period before you signed up.',
  scopeScoped: 'Scoped to your selected market.',
  scopeFallback: 'From monitored official sources — not yet filtered to your profile.',
  sealedChip: 'Sealed record',
  capturedLabel: 'Captured',
  sealLabel: 'Seal',
  changeNoteLabel: 'Detected change',
  verifyLink: 'Verify this record yourself',
  empty:
    'No sealed change records are available to preview yet. Your evidence trail starts when a monitoring run detects a change — no sample data is shown here.',
  disclaimer: 'For monitoring information only. Not legal advice and not a guarantee of compliance.',
}
