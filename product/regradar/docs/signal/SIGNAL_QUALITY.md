# SIGNAL_QUALITY — Phase 0 Evidence Base (signal-max sprint)

Date: 2026-07-06 · Branch: `signal-max` off main `1e10e9f` · Data: real trail
read-only (`data/source_runs/source_runs.jsonl`, 1,406 runs; snapshots;
`sources.json`).

**Bad news first: of 68 historical CHANGED runs, 63 were replayable, and NOT
ONE is an unambiguous genuine regulatory update.** 59/63 are pipeline or
website noise; 3 are listing-count increments (possible genuine publications);
1 is a real-world ministry rebrand visible only in page chrome. Every alert
this system has ever flagged as CHANGED was, at best, weak metadata signal.
The rubric itself also has a proven substring defect (`"ban" in "bank"` →
True) that manufactured HIGH severities on central-bank pages.

## A. Severity truth — replay of the current rubric over all CHANGED runs

Method: `scripts/signal/replay_severity.py` — for each CHANGED run, diff the
previous vs current normalized snapshots with `app.diff.get_diff`, score with
`app.risk.analyze_risk` at commit `1e10e9f`, compare to the risk recorded at
run time. Full per-run table with human judgment: `judgment_table.md`;
raw rows: `replay_severity.jsonl`.

```
CHANGED runs: 68; replayed: 63 (5 from 2026-05-29/30 predate snapshot storage)
recorded risk_level: absent for 66/68 (field only recorded recently); HIGH ×2 (both 2026-07-05)
replayed: HIGH 17 / MEDIUM 30 / LOW 16
```

Rubric-verdict vs my judgment of each delta (totals; per-run rows in
`judgment_table.md`):

| Judgment class | Runs | What it actually was | Rubric said |
|---|---|---|---|
| ADAPTER_FORMAT | 22 | extraction adapter output format switched/enriched (nav-scrape ↔ "listing items", `Context:` lines added) | 9 HIGH, 8 MEDIUM, 5 LOW |
| CHROME_SHUFFLE | 15 | nav/carousel/banner rotation, marketing-copy reshuffle | mix MEDIUM/LOW, 3 HIGH |
| COUNTER | 6 | visitor/rating counters (`Rated by 1008→1009 People`, `114175→114178 مستخدماً`) | 2 HIGH (CBUAE, via `ban`⊂`bank` + `license`⊂`licensed`), 4 MEDIUM |
| PDF_REFLOW | 6 | PDF extractor change re-flowed identical VARA rulebooks (all 6 on 2026-06-19) | 6 MEDIUM (Arabic path) |
| WRONG_PAGE | 5 | fetch landed on ADGM homepage instead of target page | 3 HIGH, 2 MEDIUM |
| COUNT_CHANGE | 3 | legislation/publication counts changed (UAEFIU 61→62; legislation-portal category counts flip 66↔62) — **possible genuine** | LOW/MEDIUM |
| ERROR_PAGE | 2 | Cloudflare 502 and VARA 404 hashed as baseline, then "recovery" flagged CHANGED | MEDIUM |
| TITLE_FLIP | 2 | DFSA `<title>` toggles `\| DFSA` ↔ `\| DFSA \| THE INDEPENDENT REGULATOR…` (2026-07-05, recorded HIGH at run time) | LOW after cycle-3 fix |
| LANG_FLAP | 1 | same URL served Arabic then English | LOW |
| REBRAND | 1 | Ministry of Economy → "Economy & Tourism" (weak genuine, chrome-level) | LOW |

Disagreement summary: the two 2026-07-05 recorded-HIGH runs replay as LOW
(cycle-3 delta-only scoring works, but the truthful outcome is NO diff — F1).
For the other 61, the run-time record carries no risk_level, so the
"disagreement" is: pipeline said CHANGED, human judgment says 59× noise,
3× possible-genuine, 1× weak-genuine.

### Rubric defects proven during replay (file/line refs)

1. **Substring matching**: `app/risk.py:287` uses `kw in all_text`;
   `"ban" in "bank"` → True (verified). Both CBUAE false HIGHs
   (2026-06-12) matched `['ban', 'license']` on a page whose only change was
   a rating counter. Fix = word-boundary matching (F4).
2. **Arabic branch returns no rule id / matched keywords**
   (`app/risk.py:276-283`) — docstring promises `MEDIUM_ARABIC`; callers get
   `rule=None`. 20 of the 63 replays hit this branch. (F3/F4)
3. **Stale docstring**: `app/risk.py:15` still lists `rate` as a strong
   keyword; the tuple does not contain it.
4. **Error pages become baselines**: 502/404 body was normalized, hashed,
   stored — the *recovery* then alerts as CHANGED. (F1)
