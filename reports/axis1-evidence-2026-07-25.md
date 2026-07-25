# Axis 1 — EVIDENCE: 35 → measured

Branch `tenten`. Nothing deployed. Every number below comes from
`product/regradar/tools/measure_evidence_axis.py`, which is committed so the same
command produces the before/after comparison rather than a recollection of one.

## Before → after

| Instrument | Before | After |
|---|---|---|
| public `/verify` on real stored records | 41 / 143 (28.7%) | **108 / 108 real evidence records (100%)** |
| `run.py verify-trail` | 149 verified, **855 divergent**, 426 unverifiable | 825 verified, **0 divergent**, 605 unverifiable |
| Hash chain | intact, 24 records | intact, 24 records (unchanged) |

The DoD asked for ≥95% verified over ≥100 real records. Measured: **108 real
records, 100%**.

## What was actually wrong

Not tampering, and not what the audit hypothesised. `normalization_reproducible`
re-derives `normalize_for_change_hash(raw.txt)` and compares it to the stored
`normalized.txt`. That is a statement about the **normalizer**, not about the
evidence — and it was hard-gating `verified`.

`NORMALIZATION_VERSION` is 3 today. The store holds records from at least three
generations: the **same** stored `raw.txt` is on record producing 51,148 / 43,717 /
42,173 normalized characters. So every older record failed a check it could never
pass, and the customer-facing endpoint reported genuine untampered evidence as
unverified — in front of the auditor it exists to satisfy.

The decisive measurement before changing anything: of 143 sampled records, **79
failed ONLY this check while passing BOTH hash seals** (`raw_bytes_match` and
`normalized_bytes_match`, 79/79 each). Their bytes are provably the sealed bytes.

## The fix

`normalization_reproducible` now:

- **passes** when re-derivation matches;
- **fails** when the record declares the version the verifier is running and
  re-derivation still fails — a real defect, kept sharp;
- **skips, stating why**, when the record declares an older version or none, because
  a re-derivation under an unknown historical normalizer is not a meaningful test.

Integrity is untouched. It lives in the seals, and four tests pin that tampering
with either `raw.txt` or `normalized.txt` still fails. The same rule now governs
`verify-trail`, sharing one version parser so the two instruments cannot drift —
the field is written as `3`, `"1.0"` and absent across vintages (4 / 754 / 672 in
the live trail), so a naive `isinstance(int)` check would have misread the majority.

The published spec (`docs/EVIDENCE-VERIFICATION-SPEC.md`, served at
`/api/verify-spec`) now describes this, including the instruction that an auditor
should read "skipped" as *not applicable to this vintage*, never as *not checked*.

## Two things I got wrong along the way

**My own harness fabricated 10 failures.** `Path.read_text()` applies
universal-newline translation, turning a stored CRLF into LF and changing the bytes
before hashing. Ten records "failed" `raw_bytes_match` because of my measurement,
not the product. Fixed with `newline=""`.

**My first sample was date-biased.** Snapshot paths sort by date, so taking the
first 200 sampled one vintage and reported it as the whole store. The sampler now
strides across the range. This mattered: it moved the headline from 83.9% to 56.5%
of *all* artifacts — while the real-evidence-record figure held at 100%.

## A real gap this surfaced, not yet fixed

**557 of 1317 stored artifacts carry no hashes at all** — no `normalized_hash`, no
`raw_hash`, no `record_hash`. They are not evidence records, and the verifier is
right to reject them; loosening that would be the dishonest fix.

It is a bounded incident, not a live bug: 116 on 2026-07-03, 416 on 07-04, 2 on
07-05, and zero on either side (105 clean on 06-19, 20 clean on 07-25). Whatever
ran on 3–5 July wrote proofs without sealing them. Those records cannot be made
verifiable after the fact — the question is whether the sources involved need
re-capture. **Not silently dropped from any count**: the measurement tool reports
them as their own bucket on every run.

## Coverage change to be aware of

Fixing the audit-truth files exposed that my earlier demotion of
`AE-vara-regulatory-notices-and-enforcement-index` (no `proof_path`, zero baseline
runs) reduced **enforcement** fresh-alert coverage from 2 sources to 1. The test
floor moved from `>= 2` to `>= 1` with the reason written into the test rather than
the number quietly lowered. The published sales claim in
`reports/source_signal_quality_audit.json` and `web/src/data/sourceQualityAudit.ts`
said "41 fresh-alert-eligible"; corrected to 40 in both, along with the VARA family
row (fresh 4→3, candidate 0→1).

## Still open on this axis

- `record_hash` covers only the 24-record chained tail; the earlier 1406 records can
  be deleted or reordered without detection. The DoD's "chain covers whole trail" is
  **not** met.
- The 557 unsealed artifacts above.
