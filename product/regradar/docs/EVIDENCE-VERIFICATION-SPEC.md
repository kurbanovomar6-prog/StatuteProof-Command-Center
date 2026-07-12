# StatuteProof Evidence Verification — Open Specification (v1)

> **Purpose.** This document describes, in full and without secrets, exactly how a
> StatuteProof evidence record is constructed and how **anyone** — an auditor, a
> regulator, your own IT team — can independently verify its integrity **without a
> StatuteProof account and without trusting StatuteProof**. Verification uses only
> published, standard cryptography (SHA-256) over the bytes you were given.
>
> This is the trust cornerstone of StatuteProof: we are a *notary of official-source
> change*. A notary is only credible if its records can be checked against it.

## 1. What a record attests (and what it does NOT)

An evidence record attests, in a tamper-**evident** way:

- **What** the monitored official source's text was (`raw.txt`) and its
  content-normalized form (`normalized.txt`) at a captured moment;
- **When** it was captured (`timestamp`, UTC);
- **That** these bytes have not been altered *in place* since capture (any edit to
  the stored bytes makes the recomputed hash differ from the sealed hash);
- **Ordering** relative to the previous captured state of the same source
  (`prev_record_hash` chains each record to the one before it).

It does **not** claim to be tamper-**proof**. Honest scope (also stated in the
verifier tool): a clean chain proves there was no *in-place, un-relinked* tampering
since the last known head. An actor who can also *relink* the whole trail could
produce a trail that re-verifies clean. Two things raise that bar and are addressed
in §5: a separately-persisted **head anchor**, and (roadmap) an **external
timestamp anchor** (RFC 3161) that a third party — not StatuteProof — signs.

StatuteProof is not legal advice, not a guarantee of compliance, and not a
certification. Verification proves *integrity of the captured record*, nothing more.

## 2. The hashes (all SHA-256, lowercase hex, prefixed `sha256:`)

| Field | Definition |
|---|---|
| `raw_hash` | `SHA-256( bytes of raw.txt )` — the exact source bytes as captured. In the canonical `evidence-record.json` this is stored as `content.raw_hash`. |
| `current_hash` (normalized) | `SHA-256( bytes of normalized.txt )`, where `normalized.txt = normalize_for_change_hash(raw)` — the content-stable form used for change detection (strips volatile markup/whitespace so a cosmetic republish is not a false change). Stored as `content.current_hash`. |
| `previous_hash` | The `current_hash` of the immediately preceding captured state of the same source (empty for the first-ever capture, `FIRST_SEEN`). Stored as `content.previous_hash`. |
| `record_hash` | The record's own fingerprint — `SHA-256` over its canonical JSON. Two concrete, self-checkable schemes exist. The append-only **trail record** hashes its identifying fields (`app/source_runs.py::compute_record_hash`). The canonical **`evidence-record.json`** carries a top-level `record_hash` and `record_hash_method: content-sha256-v1`, computed as `SHA-256` over the **compact** (`separators=(",", ":")`), **sorted-key**, **UTF-8** (`ensure_ascii=false`) JSON of its `content` block — the single shared function `app/record_hashing.py::canonical_record_hash`, used by both the writer and the public verifier so the two can never drift. |
| `prev_record_hash` | The `record_hash` of the immediately preceding record in the append-only trail. This forms the chain. |

The normalization function `normalize_for_change_hash` is published (see the
`verify.py` shipped inside every Evidence Pack, and the source in
`app/change_hash.py`). You do not need it to verify the *normalized* hash if you were
given `normalized.txt` — just hash the bytes. You need it only if you want to
re-derive `normalized.txt` from `raw.txt` yourself.

## 3. How to verify ONE record (no StatuteProof needed)

Given a record bundle (`raw.txt`, `normalized.txt`, `record.json`):

1. **Recompute the raw hash:** `sha256sum raw.txt` → must equal `record.raw_hash`.
2. **Recompute the normalized hash:** `sha256sum normalized.txt` → must equal
   `record.current_hash`.
3. *(optional, stronger)* **Re-derive normalization:** run the published
   `normalize_for_change_hash` on `raw.txt`; the output must be byte-identical to
   `normalized.txt` (so the "normalized" form was not quietly swapped).
4. **Recompute the record hash:** for a canonical `evidence-record.json`
   (`record_hash_method == "content-sha256-v1"`), serialize `record.content` as
   compact (`separators=(",", ":")`), sorted-key, UTF-8 (`ensure_ascii=false`) JSON
   and `sha256` it → must equal the bare digest in `record.record_hash` (drop the
   `sha256:` prefix). Because `content` includes `current_hash`, `raw_hash`, and the
   previous-side fields, this one fingerprint covers every hash the record asserts:
   altering any field inside `content` makes `record_hash` diverge. (For a source-run
   trail record, the record hash is instead computed over its identifying fields; see
   §4.)

If all match, the record's bytes are exactly what was sealed. Any mismatch =
`divergent` (corrupted or altered) — that is the signal, and it never auto-heals.
This remains tamper-**evident**, not tamper-**proof** (see §1): a `record_hash` that
recomputes proves the content block was not edited *in place*, not that no actor with
full write access re-sealed the whole record.

One-liner anyone can run on the bytes we give them:

```bash
sha256sum raw.txt normalized.txt   # compare against raw_hash / current_hash in record.json
```

Every Evidence Pack ships a standalone `verify.py` that does steps 1–4 offline with
no network and no dependency on StatuteProof.

## 4. How to verify a CHAIN (a source's timeline)

Records for one source form an append-only trail. Each line carries
`prev_record_hash` pointing at the previous line's `record_hash`.

1. Verify each record individually (§3).
2. Walk the trail in append order; for each record after the first, confirm
   `record[i].prev_record_hash == record[i-1].record_hash`.
3. The **first** broken link is reported; everything after a break is untrusted.

A clean chain proves the sequence of captured states was not altered *in place* and
not reordered since it was written.

## 5. Head anchor and external anchoring (raising "evident" toward "proof")

- **Head anchor (implemented):** the live head `record_hash` is also written to a
  separately-persisted head file. On verification, the live head is compared to that
  anchor; a mismatch **reports** a likely delete-then-relink (`anchor_status:
  divergent`). It is advisory (does not fail the run) because legitimate new captures
  advance the head.
- **External timestamp anchor (roadmap, §Public Verifier):** periodically submit the
  head `record_hash` to an **RFC 3161 Time-Stamping Authority** (and/or a public
  transparency log). The TSA — a third party, not StatuteProof — returns a signed
  token binding that hash to a time. A relinked trail cannot reproduce a TSA token
  that predates the relink. This is what upgrades the guarantee from *tamper-evident*
  to *externally-anchored tamper-evident*, and it is verifiable by anyone who trusts
  the TSA, not StatuteProof.

## 6. The Public Verifier (what we expose)

A public, no-login endpoint and page: paste a `record.json` (or upload a bundle /
Evidence Pack), and the verifier runs §3–§4 **client-observable** and returns
`verified` / `divergent` with the exact field that failed — plus, when present, the
external anchor status. The verifier's method is this document; the logic is the
open `verify.py`. Nothing about verification requires trusting StatuteProof's
servers: the math is standard and the bytes are in your hand.

---
*This spec is versioned. v1 covers raw+normalized+record hashing, the append-only
chain, and the head anchor. External RFC 3161 anchoring and signed exports are
tracked additions that only strengthen — never weaken — the above.*
