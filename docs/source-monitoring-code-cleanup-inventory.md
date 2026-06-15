# Source Monitoring Code Cleanup Inventory

Date: 2026-06-15

Cleanup rule: no source-monitoring code is deleted unless references prove it is unused or harmful and tests pass after removal. If uncertain, the action is `deprecate` or `refactor`, not `delete`.

| Path | Why Suspicious | References Found | Used In CLI/API/Tests | Safe To Delete | Risk If Deleted | Recommended Action |
|---|---|---|---|---|---|---|
| `product/regradar/app/source_connector/` | Older "source connection" layer overlaps with new Source Discovery Engine. | `run.py` imports `discover_source_capabilities`; `source_connector/source_onboarding.py` uses connector modules. | Yes, CLI paths still reference the old capability discovery flow. | No. | Could break older onboarding/discovery commands and reports. | Keep now; create later parity/refactor plan to route old commands through `source_discovery.py`. |
| `product/regradar/run.py` discovery help lines | Stale help still says `discover-source` uses "Source Connection Engine" and exports `reports/discover_source_*.json`. | `rg` found stale text near help output. | Yes, CLI help. | Not a delete target. | Misleads operators during source onboarding. | Update help text to current no-save discovery behavior. |
| `product/regradar/repopack-output.txt` | Large historical project bundle can confuse searches. | Referenced in historical docs/reports; not imported by runtime. | No runtime use found in this audit. | Not deleted in this sprint. | Removing tracked history artifact could create unrelated churn. | Keep; consider archival cleanup in separate repo hygiene task. |
| `product/regradar/app/telegram_clients.py` | Contains legacy helper wording. | Used by Telegram/client commands. | Yes, alert/customer-channel area. | No. | Could break alert/client utilities. | Keep; unrelated to mass source activation. |
| `product/regradar/app/extractors.py::_legacy_extract_best_text` | Legacy fallback name. | Extractor fallback used by parser tests/intake. | Yes. | No. | Could weaken parser fallback behavior. | Keep; refactor only with parser regression tests. |
| `product/regradar/app/report.py` legacy flags | Historical report behavior. | Report generation paths. | Yes. | No. | Could break reports. | Keep. |
| `product/regradar/web/src/components/app/SourcesPage.jsx` legacy modal notes | Prior docs mention duplicated/legacy modal state. | Frontend route/component still exists. | Yes. | No. | Could break source management UI. | Defer to frontend UX cleanup sprint. |

## Cleanup Performed In This Sprint

- No code was deleted.
- One safe CLI help-text correction is allowed because it reduces operator confusion and does not alter runtime behavior.

## Cleanup Deferred

1. `source_connector` parity review against `source_discovery.py`.
2. Historical generated/bundled artifact cleanup.
3. Frontend SourcesPage modal simplification.
4. Parser fallback naming cleanup after broad parser regression coverage.
