# StatuteProof — Authenticated Dashboard Specification

**Version:** 1.0  
**Date:** 2026-06-12  
**Status:** Implementation-ready  
**Not legal advice. Internal spec only.**

---

## Overview

This document specifies the authenticated app dashboard — the first screen a logged-in pilot customer sees. The dashboard must immediately demonstrate that monitoring is real, running, and producing evidence. Fake/mock data in the dashboard is a trust-destroying pattern for compliance buyers.

Current state: Dashboard is demo-mode per HANDOFF.md. All widgets use frontend mock data.

---

## 1. Navigation Structure

### Left Sidebar (Persistent)

```
[StatuteProof Logo]

Navigation:
─────────────
Dashboard        (house icon)
Sources          (globe/link icon)
Alerts           (bell icon)
Evidence         (shield/hash icon)
Briefs           (document icon)
Review Queue     (checkmark icon — shown for Reviewer/Admin/Owner only)

─────────────
Settings         (gear icon)
  ↳ Organization
  ↳ Team
  ↳ Sources
  ↳ Notifications
  ↳ Billing

─────────────
[User Avatar]
[User Name]
[User Role badge]
[Log out]
```

### Top Bar

- Page title (current page name)
- Organization name (top-right)
- Notification bell icon (with count badge if unread notifications)
- User avatar dropdown (profile, settings, log out)

### Mobile / Collapsed Sidebar

On mobile or narrow viewports:
- Sidebar collapses to icon-only
- Tap any icon → expands label and sub-items
- Dashboard, Alerts, Evidence are the three primary mobile navigation targets

---

## 2. Dashboard Page — 8 Widgets

The dashboard is a grid of 8 widgets. Layout: 2 columns on desktop, 1 column on mobile.

### Widget 1: Source Status Overview

**Position:** Top-left (large)  
**Title:** "Source Status"  
**Data:** Count of sources by status from latest monitoring run  
**Display:**

```
Source Status
─────────────────────────────────
  [N] ACTIVE       [green dot]
  [N] CHANGED      [green badge]
  [N] FAILED       [red dot]
  [N] QUALITY_DROP [amber dot]
  [N] PAUSED       [grey dot]
─────────────────────────────────
Last run: [timestamp relative — e.g., "2 hours ago"]
[View all sources →]
```

**Empty state:** "No sources configured. [Configure sources]"  
**Error state:** "Could not load source status. [Retry]"  
**Click:** → /app/sources

---

### Widget 2: Active Alerts

**Position:** Top-right (large)  
**Title:** "Alerts Pending Review"  
**Data:** Unreviewed alerts by risk level

```
Alerts Pending Review
─────────────────────────────────
  [N] HIGH         [red badge]
  [N] MEDIUM       [amber badge]
  [N] LOW          [grey badge]
─────────────────────────────────
  [N] Total pending review
[View alerts →]
```

**Empty state:** "No alerts pending review."  
**Error state:** "Could not load alerts. [Retry]"  
**Click:** → /app/alerts

---

### Widget 3: Recent Evidence Records

**Position:** Second row, left  
**Title:** "Recent Evidence"  
**Data:** Last 5 evidence records across all sources

```
Recent Evidence
─────────────────────────────────
[source name]         [CHANGED] [timestamp]
[source name]         [UNCHANGED] [timestamp]
[source name]         [FIRST_SEEN] [timestamp]
[source name]         [UNCHANGED] [timestamp]
[source name]         [FAILED] [timestamp]
─────────────────────────────────
[View all evidence →]
```

**Empty state:** "No evidence records yet. Your first run will complete within 24 hours."  
**Click:** → /app/evidence

---

### Widget 4: Briefs Ready

**Position:** Second row, right  
**Title:** "Briefs"  
**Data:** Counts by state

```
Briefs
─────────────────────────────────
  [N] Approved — ready to export   [green]
  [N] Needs review                 [amber]
  [N] Draft                        [grey]
─────────────────────────────────
[View briefs →]
```

**Empty state:** "No briefs generated yet. Briefs are created from approved alerts."  
**Click:** → /app/briefs

---

### Widget 5: Review Queue

**Position:** Third row, full-width  
**Title:** "Review Queue"  
**Data:** Items currently waiting for human review  
**Shown to:** Reviewer, Admin, Owner only (hidden for Compliance User and Auditor)

```
Review Queue
─────────────────────────────────────────────────────
Source                  Risk        Type            Age
VARA — Enforcement      HIGH        RULEBOOK_UPDATE  2h
CBUAE — Regulations     MEDIUM      CIRCULAR_UPDATE  1d
─────────────────────────────────────────────────────
[Go to review queue →]
```

