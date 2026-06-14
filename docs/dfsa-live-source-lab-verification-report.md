# DFSA Live Source Lab Verification Report

Date: 2026-06-14

Scope: two approved no-save Source Lab checks only. No evidence was saved, no source registry status was changed, no alerts were sent, and no broad monitoring run was started.

## Commands Run

From `product/regradar`:

```bash
python3 run.py source-lab https://www.dfsa.ae/rules-and-standards --js --wait-for-selector main --content-selector main --no-save --json
python3 run.py source-lab https://www.dfsa.ae/regulation/notices-public-registers --js --wait-for-selector main --content-selector main --no-save --json
```

## Result: AE-dubai-financial-services-authority-dfsa

| Field | Value |
|---|---|
| Source ID | `AE-dubai-financial-services-authority-dfsa` |
| URL | `https://www.dfsa.ae/rules-and-standards` |
| Playwright launched | Yes; no browser launch exception was raised |
| Wait selector | `main` |
| Content selector | `main` |
| Main selector worked | Technically yes; it matched a shell/not-found page, not regulatory content |
| Provider used | `bs4` after Playwright-rendered HTML was fetched |
| Extraction method | `bs4` |
| Normalized length | 77 |
| Normalized hash | `aaaffe59c59c09e66f5bd79fb59e0fdcf978e0ad2294e917d053521a0b918e9f` |
| Quality score | 0 |
| Quality label | `POOR` |
| Readiness status | `NAV_SHELL_ONLY` |
| Activation readiness | `NEEDS_REMEDIATION` |
| Evidence level | `PREVIEW_ONLY` |
| Nav-shell flag | `true` |
| Internal hash-collision flag | `false` in the single Source Lab result |
| Cross-DFSA hash collision | Yes; same normalized hash as DFSA notices result |
| Can save for validation | `false` |
| Can activate monitoring | `false` |
| Failure reason | Extracted content is a navigation shell or collides with another source hash. |
| Remediation hint | Configure a precise content_selector or adapter before marking this source ready. |

Normalized preview, first 500 characters:

```text
Oops! Page not found
Document or file requested was not found.
Go to Homepage
```

## Result: AE-dfsa-notices

| Field | Value |
|---|---|
| Source ID | `AE-dfsa-notices` |
| URL | `https://www.dfsa.ae/regulation/notices-public-registers` |
| Playwright launched | Yes; no browser launch exception was raised |
| Wait selector | `main` |
| Content selector | `main` |
| Main selector worked | Technically yes; it matched a shell/not-found page, not regulatory content |
| Provider used | `bs4` after Playwright-rendered HTML was fetched |
| Extraction method | `bs4` |
| Normalized length | 77 |
| Normalized hash | `aaaffe59c59c09e66f5bd79fb59e0fdcf978e0ad2294e917d053521a0b918e9f` |
| Quality score | 0 |
| Quality label | `POOR` |
| Readiness status | `NAV_SHELL_ONLY` |
| Activation readiness | `NEEDS_REMEDIATION` |
| Evidence level | `PREVIEW_ONLY` |
| Nav-shell flag | `true` |
| Internal hash-collision flag | `false` in the single Source Lab result |
| Cross-DFSA hash collision | Yes; same normalized hash as DFSA rules result |
| Can save for validation | `false` |
| Can activate monitoring | `false` |
| Failure reason | Extracted content is a navigation shell or collides with another source hash. |
| Remediation hint | Configure a precise content_selector or adapter before marking this source ready. |

Normalized preview, first 500 characters:

```text
Oops! Page not found
Document or file requested was not found.
Go to Homepage
```

## Verdict

- Playwright launched: yes.
- `main` selector worked at a technical DOM level: yes, but it selected not-found/shell content.
- Normalized content meaningful: no.
- Hashes unique between the two DFSA sources: no.
- Nav-shell / shallow shell detected: yes.
- Cross-source collision detected by review: yes, same normalized hash.
- DFSA can move from remediation: no.
- DFSA can be shown as ready in UI: no.

## Exact Next Task

Investigate the DFSA live site routes and selector strategy in a browser session, identify whether the official content has moved or requires a different path/adapter, then rerun the same no-save checks. Do not change DFSA registry status until the two sources produce meaningful, unique, non-shell content and pass Source Monitor, Evidence Trail, QA, and Legal gates.
