# Fresh Signal 25 Per Family Target Contract

Date: 2026-06-19

## Definition Of Strong Fresh Signal

A family is Strong Fresh Signal only when it has at least 25 sources that all meet these conditions:

- official or officially linked public UAE source;
- `monitoring_mode: fresh_alert`;
- `alert_eligible: true`;
- `last_monitor_status: MONITOR_OK`;
- `proof_path` exists;
- `normalized_text_path` exists;
- `normalized_hash` exists;
- `baseline_runs_completed >= 2`;
- source is daily-checkable;
- `recommended_check_frequency: daily`;
- source can reasonably produce a future official regulatory change signal;
- not a static detail page;
- not a generic homepage;
- not `evidence_library`;
- not `remediation`;
- not a no-save-only or one-run-only record.

## Daily-Checked Means Daily-Checkable, Not Daily-Changing

The source does not need to change every day. It must be safe and useful to check daily so StatuteProof can detect changes when a regulator publishes a new law, rule, circular, consultation, enforcement action, sanctions/TFS update, tax clarification, or official legal update.

## Family Targets

| Family | Current Fresh Alert | Required Fresh Alert | Minimum New Fresh Alert Needed |
|---|---:|---:|---:|
| CBUAE | 0 | 25 | 25 |
| VARA | 16 | 25 | 9 |
| DFSA | 5 | 25 | 20 |
| DIFC | 3 | 25 | 22 |
| ADGM/FSRA | 2 | 25 | 23 |
| UAE FIU | 2 | 25 | 23 |
| EOCN / sanctions / TFS | 18 | 25 | 7 |
| SCA | 1 | 25 | 24 |
| MoJ / UAE Legislation / Gazette | 0 | 25 | 25 |
| MoF | 0 | 25 | 25 |
| FTA | 25 | 25 | 0 |
| MoE / DNFBP AML | 42 | 25 | 0 |

## Priority Order

1. CBUAE
2. SCA
3. EOCN / sanctions / TFS
4. UAE FIU
5. MoJ / UAE Legislation / Gazette
6. MoF
7. VARA
8. DIFC
9. ADGM/FSRA
10. DFSA
11. FTA validation
12. MoE/DNFBP validation

## Family-Specific Target Sources

### CBUAE

Target endpoints:

- rulebook modules;
- revision updates;
- regulations;
- circulars;
- notices;
- AML/CFT;
- payments;
- open finance;
- consumer protection;
- risk management.

Homepage pages do not count.

### VARA

Target endpoints:

- rulebook PDFs;
- company rulebook;
- compliance/risk;
- market conduct;
- custody;
- exchange;
- broker-dealer/activity rulebooks;
- virtual asset issuance guidance;
- admin orders;
- enforcement/notices;
- revision updates.

Homepage pages do not count.

### DFSA

Target endpoints:

- rulebook modules;
- rules and standards;
- laws and rules;
- consultation listings;
- AML/CTF and financial crime notices;
- enforcement decisions;
- regulatory actions;
- publication/listing pages.

Old individual notice pages do not count.

### DIFC

Target endpoints:

- legal database;
- legal notices;
- Data Protection Commissioner pages;
- AML/CFT;
- economic substance;
- consultations;
- publications;
- official law/document listings;
- official versioned PDFs only when hash-monitoring is meaningful.

Old whats-on/news detail pages do not count.

### ADGM/FSRA

Target endpoints:

- FSRA circulars;
- regulatory alerts;
- consultations;
- guidance;
- legal framework;
- enforcement;
- RA circulars;
- listing authority rules;
- data protection documents/listings.

Old individual announcement pages do not count.

### UAE FIU

Target endpoints:

- publications;
- NRA documents;
- typologies;
- annual reports;
- press releases;
- AML/CFT laws;
- public circulars if accessible.

goAML and private portals are forbidden.

### EOCN / Sanctions / TFS

Target endpoints:

- TFS guidance;
- sanctions guidance;
- laws/regulations;
- publications;
- notices;
- news;
- designation-list pages only with noise controls.

MoE-owned TFS documents may be partial substitute coverage, but do not prove complete/direct EOCN coverage.

### SCA

Target endpoints:

- AML/CFT;
- laws;
- decisions;
- regulations;
- circulars;
- procedures;
- enforcement/violations;
- market notices;
- PDF/download endpoints.

### MoJ / UAE Legislation / Gazette

Target endpoints:

- UAE legislation portal;
- official gazette;
- federal laws/decrees;
- legal database;
- official PDFs/document listings.

Access controls must be respected.

### MoF

Target endpoints:

- federal finance decisions;
- tax policy decisions;
- VAT/excise/treaty documents;
- policy publications;
- official announcements;
- budget/fiscal publication listings where commercially relevant.

Generic MoF homepage does not count.

## Hard Blocker Standard

If a family remains below 25, the final report must show:

- official-source research performed;
- candidates tested;
- no-save results;
- exact adapter investigation;
- HTTP/status/access classification;
- proof/baseline attempts for strong candidates;
- why remaining sources would be fake or unsafe to count;
- exact next technical fix.

“Could not quickly find sources” is not an acceptable blocker.
