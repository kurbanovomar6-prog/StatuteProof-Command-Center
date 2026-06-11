# Workflow 02: First Source Spec

**When:** Before enabling any new source for monitoring.
**Agent:** Source Monitor Agent.
**Output:** A validated source spec ready to add to `sources.json`.

---

## Prerequisites

- [ ] You have the official URL from the regulator's own domain
- [ ] The URL is accessible without login
- [ ] You know what regulatory content you want to monitor on that page

---

## Step 1 — Choose the Source

Use UAE official regulatory domains only:
- `vara.ae` — Virtual Assets Regulatory Authority
- `centralbank.ae` — Central Bank UAE
- `dfsa.ae` — Dubai Financial Services Authority
- `adgm.com` — Abu Dhabi Global Market
- `mof.gov.ae` — Ministry of Finance
- `amlcft.ae` — UAE Financial Intelligence Unit
- `uaelegislation.gov.ae` — UAE Legislation Portal
- `difclaw.difc.ae` — DIFC Laws
- `moec.gov.ae` — Ministry of Economy

Start with VARA, CBUAE, or DFSA — they are already verified in the pipeline with real run records.

---

## Step 2 — Use Source Spec Prompt

Fill in and run `prompts/source-spec-prompt.md` with the Source Monitor Agent.

---

## Step 3 — Run the Before-Source-Spec Checklist

`checklists/before-source-spec.md` — complete all items before proceeding.

---

## Step 4 — Add to sources.json (Disabled)

Add the new source to `regradar/sources.json` with `"enabled": false`.
Do not enable until Step 5 passes.

Format:
```json
{
  "source_id": "AE-VARA-VASP-FEES",
  "source_name": "VARA VASP Fee Schedule",
  "regulator": "VARA",
  "official_url": "https://www.vara.ae/[path]",
  "country": "AE",
  "market": "AE",
  "enabled": false,
  "fetch_method": "http",
  "monitoring_frequency": "daily",
  "priority": "HIGH"
}
```

---

## Step 5 — Run Evidence Dry Run

Go to `workflows/03-evidence-dry-run.md`.
Only enable the source after the dry run produces PASS status.

---

## Step 6 — Enable and Record

After PASS dry run:
1. Set `"enabled": true` in `sources.json`
2. Note the first real `run_id` and `run_timestamp`
3. Update `STATUTEPROOF_CONTEXT.md` if this is a new source

---

## What Not to Do

- Do not fabricate or invent a URL that you have not verified in a browser
- Do not enable a source before the dry run
- Do not create more than 1 new source spec per week until monitoring is stable
