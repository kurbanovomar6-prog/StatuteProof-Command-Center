# StatuteProof — Next Implementation Task

**Date:** 2026-06-12  
**Task:** Wire real source status data to the authenticated dashboard and Sources page  
**Priority:** P0 — highest signal-to-effort ratio for first pilot conversations  
**Estimated effort:** 4-6 hours  
**Not legal advice. Internal implementation document.**

---

## Task Name

**"Connect real source run data to the authenticated dashboard and Sources page"**

---

## Why This First

### Business rationale

1. A pilot customer who logs in and sees fake numbers loses trust immediately. Compliance professionals are trained to spot inconsistencies.
2. The source status data already exists in `data/source_runs/source_runs.jsonl` — this is a wiring task, not a build-from-scratch task.
3. Showing a pilot customer their own live source run history (VARA UNCHANGED, CBUAE UNCHANGED, etc.) proves the monitoring is real. No marketing copy does this as effectively as real data.
4. Every other feature (evidence records, diff viewer, briefs) can only be shown meaningfully once source status is real. This task unblocks all subsequent demo-ability.

### Technical rationale

1. The monitoring pipeline runs and produces real data (source_runs.jsonl confirmed populated per HANDOFF.md — Sprint 1 records, Sprint 2 evidence, Sprint 3 alert drafts).
2. The backend has a FastAPI router and an existing GET /regulations endpoint pattern to follow.
3. The frontend has DashboardPreview.jsx and Coverage.jsx already — this is a data-source swap, not a component rebuild.
4. The source_readiness.py module already has `latest_runs()` function that reads source_runs.jsonl — the data layer is done.

---

## Exact Files to Modify or Create

### Backend (New API endpoint)

**File to modify:** `product/regradar/app/api/v1/router.py`
**New endpoint:** `GET /api/v1/sources/status`

This endpoint reads from source_runs.jsonl via existing `latest_runs()` function and returns per-source current status.

**File to read first:** `product/regradar/app/source_runs.py` — understand the `latest_runs()` return structure  
**File to read first:** `product/regradar/app/source_readiness.py` — understand build_readiness_report() and load_market_sources()

### Frontend (Component updates)

**File to modify:** `product/regradar/web/src/components/DashboardPreview.jsx`
- Replace hardcoded mock data with API call to GET /api/v1/sources/status
- Show source count, status breakdown, last run timestamp

**File to modify:** `product/regradar/web/src/api.js`
- Add `getSourceStatus(market = 'AE')` function

**File to modify (verify/update):** `product/regradar/web/src/components/Coverage.jsx`
- Ensure UAE source list matches the 13 READY sources from sources.json
- Source status shown as Active/Limited/Blocked (not a number count)

**File to review:** `product/regradar/web/src/App.jsx`
- Verify DashboardPreview is rendered in authenticated view
- Understand current auth routing (logged-in vs public)

---

## Step-by-Step Implementation Instructions

### Step 1: Create a git branch (safety first)

```bash
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar
git checkout -b feat/real-source-status-dashboard
```

### Step 2: Read current code before modifying

Read these files in order before writing a line of code:
1. `product/regradar/app/source_runs.py` — understand `latest_runs(market: str) -> dict`
2. `product/regradar/app/source_readiness.py` — understand `load_market_sources(jurisdiction)`
3. `product/regradar/app/api/v1/router.py` — understand endpoint pattern and auth middleware
4. `product/regradar/web/src/components/DashboardPreview.jsx` — understand current mock data structure
5. `product/regradar/web/src/api.js` — understand current API call pattern

### Step 3: Add GET /api/v1/sources/status to router.py

Add after the existing `/kpis` endpoint in `product/regradar/app/api/v1/router.py`:

