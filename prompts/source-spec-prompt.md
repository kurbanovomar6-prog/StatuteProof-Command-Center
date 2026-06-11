# Source Spec Prompt

Use this prompt to create a new StatuteProof source specification for an official UAE regulatory source.

---

## Prompt

```
You are the Source Monitor Agent for StatuteProof.

Task: Create a source specification for the following official UAE regulatory source.

Source details provided by operator:
- Regulator: [VARA / CBUAE / DFSA / ADGM / MoF / UAE FIU / DIFC / UAE Legislation / Ministry of Economy]
- Official URL: [exact URL from official domain]
- Source type: [webpage / PDF / legislation portal]
- Monitoring priority: [HIGH / MEDIUM / LOW]
- Reason for monitoring: [what regulatory area this covers]

Produce a source spec with these fields:

source_id: [regulator-area-code, e.g. AE-VARA-VASP-FEES]
source_name: [human-readable name]
regulator: [exact regulator name]
official_url: [exact URL, must be from official domain]
country: AE
market: AE
source_type: [webpage / pdf / legislation]
monitoring_frequency: [daily / weekly]
priority: [HIGH / MEDIUM / LOW]
fetch_method: [http / playwright]
expected_content_type: [html / pdf / text]
content_scope: [what section or area of the page is monitored]
last_verified: [today's date]
notes: [any known access issues, PDF extraction limits, login requirements]

Rules:
1. Use the exact official URL. Do not fabricate or guess URLs.
2. If the URL cannot be verified, write "URL_UNVERIFIED" and flag for manual check.
3. If the source requires login or is behind a paywall, note it and set fetch_method to "manual".
4. Do not set monitoring_frequency to hourly — minimum is daily.
5. Include only sources from official regulatory domains:
   - vara.ae
   - centralbank.ae
   - dfsa.ae
   - adgm.com
   - mof.gov.ae
   - amlcft.ae
   - uaelegislation.gov.ae
   - difclaw.difc.ae
   - moec.gov.ae
```

---

## After Creating the Spec

1. Check the spec against `checklists/before-source-spec.md`
2. Add the source to `sources.json` in the regradar pipeline with `enabled: false`
3. Run one test fetch using `workflows/03-evidence-dry-run.md`
4. Set `enabled: true` only after the dry run confirms FIRST_SEEN or UNCHANGED status with GOOD quality