5. **Extractor/adapter version changes flag CHANGED**: 22 ADAPTER_FORMAT +
   6 PDF_REFLOW runs = 44% of all historical CHANGED events were caused by
   our own extraction changes, not the regulator. (F1 + reset runbook)

## B. Term reality — frequency over real deltas and documents

Method: `scripts/signal/term_frequency.py`; full output:
`term_frequency_output.txt`. Two corpora: DELTAS = full added+removed text of
the 63 replayed runs (3.40M chars; EN 2.79M / AR 0.61M). DOCS = latest
normalized snapshot of 316 sources (7.97M chars; EN 7.66M / AR 0.31M).

Candidate detection terms with real counts (deltas / docs):

| EN pattern | deltas | docs |
|---|---|---|
| law_ref (Decree-Law / Cabinet Decision / Federal Law No. (n)) | 629 | 1,050 |
| article_ref (Article (n)) | 167 | 3,351 |
| must/shall/required to | 1,589 | 8,990 |
| penalty/fine/sanction | 593 | 2,300 |
| effective from/date | 200 | 208 |
| date (d Month yyyy) | 777 | 800 |
| date (d/m/y) | 19 | 789 |
| amount AED/dirham | 145 | 509 |
| percentage | 182 | 481 |
| in-force/repealed status | 54 | 222 |
| consultation paper/period/closes | 58 | 273 |
| deadline phrases (no later than / within N days) | 6 | 106 |
| licence + category/class/type | 23 | 52 |

| AR pattern | deltas | docs |
|---|---|---|
| قانون اتحادي (federal law) | 242 | 75 |
| قرار (decision) | 257 | 101 |
| مرسوم بقانون (decree-law) | 149 | 74 |
| التزام/يجب/يتعين (obligation) | 369 | 267 |
| درهم (dirham) | 233 | 133 |
| الأصول الافتراضية (virtual assets) | 339 | 98 |
| غسل الأموال / تمويل الإرهاب (AML/CFT) | 54+53 | 87+78 |
| مادة/المادة (article) | 0 | 225 |
| عقوبة/جزاء (penalty) | 85 | 60 |
| ترخيص/رخصة (licence) | 35 | 54 |
| غرامة (fine) | 0 | 11 |
| موعد نهائي/مهلة (deadline) | 0 | 1 |

Named blind spots (contract item B):

- **Arabic deadline vocabulary is effectively absent from the trail** (0
  delta hits, 1 doc hit). Data too thin to build AR deadline detection with
  honest confidence → F3 must route low-confidence Arabic to the explicit
  "human review required" path, not fake it.
- **`غرامة` (fine) and `مادة (n)`** appear in documents but never in deltas —
  historical deltas are noise, so obligation-bearing Arabic has never actually
  flowed through scoring.
- EN deadline phrases are rare in deltas (6) but present in docs (106) —
  detection must run on document/delta text, counts justify F2 patterns.
- Delta corpus top tokens are DIFC asset-URL fragments
  (`difc:12100, media:7218, dubaiintern:3576…`) — noise contaminates any
  naive keyword statistics; cleaning (F1) is a precondition for honest term
  mining.

## C. Noise anatomy — per-source contamination

Method: `scripts/signal/noise_anatomy.py` over the latest normalized snapshot
of 311 sources; markers taken verbatim from the 63-delta judgment. Full table:
`noise_anatomy.jsonl`, `noise_anatomy_output.txt`.

- **92/311 sources (30%) contain ≥1 hard chrome/counter line** — their
  baseline hash flips the moment extraction is cleaned. This is the *minimum*
  reset size; nav-label stripping raises it further (DFSA pages: ~106 of 143
  normalized lines are nav labels; ADGM: ~60-72 of 78-112).
- Worst offenders by marker fraction: `AE-vara-rulebook` (1 line, 100%
  chrome), SCA/UAEFIU listing pages (30%), ADGM family (~10% markers + ~70%
  nav-like), DFSA family (~4% markers + ~75% nav-like).
- Consequence: the coordinated baseline reset (RESET_RUNBOOK.md, F1
  deliverable) must expect **every HTML source to fire CHANGED once**;
  planning number: 92 minimum, realistically ~250-311 of sources with
  snapshots.

## D. Portfolio

See `SOURCE_PORTFOLIO.md`.

## Priority check against the build track list

Phase-0 evidence **confirms the F1→F6 order**: 44% of historical CHANGED
events are self-inflicted (extraction/adapter) → F1 first. The substring
defect (F4 scope) is severe but its worst instances route through noise that
F1 removes; word-boundary fix lands in F4 as planned. F2 patterns are
grounded (table above). F3 must include the honest human-review path (AR
deadline data too thin).