```python
@api_router.get(
    "/sources/status",
    summary="Current source status from latest run history",
)
def get_sources_status(
    current_user: Annotated[dict, Depends(_get_current_user)],
    market: str = Query("AE", max_length=5, description="Market/jurisdiction code e.g. AE"),
) -> dict:
    """
    Returns per-source status from the latest source run history.
    Reads from source_runs.jsonl (ignored runtime data).
    
    Returns:
      - sources: list of source status records
      - summary: counts by status
      - last_run_at: timestamp of most recent run
      - market: jurisdiction code
    
    Not legal advice. For monitoring information only.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    try:
        from app.source_runs import latest_runs
        from app.source_readiness import load_market_sources
    except ImportError as e:
        log.error("sources/status: import error: %s", e)
        raise HTTPException(status_code=500, detail="Source status module unavailable")
    
    jur = market.upper()
    all_sources = load_market_sources(jur)
    history = latest_runs(jur)
    
    status_counts = {
        "FIRST_SEEN": 0,
        "UNCHANGED": 0,
        "CHANGED": 0,
        "FAILED": 0,
        "QUALITY_DROP": 0,
        "NOT_RUN": 0,
    }
    
    last_run_at = None
    source_list = []
    
    for src in all_sources:
        src_id = src.get("source_id") or src.get("name", "")
        name = src.get("name", "")
        enabled = src.get("enabled", True)
        
        if not enabled:
            continue
        
        run = history.get(src_id) or history.get(name)
        
        if run:
            change_status = run.get("change_status", "FIRST_SEEN")
            quality = run.get("extraction_quality", "unknown")
            chars = int(run.get("extracted_chars") or run.get("normalized_chars") or 0)
            run_ts = run.get("timestamp_utc") or run.get("run_timestamp")
            error = run.get("error")
            
            if run_ts and (last_run_at is None or run_ts > last_run_at):
                last_run_at = run_ts
        else:
            change_status = "NOT_RUN"
            quality = "unknown"
            chars = 0
            run_ts = None
            error = None
        
        status_counts[change_status] = status_counts.get(change_status, 0) + 1
        
        source_list.append({
            "source_id": src_id,
            "name": name,
            "regulator": src.get("name", name),
            "url": src.get("url", ""),
            "category": src.get("category", ""),
            "tier": src.get("tier", ""),
            "change_status": change_status,
            "extraction_quality": quality,
            "extracted_chars": chars,
            "last_run_at": run_ts,
            "error": error,
            "limitations": src.get("notes", None),
        })
    
    return {
        "market": jur,
        "sources": source_list,
        "summary": status_counts,
        "total_sources": len(source_list),
        "last_run_at": last_run_at,
        "disclaimer": "Not legal advice. For monitoring information only.",
    }
```

**Key points:**
- Do NOT raise exceptions for missing source_runs.jsonl — return empty summary with total_sources=0 and an empty list
- Handle both `source_id` and `name` as lookup keys (some records use one, some the other)
- Return `last_run_at` so the dashboard can show "Last run: 2 hours ago"
- Include `disclaimer` in every API response that returns monitoring data

### Step 4: Add getSourceStatus to api.js

In `product/regradar/web/src/api.js`, add:

```javascript
export async function getSourceStatus(market = 'AE', accessToken) {
  const response = await fetch(`/api/v1/sources/status?market=${market}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`Source status fetch failed: ${response.status}`);
  }
  
  return response.json();
}
```

**Note:** Check how the existing API calls handle auth token storage and passing. Match the existing pattern in api.js — do not introduce a new auth pattern.

### Step 5: Update DashboardPreview.jsx

In `product/regradar/web/src/components/DashboardPreview.jsx`:

1. Import `getSourceStatus` from api.js
2. Add `useEffect` to fetch on mount (or on auth context available)
3. Add loading state (skeleton)
4. Add empty state ("No monitoring runs yet. First run within 24 hours.")
5. Add error state ("Could not load source status. Retry.")
6. Replace mock data in the source status widget with real data

**Minimal change approach:** Do NOT rewrite DashboardPreview.jsx. Find the specific section that renders source counts or status summary. Replace only that section's data source. Leave all other mock data in place for now — document the remaining mocks as TODO.

**Template for the status summary section:**

```jsx
// Replace mock status counts with real data
const [sourceStatus, setSourceStatus] = useState(null);
const [statusLoading, setStatusLoading] = useState(true);
const [statusError, setStatusError] = useState(null);

useEffect(() => {
  const token = getAccessToken(); // use existing auth token retrieval
  if (!token) return;
  
  getSourceStatus('AE', token)
    .then(data => {
      setSourceStatus(data);
      setStatusLoading(false);
    })
    .catch(err => {
      console.error('Source status error:', err);
      setStatusError(err.message);
      setStatusLoading(false);
    });
}, []);

