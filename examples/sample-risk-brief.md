# SAMPLE / FAKE — FOR TESTING ONLY. NOT A REAL REGULATORY ALERT.

Source: SAMPLE VARA — VASP Fee Schedule Page
Run ID: SAMPLE-20260611-001
Detected: 2026-06-11T09:15:00Z
Change status: CHANGED
Evidence record: ER-SAMPLE-20260611-001 (status: complete)

---

## Summary

The SAMPLE VARA fee schedule page shows a text change in the annual license fee row for VASP intermediaries. The previous normalized text stated "AED 25,000 annually." The current normalized text states "AED 35,000 annually." Change detected during the 09:00 UTC run on 2026-06-11. No effective date is stated in the changed text.

---

## Risk Assessment

Risk level: HIGH
Risk score: 78
Score components:

- Source authority: 25/30 — VARA is the primary VASP regulator in the UAE. Direct fee schedule change.
- Change materiality: 30/30 — Fee increase from AED 25,000 to AED 35,000 (40%) for a mandatory license category.
- Operational impact: 15/20 — Direct cost impact on VASP intermediary license holders.
- Enforcement language: 8/20 — No enforcement or penalty language visible in the changed section. However, fee deadlines are usually in a separate circular.

Confidence: 0.65
Human review required: YES — risk score >= 70 and confidence < 0.70.

---

## Affected Entities

Source text says: "VASP intermediaries."
Note: "VASP intermediaries" is copied from the SAMPLE source text. The exact scope of this category should be verified against VARA's current classification guidance.
Ambiguity: Does this category include all VASP intermediary license types or a specific subcategory? Source text does not specify. Flag for legal review.

---

## Key Changes

From the SAMPLE diff excerpt:

```
- Annual license fee for VASP intermediaries: AED 25,000
+ Annual license fee for VASP intermediaries: AED 35,000
```

No other sections changed in the SAMPLE run.

---

## Ambiguity Notes

1. Effective date: No effective date stated in the changed section. May be in a separate VARA circular.
2. Entity scope: "VASP intermediaries" category boundaries not defined in this page.
3. Source limitation: SAMPLE PDF extraction quality is LIMITED. Footnotes may contain additional conditions not captured.

---

## Evidence Trail

Evidence record ID: ER-SAMPLE-20260611-001
Evidence record status: complete
Raw hash: a3f1e2b4c5d6e7f8a3f1e2b4c5d6e7f8a3f1e2b4c5d6e7f8a3f1e2b4c5d6e7f8
Normalized hash: b4e2f1a3c6d5e8f7b4e2f1a3c6d5e8f7b4e2f1a3c6d5e8f7b4e2f1a3c6d5e8f7
Diff excerpt: See above (Key Changes section).
Snapshot path: SAMPLE/data/source_snapshots/2026-06-11/AE/SAMPLE-VARA-FEE/SAMPLE-20260611-001/
proof_quality: LIMITED (PDF extraction; footnotes may be incomplete)

---

## Recommended Actions

The following are suggested review steps only. They are not legal instructions or compliance decisions.

1. Compliance teams with active VASP intermediary licenses may want to verify the fee change directly on the VARA official fee schedule page.
2. Finance teams may want to review the impact on the next license renewal budget.
3. Legal or compliance counsel may want to check for a related VARA circular with an effective date and transition terms.

---

## Disclaimer

StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report.

---

# SAMPLE / FAKE — END OF BRIEF
