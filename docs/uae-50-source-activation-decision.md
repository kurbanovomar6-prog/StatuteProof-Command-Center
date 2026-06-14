# UAE 50 Source Activation Decision

Date: 2026-06-14

## 1. Decision

Add new sources to `sources.json`: **No**.

Reason:

The 50-target no-save live validation produced **0** new strict no-save passes. No new saved evidence or repeat baseline was created. Therefore no source qualifies for activation-ready status.

## 2. Sources Added To `sources.json`

None.

## 3. Sources Not Added And Why

| group | reason not added |
|---|---|
| VARA | current URLs returned not-found/nav-shell output; official URL cleanup required. |
| ADGM legacy `/fsra/...` URLs | selector timeout or nav/404 shell; use newer proven ADGM URL models. |
| DFSA/DIFC | blocked/chrome-heavy under strict gates; needs refined source model and adapters. |
| CBUAE | 403 before Playwright and chrome-heavy output after render; needs official endpoint/DOM remediation. |
| UAE FIU/EOCN/MoE/MoF/legislation | blocked, chrome-heavy, or broad homepages; needs narrower official endpoints. |
| SCA | item-level listing extraction remains unresolved. |

## 4. Public Source Truth Before / After

Before:

`13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation`

After:

`13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation`

## 5. Customer-Safe Wording

Allowed:

- “StatuteProof is expanding its UAE official-source map through adapter-gated validation.”
- “Current public source truth remains 13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.”
- “Five source-specific adapter families were added for remediation work.”
- “No new source was activated because live no-save checks did not pass strict readiness gates.”

Forbidden:

- “50 working sources.”
- “60 validated sources.”
- “40+ monitored sources.”
- “Any website can be parsed.”
- “Perfect parsing.”
- “Guaranteed compliance.”
- “Legal advice.”
- “Official regulator certified.”

## 6. Next Exact Task

Run a targeted SCA/DFSA DOM remediation sprint before attempting another 50-source activation batch.