// In render:
{statusLoading && <SourceStatusSkeleton />}
{statusError && <SourceStatusError onRetry={() => { /* re-fetch */ }} />}
{sourceStatus && (
  <SourceStatusSummary
    summary={sourceStatus.summary}
    total={sourceStatus.total_sources}
    lastRunAt={sourceStatus.last_run_at}
  />
)}
```

### Step 6: Verify Coverage.jsx source list is accurate

Open `product/regradar/web/src/components/Coverage.jsx`.

The UAE source list shown publicly must match the 13 READY sources from sources.json. Count the enabled, non-disabled AE sources in sources.json:

**Correct 13 enabled AE sources (from sources.json, enabled:true, status:active):**
1. Central Bank of the UAE (centralbank.ae) — AE-central-bank-of-the-uae
2. Dubai Virtual Assets Regulatory Authority (VARA) — AE-dubai-virtual-assets-regulatory-authority-vara
3. Dubai Financial Services Authority (DFSA) — AE-dubai-financial-services-authority-dfsa
4. Abu Dhabi Global Market (ADGM) — AE-abu-dhabi-global-market-adgm
5. UAE Ministry of Finance — AE-uae-ministry-of-finance
6. UAE Legislation Portal — AE-uae-legislation-portal
7. UAE Financial Intelligence Unit (UAEFIU) — AE-uae-financial-intelligence-unit-uaefiu
8. DIFC Laws and Regulations — AE-difc-laws-and-regulations
9. UAE Ministry of Economy — AE-uae-ministry-of-economy
10. VARA Enforcement Notices — AE-vara-enforcement
11. CBUAE Regulations Sub-page — AE-cbuae-regulations
12. UAE FIU Circulars and Notices — AE-uaefiu-circulars
13. DFSA Regulatory Notices — AE-dfsa-notices

If Coverage.jsx does not show these 13 specifically, update the data. Do not add sources that are disabled or not enabled in sources.json.

The limitation note in Coverage.jsx must mention: FTA (disabled_external_access), SCA (disabled_navigation_only), UAE e-Laws/MOJ (disabled_external_access), AE-adgm-fsra-rules (disabled_external_access), AE-difc-legislation (disabled_navigation_only).

### Step 7: Run validation

```bash
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar

# Backend syntax check
python -m compileall app run.py -q

# Test the new endpoint locally (start the API first)
python run.py api --port 5001 &
sleep 3

# Test with no auth (should fail 401)
curl -s http://localhost:5001/api/v1/sources/status | python -m json.tool

# Test with auth (get a token first)
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"'"$API_USERNAME"'","password":"'"$API_PASSWORD"'"}' \
  | python -m json.tool | grep access_token | cut -d'"' -f4)

curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/v1/sources/status?market=AE \
  | python -m json.tool

# Frontend build (from web/ directory)
cd web
npm run build

# Check for lint errors
npm run lint
```

Expected API response (example with real data):
```json
{
  "market": "AE",
  "sources": [
    {
      "source_id": "AE-vara-enforcement",
      "name": "VARA Enforcement Notices",
      "change_status": "UNCHANGED",
      "extraction_quality": "GOOD",
      "extracted_chars": 4821,
      "last_run_at": "2026-06-10T09:14:22Z"
    },
    ...
  ],
  "summary": {
    "FIRST_SEEN": 0,
    "UNCHANGED": 8,
    "CHANGED": 1,
    "FAILED": 0,
    "QUALITY_DROP": 0,
    "NOT_RUN": 4
  },
  "total_sources": 13,
  "last_run_at": "2026-06-10T09:14:22Z",
  "disclaimer": "Not legal advice. For monitoring information only."
}
```

Expected behavior if source_runs.jsonl is empty or missing:
```json
{
  "market": "AE",
  "sources": [...all sources with change_status: "NOT_RUN"...],
  "summary": { "NOT_RUN": 13 },
  "total_sources": 13,
  "last_run_at": null,
  "disclaimer": "Not legal advice. For monitoring information only."
}
```

---

## Acceptance Criteria (Testable)

1. `GET /api/v1/sources/status?market=AE` returns HTTP 200 with JSON body matching the expected structure
2. Response includes `sources` array with at least the 13 enabled AE sources from sources.json
3. Response includes `summary` with status counts (all counts >= 0)
4. Response includes `disclaimer` field with "Not legal advice" text
5. Dashboard source status widget shows data from the API (not hardcoded mock numbers)
6. If source_runs.jsonl is empty or missing, dashboard shows "No monitoring runs yet" empty state — not a crash or an error
7. `python -m compileall app run.py -q` passes with no errors
8. `npm run build` from web/ passes (chunk-size warning is acceptable, errors are not)
9. Coverage.jsx UAE source list shows exactly 13 enabled sources with correct names and official URLs
10. Coverage.jsx limitation note mentions FTA and SCA as not currently accessible

---

## Validation Commands

```bash
# Backend compile check
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar
python -m compileall app run.py -q

