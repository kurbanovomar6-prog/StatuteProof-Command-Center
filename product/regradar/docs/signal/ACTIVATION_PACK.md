# ACTIVATION_PACK — F6 (signal-max sprint)

One real fetch per top-10 candidate on 2026-07-06 through the full new
stack (fetch → extraction → v2 normalization → hash). Raw results:
`activation_probe_results.jsonl`; probe code:
`scripts/signal/activation_probe.py`. **No source was enabled; sources.json
is untouched. Enabling is Phase 2, operator-gated, batches ≤10 with
per-source MONITOR_OK proof.**

## Results (real output, one fetch each)

| Source | Fetch | Normalized chars | Quality | Label |
|---|---|---|---|---|
| AE-adgm-fsra-waivers | OK | 1,931 | good | **fresh-alert candidate** — extraction+normalization+hash proven |
| AE-adgm-ra-circulars | OK | 9,291 | good | **fresh-alert candidate** — proven |
| AE-fta-tax-legislation-listing | OK | 35 | failed | NAV-SHELL — needs JS adapter |
| AE-fta-vat-guides-references | OK | 66 | failed | NAV-SHELL — needs JS adapter |
| AE-fta-corporate-tax-guides-references | OK | 37 | failed | NAV-SHELL — needs JS adapter |
| AE-fta-media-centre | OK | 36 | failed | NAV-SHELL — needs JS adapter |
| AE-fta-corporate-tax-legislation | OK | 11 | failed | NAV-SHELL — needs JS adapter |
| AE-uae-financial-intelligence-unit-uaefiu | OK | 1,413 | good | **fresh-alert candidate** — geo-block did NOT trip today; history says intermittent |
| AE-uaefiu-circulars | OK | 2,680 | good | fresh-alert candidate with caveat below |
| AE-uaefiu-typology-reports | OK | 2,680 | good | **caveat: same page shell as circulars** |

## Honest findings

1. **FTA (5 sources): nav-shell confirmed.** 11–66 normalized chars — the
   2026-06-18 "no-save retest" downgrade was correct. Activation requires a
   rendered-DOM adapter (Playwright) + content selector. Effort: M per
   source family; one adapter likely covers all five.
2. **UAEFIU typology vs circulars land on the same "FIU | Publications"
   shell** (hashes differ only by `Total visitors 59333/59334`). The
   distinct typology listing is JS-loaded; Playwright fetched 190k chars raw
   but extraction still returned the shell. These two sources need a
   listing adapter before they are DISTINCT monitors; enabling both today
   would double-count one page.
3. **Probe found two normalization leaks, fixed red→green in this cycle:**
   `Total visitors N` (EN visitor counter) and bare hex-color theme lines.
   Without the probe these would have produced a CHANGED on every UAEFIU
   visit.
4. **Geo-blocking is intermittent, not permanent.** All three UAEFIU URLs
   fetched fine from this network today. The `geo_blocked` status came from
   real failures in history — treat as flaky access, monitor with the
   circuit-breaker, do not promise coverage.

## Proposed config stubs (Phase 2 — NOT applied)

```json
{"source_id": "AE-adgm-fsra-waivers",  "monitoring_mode": "fresh_alert", "alert_eligible": true,
 "activation_evidence": "probe 2026-07-06: 1931 chars good, hash stable, no error page"}
{"source_id": "AE-adgm-ra-circulars", "monitoring_mode": "fresh_alert", "alert_eligible": true,
 "activation_evidence": "probe 2026-07-06: 9291 chars good"}
{"source_id": "AE-uae-financial-intelligence-unit-uaefiu", "monitoring_mode": "fresh_alert", "alert_eligible": true,
 "activation_evidence": "probe 2026-07-06: 1413 chars good; access flaky — keep circuit breaker"}
{"source_id": "AE-uaefiu-circulars", "monitoring_mode": "fresh_alert", "alert_eligible": true,
 "activation_evidence": "probe 2026-07-06: 2680 chars good; same shell as typology — enable ONE of the pair until a listing adapter lands"}
{"source_id": "AE-uaefiu-typology-reports", "monitoring_mode": "candidate", "alert_eligible": false,
 "activation_evidence": "probe 2026-07-06: renders the Publications shell — needs listing adapter first"}
{"source_id": "AE-fta-*", "monitoring_mode": "candidate", "alert_eligible": false,
 "activation_evidence": "probe 2026-07-06: nav-shell 11-66 chars — JS adapter required"}
```

Per-source gate at activation time (Phase 2): MONITOR_OK with proof URL +
timestamp + hash + baseline, plus an observed meaningful diff or an explicit
static/evidence-library label. Configured / eligible / monitored stay three
different truthful numbers.