**Empty state:** "Review queue is empty. No items waiting for approval."  
**Note:** Review queue items cannot be approved directly from widget — click through to full review page.

---

### Widget 6: Source Health

**Position:** Third row, right (or fourth row)  
**Title:** "Source Health"  
**Data:** Last extraction quality rating per source

```
Source Health
─────────────────────────────────────────────────
VARA — Enforcement         [GOOD]    Updated 2h ago
CBUAE Regulations          [GOOD]    Updated 2h ago
DFSA Rules                 [GOOD]    Updated 2h ago
DFSA Notices               [GOOD]    Updated 2h ago
ADGM FSRA                  [GOOD]    Updated 2h ago
DIFC Laws                  [MEDIUM]  Updated 2h ago
UAE FIU Circulars          [GOOD]    Updated 2h ago
Ministry of Finance        [GOOD]    Updated 2h ago
UAE Legislation Portal     [MEDIUM]  Updated 2h ago
Ministry of Economy        [GOOD]    Updated 2h ago
─────────────────────────────────────────────────
[View source details →]
```

**Limitation row:** "Note: Some sources have known access limitations. [View details]"

---

### Widget 7: Last Run Summary

**Position:** Fourth row, left  
**Title:** "Last Monitoring Run"  
**Data:** Most recent monitoring run statistics

```
Last Monitoring Run
─────────────────────────────────
  Completed:  [timestamp — "Today at 09:14 UTC"]
  Sources run: [N]
  Changed:     [N]
  Unchanged:   [N]
  Failed:      [N]
  Quality drops: [N]
─────────────────────────────────
Next run: [scheduled time]
[View run history →]
```

**Empty state:** "No monitoring runs completed yet. First run scheduled within 24 hours."

---

### Widget 8: Onboarding Checklist

**Position:** Top (shown prominently until complete, then collapsed/hidden)  
**Title:** "Setup Progress"  
**Shown:** Only until all checklist items complete

```
Setup Progress
─────────────────────────────────
[x] Account created
[x] Sources configured (9 sources)
[ ] First monitoring run complete
[ ] First brief ready for review
[  ] Invite a team member (optional)
─────────────────────────────────
[3 of 5 complete]
```

**After completion:** Widget hidden. User can re-show via Settings.

---

## 3. Alerts Table — Full Spec

**Route:** /app/alerts  
**Title:** "Alerts"

### Filters (top of page)

- Filter by risk level: ALL / LOW / MEDIUM / HIGH (radio buttons or tabs)
- Filter by review status: ALL / Pending review / Approved / Rejected
- Filter by regulator: Multi-select dropdown
- Filter by source: Multi-select dropdown
- Date range: from/to date picker
- Search: free text search on source name and change type

### Table Columns

| Column | Type | Sortable | Notes |
|--------|------|---------|-------|
| Source | Text + logo space | Yes | Source name + regulator below in smaller text |
| Status | Badge | Yes | CHANGED/FIRST_SEEN/etc. with color |
| Risk | Badge | Yes | LOW/MEDIUM/HIGH with color |
| Change Type | Text | Yes | RULEBOOK_UPDATE, CIRCULAR_UPDATE, etc. |
| Detected | Relative time + hover for full UTC timestamp | Yes (default sort, desc) | "2 hours ago" |
| Review Status | Badge | Yes | DRAFT/APPROVED_FOR_WEEKLY/etc. |
| Actions | Button group | No | View evidence, View diff, Review, Export |

### Status Badge Colors (Table)

| Status | Background | Text | Border | Tooltip |
|--------|-----------|------|--------|---------|
| FIRST_SEEN | #1D4ED8 (blue-700) | White | None | "First snapshot stored. Baseline established." |
| UNCHANGED | #374151 (grey-700) | #9CA3AF (grey-400) | None | "No changes detected since last run." |
| CHANGED | #166534 (green-800) | #86EFAC (green-300) | 1px #22C55E | "Text change detected. Review evidence record." |
| FAILED | #991B1B (red-800) | #FCA5A5 (red-300) | 1px #EF4444 | "Source fetch or extraction failed. Check source." |
| QUALITY_DROP | #92400E (amber-800) | #FCD34D (amber-300) | 1px #F59E0B | "Extraction quality dropped. Changes may be missed." |
| SOURCE_STRUCTURE_CHANGED | #5B21B6 (purple-800) | #C4B5FD (purple-300) | 1px #8B5CF6 | "Source HTML structure changed. Adapter may need updating." |

### Row Actions

