# Fresh Signal Source Mode Spec

## Purpose

StatuteProof needs to separate sources that can create customer-facing fresh regulatory alerts from official pages that are useful only as reference/evidence records.

## Modes

### fresh_alert

Use when a source is eligible to produce customer update signals.

Required:

- Official or officially linked public source.
- UAE-relevant.
- Commercially useful to MLRO/CCO/compliance/legal/tax buyers.
- `last_monitor_status == "MONITOR_OK"`.
- `proof_path` exists.
- `normalized_hash` exists.
- Baseline is complete or there is an explicit legacy proof exception.
- Source-health risk is acceptable or documented.
- Noise risk is acceptable or filtered.
- `alert_eligible: true`.

Examples:

- Rulebook revision listing.
- Circular/notice listing page.
- Enforcement/admin order listing page.
- Official PDF rulebook with stable hash monitoring.
- Official tax decision/guidance PDF.

### evidence_library

Use when a source is official and can be retained as evidence/reference, but should not create customer “new update” alerts.

Allowed:

- May have proof.
- May have normalized hash.
- May have `MONITOR_OK`.
- May appear in audit packs or source transparency.

Forbidden:

- Must not count as fresh-alert monitoring.
- Must not trigger customer fresh-update notifications.
- Must not be used in “live monitoring source count” claims.

Examples:

- Old static DFSA individual notice detail pages.
- Old static DIFC “whats-on” pages.
- Old static ADGM announcement detail pages.
- Generic official homepages when stronger official endpoints exist.

### remediation

Use when a source is important but currently blocked, unstable, too noisy, shallow, or unconfirmed.

Required:

- Exact blocker reason.
- Next remediation step.
- `alert_eligible: false`.

Examples:

- WAF-blocked official legislation portal.
- SCA source with 403/robots blocker.
- EOCN direct source without live monitoring confirmation.

### candidate

Use when a source has been researched but is not activated.

Required:

- Official/public rationale.
- Expected adapter strategy.
- Activation blocker or next test.

## Customer Copy Rule

Only `fresh_alert` sources with `MONITOR_OK` may be counted in customer-facing “confirmed live monitoring” claims. `evidence_library` sources may be described as official evidence/reference records, not fresh monitoring.

Approved disclaimer:

“Monitoring intelligence only. Not legal advice.”
