# StatuteProof Source Family Upgrade Audit

Date: 2026-06-21

## Verdict

PASS for truth upgrade. HOLD for source activation.

Chosen family: UAE FIU.

Chosen target: `AE-uaefiu-circulars`.

This sprint did not activate the FIU circulars source. It proved why it must
remain held: the configured public URL resolves to the UAE FIU publications
index, not a distinct circulars/notices endpoint. The source registry and
source-quality audit were updated to remove the misleading circulars/notices
label.

## Agent Runtime

- Agents launched: 0
- Agent launch failures: 4
- Failure message: `collab spawn failed: agent thread limit reached`
- Fallback used: yes, Codex local fallback

No agent packet is claimed as real.

## Codex Local Fallback Packet

- verdict: PASS for blocker clarity, HOLD for activation
- chosen family: UAE FIU
- score_before: 6.2/10
- score_after: 6.3/10
- evidence found: `AE-uaefiu-circulars` has historical proof-backed runs, but the public page and sitemap do not show a distinct circulars/notices endpoint; Source Lab no-save returned `NAV_SHELL_ONLY`.
- files inspected: `product/regradar/sources.json`, `product/regradar/data/source_runs/source_runs.jsonl`, saved UAE FIU snapshots, `product/regradar/reports/source_signal_quality_audit.*`, `product/regradar/web/src/data/sourceQualityAudit.ts`, `tools/uae50_batch_nosave.py`.
- commands run: clean gate validators, preflight, source row audit, saved run audit, page header/content check, sitemap check, `uae50_batch_nosave.py`.
- methods attempted: saved proof/run inspection, public page redirect/content inspection, public page link extraction, official sitemap inspection, Source Lab no-save test.
- blockers found: no distinct official circulars/notices endpoint found; no-save result was `NAV_SHELL_ONLY`; current URL overlaps with already-active publications/typology sources.
- unsafe methods rejected: broad crawl, access-control bypass, fake activation, no-save-only activation, claiming FIU circulars monitored.
- safe alternatives remaining: manually inspect UAE FIU site navigation for a future official circulars/notices URL; contact founder/operator for legal/regulator-site review; if a new official endpoint appears, run save-proof plus repeat baseline.
- source IDs inspected: `AE-uaefiu-circulars`, `AE-uaefiu-guidance`, `AE-uaefiu-publications-hub`, `AE-uaefiu-typology-reports`, `AE-uaefiu-system-guides`.
- source IDs changed: `AE-uaefiu-circulars`, `AE-uaefiu-guidance` metadata only.
- customer claim impact: stronger truth boundary; selected UAE FIU publications/typology monitoring remains safe, but FIU circular monitoring remains forbidden.
- next prompt: investigate DIFC legal database/listing or ADGM/FSRA candidate rows with the same proof-first gate.
- stop/continue recommendation: stop activation attempt for FIU circulars; continue with a different official endpoint or different family.

## Current UAE FIU Source Rows

| Source ID | Mode | Status | Proof / baseline | Decision |
| --- | --- | --- | --- | --- |
| `AE-uae-financial-intelligence-unit-uaefiu` | remediation | remediation | historical homepage runs only | Keep remediation. |
| `AE-uaefiu-circulars` | candidate | active | historical proof-backed runs exist, but no distinct circulars endpoint | Keep candidate/held; metadata corrected. |
| `AE-uaefiu-guidance` | evidence_library | duplicate_url / disabled | duplicate of held publications URL | Keep disabled alias; metadata corrected. |
| `AE-uaefiu-typology-reports` | fresh_alert | active | proof + baseline; canonical evidence exists | Keep selected-source fresh-alert. |
| `AE-uaefiu-aml-cft-laws` | fresh_alert | active | proof + baseline | Keep selected-source fresh-alert. |
| `AE-uaefiu-publications-hub` | fresh_alert | active | proof + baseline | Keep selected-source fresh-alert; broad hub caveat. |
| `AE-uaefiu-annual-reports` | fresh_alert | active | proof + baseline | Keep selected-source fresh-alert. |
| `AE-uaefiu-press-releases` | fresh_alert | active | proof + baseline | Keep selected-source fresh-alert. |
| `AE-uaefiu-system-guides` | fresh_alert | active | proof + baseline; canonical evidence exists | Keep selected-source fresh-alert. |

## Methods Attempted

### 1. Saved Run Inspection

`AE-uaefiu-circulars` has saved runs from 2026-06-11 and 2026-06-12 with
proof paths and stable hash:

- `AE-20260611T222827Z-db5a1dea`: `FIRST_SEEN`, `GOOD`, 3,458 normalized chars.
- `AE-20260611T224414Z-2a59324c`: `UNCHANGED`, `GOOD`, 3,458 normalized chars.
- `AE-20260612T125401Z-c427013a`: `UNCHANGED`, `GOOD`, 3,458 normalized chars.

This proves the page was extractable, but it does not prove it is a circulars
source.

### 2. Snapshot Content Inspection

The saved normalized text contains the UAE FIU publications page with annual
reports, typology reports, strategic analysis and national risk assessment
items. It does not show a distinct circulars/notices listing.

### 3. Live Public Page Check

The configured URL:

`https://www.uaefiu.gov.ae/en/Publications/`

redirects to:

`https://uaefiu.gov.ae/en/more/knowledge-centre/publications`

Observed page title: `FIU | Publications`.

Term counts in the public HTML:

- `Circular`: 0
- `Notice`: 0
- `Typology`: 62
- `Publication`: 49
- `Annual Report`: 20
- `System Guides`: 2
- `AML`: 4

### 4. Public Link Extraction

The page links include annual reports, trends and typology reports, strategic
analysis, mutual evaluation reports and national risk assessment report pages.
No distinct circulars/notices URL was found.

### 5. Official Sitemap Check

`robots.txt` allows the public sitemap and lists:

- `https://www.uaefiu.gov.ae/en/xml-sitemap`
- `https://www.uaefiu.gov.ae/ar/xml-sitemap`

The English sitemap contained:

- `circular`: 0
- `notice`: 0
- `publication`: 34
- `typology`: 20
- `strategic`: 7
- `annual`: 11
- `system-guides`: 1

No official circulars/notices endpoint was identified.

### 6. Source Lab No-Save

Command:

```bash
python3 tools/uae50_batch_nosave.py \
  --url https://www.uaefiu.gov.ae/en/Publications/ \
  --source-id AE-uaefiu-circulars \
  --regulator "UAE FIU" \
  --out /tmp/uaefiu_circulars_nosave.json
```

Result:

- strong no-save passes: 0/1
- best status: `NAV_SHELL_ONLY`
- activation readiness: `NEEDS_REMEDIATION`
- `can_save_evidence`: false

## Safe Claim

StatuteProof monitors selected UAE FIU publication, typology, AML/CFT law,
press, annual-report and system-guide sources.

## Forbidden Claim

StatuteProof monitors UAE FIU circulars/notices.

## Score Decision

UAE FIU score: 6.2 -> 6.3.

Reason: blocker clarity and registry truth improved. No source activation, fresh
alert count, proof count, or customer delivery gate improved.

## Next Exact Source Task

Move to DIFC legal database/listing or ADGM/FSRA candidate rows, unless a new
official UAE FIU circulars/notices endpoint is found manually.
