# Design Sprint 4A — UAE-First Demo Data Cleanup

## 1. Verdict

Completed. The default logged-in workspace and frontend sample/demo data are now UAE-first. Non-UAE market examples, flags, sources and reports were removed or replaced with UAE, DIFC, ADGM and UAE source-layer examples.

## 2. Files changed

- web/src/data/appMockData.js
- web/src/data/workspaceProfile.js
- web/src/data/watchlistOptions.js
- web/src/components/app/DashboardHome.jsx
- web/src/components/app/OnboardingPage.jsx
- web/src/components/app/ReportsPage.jsx
- web/src/components/app/SettingsPage.jsx
- web/src/components/app/SourcesPage.jsx
- web/src/components/AIAnalyst.jsx
- web/src/components/InteractiveDemo.jsx
- web/src/components/MonitoringProfile.jsx
- web/src/components/SampleReports.jsx
- web/src/components/Solution.jsx

## 3. Non-UAE demo data removed/replaced

Removed default client-facing references to Turkey, Kazakhstan, Georgia, Azerbaijan, Saudi Arabia, Armenia, CIS/Caucasus and their legacy source examples. Market selectors now default to UAE, DIFC, ADGM and Other UAE source.

Legacy demo components were also cleaned so old regional examples cannot be surfaced accidentally if those components are reused.

## 4. UAE source layers added

The default sample source list now uses UAE-relevant source layers:

- VARA
- CBUAE
- UAE FIU
- DFSA
- DIFC Laws
- ADGM / FSRA
- MoET AML / DNFBP
- FTA
- UAE Legislation Portal
- Executive Office / Sanctions
- DIFC Data Protection
- ADGM Data Protection

Statuses use readiness language: Validated, Under validation, Needs adapter and Limited.

## 5. Reports/alerts/briefs updated

Reports, alerts and brief previews now use UAE-first sample content:

- UAE VASP Source Readiness Review
- CBUAE / AML Brief Preview
- VARA Rulebook Update Preview
- DIFC / DFSA Source Transparency Report
- ADGM / FSRA Circulars Preview
- FTA Public Clarification Watch
- UAE FIU Typology Brief Preview
- Proof/Diff Artifact Sample

Sample alerts are marked as preview/sample content and include source proof, profile relevance, limitation notes and delivery status that does not imply production routing.

## 6. Claims safety result

The required non-UAE grep returned no matches.

The unsafe-claims grep returned only "not legal advice" disclaimer language. No new claim was added for complete UAE coverage, 35 active sources, all UAE regulators, real-time alerts, guaranteed compliance, live client data or production delivery.

## 7. Remaining future expansion notes

No country-specific future expansion list was added. Regional expansion can be revisited after the UAE pilot source validation is complete.

## 8. Validation result

- `cd web && npm run build`: passed
- `git diff --check`: passed
- non-UAE demo grep: no matches
- unsafe claims grep: disclaimer-only "not legal advice" matches

## 9. What was deliberately not changed

- Backend/auth/Telegram were not touched.
- Telegram secrets and environment files were not touched.
- Source monitoring behavior was not changed.
- No source was activated.
- No personalized alert/brief delivery was implemented.
- No fake live data, fake clients, fake logos or fake testimonials were added.
