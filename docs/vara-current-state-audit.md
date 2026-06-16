# VARA Current State Audit

Date: 2026-06-16

## Active VARA Sources Before This Sprint

| Source ID | URL | Status | Type | Current issue / value |
| --- | --- | --- | --- | --- |
| `AE-dubai-virtual-assets-regulatory-authority-vara` | `https://www.vara.ae/` | active | general page | Useful official root, but broad and not deep rulebook coverage. |
| `AE-vara-enforcement` | `https://www.vara.ae/en/enforcement/` | active | enforcement page | Useful, but previous queue entries showed nav-shell/domain-stop issues for `www.vara.ae` paths. |
| `AE-vara-rulebook-updates` | `https://rulebooks.vara.ae/view-revision-updates?f_days=onchanged%3D-30+day` | active | rulebook updates listing | Best existing VARA source; proof-backed and adapter-gated. |

## VARA Candidates / Blockers

| Candidate | URL | Pre-sprint state | Blocker |
| --- | --- | --- | --- |
| `AE-vara-regulatory-framework` | `https://www.vara.ae/en/regulatory-framework/` | remediation | Stale/nav-shell/domain-stop on `www.vara.ae`. |
| `AE-vara-rulebooks-overview` | `https://www.vara.ae/en/regulatory-framework/rulebooks/` | remediation | Stale/nav-shell/domain-stop on `www.vara.ae`. |
| `AE-vara-company-rulebook` | `https://www.vara.ae/en/regulatory-framework/company-rulebook/` | remediation | Nav-shell/hash collision. Official equivalent found on `rulebooks.vara.ae`. |
| `AE-vara-aml-cft-rulebook` | `https://www.vara.ae/en/regulatory-framework/aml-cft-rulebook/` | remediation | Nav-shell/hash collision; no direct activation. |
| `AE-vara-public-register` | `https://www.vara.ae/en/public-register/` | remediation | Lower regulatory-change value; domain-stop history. |

## Commercial Usefulness

VARA depth matters for VASP MLROs because direct rulebooks carry obligations, controls, risk management expectations, activity-specific requirements, and enforcement context. The pre-sprint pack had VARA presence but not enough depth for a VARA-first buyer.

## Audit Decision

Use `rulebooks.vara.ae` official rulebook pages and their current-version direct PDFs as the activation path. Hold stale `www.vara.ae/en/regulatory-framework/...` paths unless they produce meaningful, stable extraction later.
