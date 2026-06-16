# Weak-Zone Agent Gate Report

Date: 2026-06-16

Subagents were emulated manually; no subagent runtime was invoked. All gates below are based on no-save, proof artifacts, repeat baseline, mass-monitor dry-run, and source relevance evidence.

## `AE-uaefiu-aml-cft-laws`

| Gate | Decision | Reason |
| --- | --- | --- |
| Source Monitor | PASS | Official/public UAE source or official Central Bank rulebook subdomain; extraction meaningful; mass-monitor returned MONITOR_OK. |
| Evidence Trail | PASS | Two proof paths written, normalized hash present, baseline complete, CERTIFIED_EVIDENCE. |
| QA/Critic | PASS | No nav-shell, not shallow, no duplicate active hash, no no-save-only activation. |
| Legal Language | PASS | Monitoring-source wording only; no legal advice, guarantee, or regulator certification claim. |
| Product Manager | PASS | Relevant to MLRO/CCO monitoring: AML/CFT laws, FIU publications, or CBUAE rulebook updates. |
| Code Architect | PASS | Uses existing adapter platform and no unsafe dependency or broad rewrite. |

**Final decision:** activation_ready and added to `sources.json` after validators are updated.

## `AE-uaefiu-publications-hub`

| Gate | Decision | Reason |
| --- | --- | --- |
| Source Monitor | PASS | Official/public UAE source or official Central Bank rulebook subdomain; extraction meaningful; mass-monitor returned MONITOR_OK. |
| Evidence Trail | PASS | Two proof paths written, normalized hash present, baseline complete, CERTIFIED_EVIDENCE. |
| QA/Critic | PASS | No nav-shell, not shallow, no duplicate active hash, no no-save-only activation. |
| Legal Language | PASS | Monitoring-source wording only; no legal advice, guarantee, or regulator certification claim. |
| Product Manager | PASS | Relevant to MLRO/CCO monitoring: AML/CFT laws, FIU publications, or CBUAE rulebook updates. |
| Code Architect | PASS | Uses existing adapter platform and no unsafe dependency or broad rewrite. |

**Final decision:** activation_ready and added to `sources.json` after validators are updated.

## `AE-cbuae-rulebook-revision-updates`

| Gate | Decision | Reason |
| --- | --- | --- |
| Source Monitor | PASS | Official/public UAE source or official Central Bank rulebook subdomain; extraction meaningful; mass-monitor returned MONITOR_OK. |
| Evidence Trail | PASS | Two proof paths written, normalized hash present, baseline complete, CERTIFIED_EVIDENCE. |
| QA/Critic | PASS | No nav-shell, not shallow, no duplicate active hash, no no-save-only activation. |
| Legal Language | PASS | Monitoring-source wording only; no legal advice, guarantee, or regulator certification claim. |
| Product Manager | PASS | Relevant to MLRO/CCO monitoring: AML/CFT laws, FIU publications, or CBUAE rulebook updates. |
| Code Architect | PASS | Uses existing adapter platform and no unsafe dependency or broad rewrite. |

**Final decision:** activation_ready and added to `sources.json` after validators are updated.