- **View evidence** — opens evidence record detail page
- **View diff** — opens diff viewer (disabled/greyed if no diff available)
- **Review** — opens review panel (disabled for Compliance User and Auditor roles)
- **Export** — downloads evidence record as JSON (requires COMPLETE status)

### Row Expansion (click row)

Clicking a row expands an inline detail panel showing:
- Evidence record ID (monospace)
- Official URL (clickable)
- Previous hash (8-char prefix, monospace)
- Current hash (8-char prefix, monospace)
- Extraction quality
- Changed blocks count
- Confidence level
- Affected entities (text)
- [View full evidence record] button
- [View full diff] button

### Empty State

```
No alerts yet.

Your monitoring is running. When a source change is detected, 
it will appear here with an evidence record and diff.

Your first monitoring run is scheduled to complete within 24 hours.

[View sources]   [View sample alert]
```

---

## 4. Source Status Badges — Full Spec

### Design Tokens for Status Badges

All status badges use:
- Background color: dark variant (contrast-accessible on dark navy background)
- Text color: light variant matching the status color family
- Optional: 1px border for CHANGED/FAILED/QUALITY_DROP to add emphasis
- Minimum size: 80px wide, 22px tall
- Font: 11px/12px, uppercase, letter-spacing 0.5px
- Border radius: 4px (not pill shape — this is a compliance tool, not consumer app)

### Implementation CSS Classes

```css
.badge-first-seen {
  background: #1e3a5f;
  color: #60a5fa;
  border: 1px solid #3b82f6;
}

.badge-unchanged {
  background: #1f2937;
  color: #6b7280;
}

.badge-changed {
  background: #14532d;
  color: #86efac;
  border: 1px solid #22c55e;
}

.badge-failed {
  background: #450a0a;
  color: #fca5a5;
  border: 1px solid #ef4444;
}

.badge-quality-drop {
  background: #451a03;
  color: #fcd34d;
  border: 1px solid #f59e0b;
}

.badge-structure-changed {
  background: #2e1065;
  color: #c4b5fd;
  border: 1px solid #8b5cf6;
}
```

---

## 5. Filter and Sort Behavior

### Sort Behavior

- Default sort: Detected timestamp, descending (newest first)
- Secondary sort (same timestamp): Source name, ascending
- Sort state persists within session (not persisted to DB)
- Sort direction toggle: click column header once for asc, twice for desc, third click clears sort

### Filter Behavior

- Filters are combinable (AND logic)
- Applied filters shown as "chips" above the table with remove (×) buttons
- "Clear all filters" button appears when any filter is active
- Filter state persists within session (not persisted to DB)
- URL query params updated when filters change (so filtered views are shareable via link)

### Pagination

- Default: 25 rows per page
- Options: 25 / 50 / 100
- Page indicator: "Showing 1-25 of [N] alerts"
- Keyboard navigation: ← → for pagination

---

## 6. Source Card Design (Sources Page)

### Card Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ [OFFICIAL]  [ACTIVE]                            [Tier: P0]      │
│                                                                  │
│ VARA — Enforcement Notices                                       │
│ Dubai Virtual Assets Regulatory Authority                        │
│                                                                  │
│ URL: https://www.vara.ae/en/enforcement/                         │
│ Category: financial_regulator  |  Frequency: Daily              │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│ Last checked: 2 hours ago (2026-06-12 09:14 UTC)               │
│ Change status: UNCHANGED                                         │
│ Extraction quality: GOOD (4,821 chars)                          │
│ Current hash: 7c1a9b3e... (normalized)                          │
│ Next check: in 22 hours                                         │
│ ─────────────────────────────────────────────────────────────── │
│ Proof readiness: COMPLETE                                        │
│                                                                  │
│ [View run history]  [View evidence]  [Pause]                    │
└─────────────────────────────────────────────────────────────────┘
```

### Card Color Rules

- Card border-left color matches current status badge color
- CHANGED → green left border (3px)
- FAILED → red left border (3px)
- QUALITY_DROP → amber left border (3px)
- UNCHANGED / FIRST_SEEN → no accent border (or very dim grey)

### Card Badge Labels

- "OFFICIAL" badge: blue background — source is from StatuteProof's validated UAE pack
- "CUSTOM" badge: slate/dark background — user-added custom source
- "PAUSED" badge: grey, shown when source is manually paused
- Tier: P0 (core), P1 (legislative), P2 (supporting), shown in smaller text top-right

---

## 7. Evidence Record Card (Evidence Page)

### Card Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ EVR-2026-0610-VARA-ENF-001                       [COMPLETE]     │
│                                                                  │
│ VARA — Enforcement Notices                    [CHANGED] [HIGH]  │
│ Dubai Virtual Assets Regulatory Authority                        │
│ Detected: 2026-06-10 09:14:22 UTC                               │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│ Previous hash: a3f8d2c1...  (2026-06-03)                        │
│ Current hash:  7c1a9b3e...  (2026-06-10)                        │
│ Extraction: Playwright  |  Quality: GOOD  |  Chars: 4,821      │
│ Diff: Available (3 blocks changed)                              │
│ ─────────────────────────────────────────────────────────────── │
│ Review status: [DRAFT — PENDING REVIEW]                         │
│                                                                  │
│ [View diff]  [Start review]  [Export]                           │
│                                                                  │
│ Not legal advice. Verify against official source.               │
└─────────────────────────────────────────────────────────────────┘
```