# Frontend build
cd web && npm run build

# Frontend lint (passes with known pre-existing warning only)
npm run lint

# Run a source readiness record (updates source_runs.jsonl)
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar
python run.py source-readiness --market AE --record-run

# Verify source history
python run.py source-history --market AE --limit 5

# Start API and test endpoint (manual)
python run.py api --port 5001
```

---

## Rollback Plan

This task modifies 3 files:
1. `router.py` — new endpoint added (no existing endpoints modified)
2. `api.js` — new function added (existing functions not modified)
3. `DashboardPreview.jsx` — one section updated

**Rollback steps:**
```bash
# Option 1: Delete new endpoint from router.py (1-2 lines)
# Revert: remove the new @api_router.get("/sources/status"...) function block

# Option 2: Full git rollback
git stash
# or
git checkout main
git branch -D feat/real-source-status-dashboard
```

Changes are additive — nothing existing is deleted. Rollback risk is minimal.

---

## Copy-Paste Implementation Prompt for Claude / Codex

Use this prompt to continue implementation in a new session:

---

```
You are implementing a specific task for the StatuteProof product codebase.

Working directory: /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar

TASK: Wire real source status data from source_runs.jsonl to the authenticated dashboard.

BEFORE WRITING ANYTHING:
1. Create a git branch: git checkout -b feat/real-source-status-dashboard
2. Read these files first (do not skip this step):
   - app/source_runs.py (understand latest_runs() return structure)
   - app/source_readiness.py (understand load_market_sources() and build_readiness_report())
   - app/api/v1/router.py (understand existing endpoint pattern and auth)
   - web/src/components/DashboardPreview.jsx (understand current mock data structure)
   - web/src/api.js (understand current API call pattern)
   - sources.json (list of AE sources — find all with enabled:true and status:active for jurisdiction AE)
3. DO NOT rewrite files from scratch. Make minimal targeted changes only.

WHAT TO BUILD:
1. Add GET /api/v1/sources/status endpoint to app/api/v1/router.py
   - Requires JWT auth (use existing _get_current_user dependency)
   - Query param: market (default 'AE')
   - Read latest run per source from source_runs.jsonl via app/source_runs.latest_runs(market)
   - Read source list from sources.json via app/source_readiness.load_market_sources(market)
   - Return: { market, sources (list), summary (status counts), total_sources, last_run_at, disclaimer }
   - Disclaimer text must be: "Not legal advice. For monitoring information only."
   - If source_runs.jsonl is missing or empty: return all sources with change_status="NOT_RUN", not an error
   - Handle both source_id and name as lookup keys in latest_runs dict

2. Add getSourceStatus(market, accessToken) to web/src/api.js
   - Match the existing fetch pattern in api.js (same auth header approach)
   - Return the parsed JSON from /api/v1/sources/status

3. Update web/src/components/DashboardPreview.jsx
   - Import getSourceStatus from api.js
   - Add useEffect to fetch on mount
   - Add loading skeleton, empty state, error state
   - Replace ONLY the source status summary section with real data
   - Leave all other mock data as-is (add TODO comments to remaining mocks)

4. Verify web/src/components/Coverage.jsx
   - The UAE source list must show the 13 enabled AE sources from sources.json
   - Add limitation note if missing: FTA and SCA are not currently accessible from outside UAE

CONSTRAINTS:
- No new npm packages. Use only what is already installed.
- No changes to existing endpoints. Only add the new one.
- No legal advice language. Include disclaimer field in API response.
- No SAMPLE label needed on real source status data — only on demo/fake content.
- Do not claim complete UAE coverage. Limitations must be visible.
- No "prevent fines", "guarantee compliance", "replace lawyers" language anywhere.

VALIDATION (run these before declaring done):
  python -m compileall app run.py -q       # must pass with no errors
  cd web && npm run build                   # must pass (chunk-size warning OK, errors not OK)
  npm run lint                              # must pass (pre-existing TanStack warning OK)
  python run.py source-readiness --market AE --record-run   # run to populate source_runs.jsonl
  python run.py source-history --market AE --limit 5        # verify records exist

ROLLBACK: Changes are additive (new endpoint + new function + minimal component edit). Rollback = git stash or delete the branch.

Do not proceed past reading the files until you have confirmed the structure of latest_runs() return value.
```

---

---

*Not legal advice. Internal implementation document.*
