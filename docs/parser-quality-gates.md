# Parser Quality Gates

StatuteProof can test and monitor public sources that are technically accessible and permitted to be monitored. It shows extraction quality, evidence readiness, hashes, diffs, activation readiness, and failure reasons clearly.

This checklist is the parser/source-intake gate before a source, parser change, Source Lab UI update, or customer-facing readiness claim is shipped.

## Parser Release Checklist

- Required parser files exist: `source_intake.py`, `source_quality.py`, `source_certification.py`, `source_tester.py`, `scraper.py`, `extractors.py`, provider modules, API, CLI, source runs, proof, diff, and normalization.
- Provider cascade returns metadata: provider used, extraction method, candidates, warnings, elapsed time where available.
- Optional providers fail closed with warnings, not uncaught exceptions.
- Requests, Playwright, explicit selector, source adapter, trafilatura/readability/selectolax/BeautifulSoup fallback, and PDF provider paths are distinguished in output.
- Fetch failures, selector timeouts, nav-shell extraction, hash collisions, shallow text, and policy blocks do not produce a ready or activation state.
- Change detection remains deterministic hash/diff logic. LLMs are not used to decide whether source content changed.

## Customer-Facing Claim Checklist

- Use: public source testing, source readiness, activation readiness, extraction quality, evidence confirmed, needs remediation, failure reasons, monitoring intelligence only, not legal advice.
- Do not imply all enabled sources are ready.
- Do not imply regulator endorsement, legal advice, guaranteed compliance, perfect parsing, or complete coverage.
- Do not show raw internal `PASS`, `Validated`, or activation-like `Active` labels in customer-facing source tables.
- Current UAE source story: 147 enabled UAE sources, 146 monitoring-active in the current registry, 1 remediation source.
- Remediation source in the current registry: UAE FIU Homepage.

## Source Readiness Checklist

- URL is public `http(s)` and does not contain credentials.
- Localhost, private IPs, file URLs, login pages, CAPTCHA, paywalls, private portals, and access-control redirects are blocked or held.
- Normalized text length is above threshold for the source type.
- Extracted content is meaningful regulatory/source content, not navigation shell.
- Normalized hash is present and unique across enabled source records where collision comparison is available.
- Quality score and quality label are visible.
- Failure reason and remediation hint are present for every not-ready result.

## Custom Source Activation Checklist

- No-save Source Lab result is preview only.
- `can_save_for_validation` may be true after a passing no-save test.
- `can_activate_monitoring` remains false until proof artifacts and baseline requirements pass.
- Save requires legal confirmation that the source is public and permitted to monitor.
- Evidence confirmed requires a proof artifact, snapshot paths, hashes, and run record.
- Monitoring-ready requires baseline run history and review approval; one successful test is not enough.
- Founder approval is required before a remediation source becomes customer-visible ready when live verification is incomplete.

## Evidence Completeness Checklist

- Run record includes source id, source name, URL, final URL, timestamp, run id, market, and category.
- Access status, fetch method, extraction quality, raw chars, normalized chars, hashes, and content hash are present.
- Snapshot paths exist for raw text, normalized text, metadata, and proof block.
- Diff paths exist for changed records.
- Failed and quality-drop runs are not silently represented as unchanged.
- Evidence level is clearly shown as preview, basic/full evidence, or baseline-backed evidence.

## DFSA Live Verification Checklist

- Run only the two approved no-save Source Lab checks.
- Use exact URLs from `sources.json`.
- Use Playwright only for the two DFSA URLs, with `--wait-for-selector main` and `--content-selector main`.
- Do not save evidence, send alerts, run all sources, or change source registry status during the check.
- Record whether Playwright launched, selector worked, normalized content was meaningful, hashes were unique, nav-shell was detected, and collision was detected.
- DFSA cannot leave remediation unless both sources produce meaningful, unique, non-nav-shell content and pass Source Monitor/Evidence/QA/Legal gates.

## Blocked-Source Policy

- Block or hold login-protected, CAPTCHA-gated, paywalled, private portal, private IP, localhost, file URL, credential-bearing, and access-control-bypass scenarios.
- Do not bypass access controls.
- Do not scrape private or personal data.
- Document the reason and remediation path instead of trying unsafe workarounds.

## Required Agent Review Gates

- Source Monitor reviews URL, source spec, extraction route, source status, and failure handling.
- Evidence Trail verifies proof artifacts, hashes, snapshots, diffs, and evidence level.
- Code Architect reviews implementation risk for parser/API changes.
- QA / Critic blocks false ready states, broken routes, bad mappings, and untested behavior.
- Legal Language reviews customer-facing copy for overclaim and legal-advice risk.