### Evidence Record Empty State

```
No evidence records yet.

When StatuteProof detects a change on a monitored source, 
an evidence record will be created here. Evidence records 
include the SHA-256 hash, diff, and full audit trail.

Your first monitoring run completes within 24 hours.

[View sources]   [View sample evidence record]
```

---

## 8. Alert Card (Alert Detail Page)

### Alert Detail Card Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Alert: ALD-2026-0610-VARA-ENF-001                               │
│                                                                  │
│ VARA — Enforcement Notices                       [HIGH RISK]    │
│ Change type: RULEBOOK_UPDATE                                     │
│ Detected: 2026-06-10 09:14:22 UTC                               │
│ Confidence: MEDIUM                                              │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│ Risk score: 74/100                                              │
│ Obligation language detected: YES                               │
│ Deadline/effective date: YES                                    │
│ Penalty/fine language: YES                                      │
│ AML/CFT reference: NO                                           │
│ Licensing change: YES                                           │
│                                                                  │
│ Changed excerpts (from diff):                                   │
│ ─────────────────────────────────────────────────────────────── │
│ + Virtual Asset Exchange licensees must submit monthly risk      │
│ + assessments to VARA by the 15th of each calendar month.       │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ Affected entities (rule-based — verify against official source): │
│ VASP licence holders, VA exchange operators, VARA-licensed firms │
│                                                                  │
│ Suggested review steps:                                         │
│ Review the full enforcement notice at the official URL.         │
│ Assess impact on your compliance programme with your legal team.│
│                                                                  │
│ Limitations: HIGH risk alerts require human review.             │
│                                                                  │
│ Evidence record: EVR-2026-0610-VARA-ENF-001  [View →]          │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│ REVIEW STATUS: DRAFT — HOLD FOR REVIEW                          │
│ ─────────────────────────────────────────────────────────────── │
│                                                                  │
│ [View evidence]  [View diff]  [Approve for weekly brief]        │
│ [Reject]         [Escalate for legal review]                    │
│                                                                  │
│ ⚠ Not legal advice. This alert is for monitoring information    │
│   only. Verify against the official source and consult your     │
│   legal or compliance counsel before taking any action.         │
└─────────────────────────────────────────────────────────────────┘
```

### Alert Card States

| State | Visual treatment |
|-------|-----------------|
| DRAFT — no review | Amber pulsing dot next to review status |
| Approved for weekly | Green checkmark, review timestamp and reviewer name shown |
| Approved for urgent | Green checkmark with "URGENT" label, reviewer name shown |
| Rejected | Red X, rejection note shown |
| Needs legal review | Purple flag icon, escalation note shown |
| HIGH risk — force-approve required | Warning banner at top of card: "This HIGH risk alert requires a review note before it can be approved for urgent delivery." |

---

## 9. Loading States

All widgets and tables use skeleton loading states — not spinners. Skeleton should match the approximate shape of the loaded content.

**Widget skeleton:**
```
[Grey rectangle — title bar]
[Grey rectangle — main number]
[Grey line — label]
[Grey line — label]
[Grey line — label]
[Grey rectangle — CTA button]
```

**Table skeleton:**
```
[Grey header row]
[Grey full-width row × 5]
```

No page-level loading spinners except for the initial auth check on page load.

---

## 10. Empty States (New User)

Dashboard empty state (first login, no data):

```
Welcome to StatuteProof.

Your monitoring is being set up.

What happens next:
1. Your configured sources will be checked in the next 24 hours.
2. When a change is detected, you will see an alert here with 
   an evidence record and diff.
3. After review and approval, a brief will be generated.

While you wait:
[View sample alert]   [View sample evidence record]

Setup progress:
[x] Account created
[x] Sources configured (9 sources)
[ ] First run complete
[ ] First alert reviewed
[ ] First brief generated
```

---

*Not legal advice. Internal implementation specification.*
