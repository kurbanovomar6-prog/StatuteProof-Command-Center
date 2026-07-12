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
in §5–§6: a separately-persisted **head anchor**, and an operator-enabled **external
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

**Canonical JSON value types (portability scope, stated plainly).** The
`content-sha256-v1` canonicalization — compact `separators=(",", ":")`,
`sort_keys=True`, `ensure_ascii=false` — is defined over JSON **strings,
integers, booleans, and `null` only**. For those types the byte output is
identical across machines, languages, and JSON tools (jq, Go, JS), so the digest
is reproducible with standard tooling. It deliberately defines **no
float-canonicalization rule**: floating-point `repr` is not guaranteed
byte-identical across languages (Python's `json` output can differ from jq/JS/Go
for the same value), so a float — even a finite one — could verify inside
StatuteProof yet fail an independent re-hash. Sealed `content` therefore **must
not contain floats**; the writers that build sealed content reject float values
(e.g. `app/decision_records.py::_validated_reviewed_copy`), and the seal itself
also refuses non-finite floats (`allow_nan=False` in
`app/record_hashing.py::canonical_record_hash`). `ensure_ascii=false` preserves
UTF-8 verbatim, so non-ASCII text is hashed as its raw UTF-8 bytes with no escape
ambiguity.

The normalization function `normalize_for_change_hash` is published — its source
is `app/text_normalization.py` (the exact function the writer and the public
verifier both import, so they cannot drift). You do not need it to verify the *normalized* hash if you were
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

Every Evidence Pack ships a standalone `verify.py` that recomputes the **raw and
normalized** hashes (steps 1–2) offline against its `manifest.json`, with no network
and no dependency on StatuteProof. The **Regulator Binder**'s `verify.py` goes
further: it also re-seals every included `evidence-record.json` (step 4 — recomputes
`record_hash` over the `content` block) and recomputes the binder-level content
hash. To re-derive step 4 for a plain Evidence Pack, run the compact/sorted-key JSON
`sha256` over `record.content` from the bundled `evidence-record.json` as described
above (or paste the record into the public verifier at `/verify`).

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
- **External timestamp anchor (implemented; optional, dormant by default — see §6):**
  periodically submit the head `record_hash` to an **RFC 3161 Time-Stamping
  Authority**. The TSA — a third party, not StatuteProof — returns a signed token
  binding that hash to a time StatuteProof cannot backdate. A relinked trail cannot
  reproduce a TSA token that predates the relink. This upgrades the guarantee from
  *tamper-evident* to *externally-anchored tamper-evident*, and it is verifiable by
  anyone who trusts the TSA, not StatuteProof. §6 documents exactly how it is stored
  and independently checked.

## 6. External RFC 3161 timestamp anchor (optional)

> **Status: implemented, and *dormant by default*.** This is an operator-enabled
> add-on, not part of the base guarantee. With no configuration it is a complete
> no-op — zero network calls, zero threads, zero files, and the capture pipeline is
> byte-for-byte unchanged; records produced without it stay 100% valid. It is enabled
> only when an operator sets the `RFC3161_TSA_URL` environment variable to a non-empty
> value (`app/rfc3161_anchor.py::anchor_enabled`). There is intentionally no default
> TSA.

### 6.1 What it adds

The internal chain (§4) is tamper-**evident**: it catches in-place, un-relinked edits.
Its honest limit (§1) is that an actor with full write access who *relinks* the whole
trail can still produce a chain that re-verifies clean. An external anchor closes that
gap with something StatuteProof cannot forge: a third-party **RFC 3161 Time-Stamping
Authority (TSA)** signs a token binding the current chain-**head** `record_hash` to a
time StatuteProof cannot backdate. A relinked trail cannot reproduce a TSA token that
predates the relink. This upgrades the guarantee from *tamper-evident* to
*externally-anchored tamper-evident* — checkable by anyone who trusts the TSA, **not**
StatuteProof.

Only the chain **head** is anchored. `app/source_runs.py::_write_chain_head` is the
single chokepoint for every head update — a normal append *and* a retention relink —
and it calls `_maybe_external_anchor` → `rfc3161_anchor.spawn_head_anchor` on a
background daemon thread with a single-in-flight guard, so a source capture never
blocks on the TSA and the TSA is never hammered per-append.

### 6.2 What gets written (the additive sidecar)

The token is persisted as an **additive sidecar** next to `evidence_chain_head.json`;
no existing evidence record, trail line, or head file is ever mutated:

| File | Contents |
|---|---|
| `evidence_chain_head.tsr.json` | JSON sidecar (metadata + base64 token) |
| `evidence_chain_head.tsr` | the raw DER timestamp token, so standard `openssl ts` tooling can read it directly |

The JSON sidecar (`app/rfc3161_anchor.py::request_timestamp` + `maybe_anchor_head`)
carries:

| Field | Meaning |
|---|---|
| `schema_version` | sidecar schema version (`"1.0"`) |
| `token_format` | `"rfc3161-timestamp-token-der-base64"` |
| `token_b64` | the RFC 3161 timestamp token, DER, base64 |
| `tsa_url` | the operator-configured TSA that issued it |
| `digest_hex` | the anchored digest — the head `record_hash`, lowercase hex |
| `digest_algorithm` | always `sha256` |
| `anchored_head_record_hash` | the head `record_hash` this token anchors (equals `digest_hex`) |
| `requested_at` | when StatuteProof requested the token (UTC; advisory) |
| `asserted_time_utc` | the TSA's asserted time, lifted from the token (advisory until verified) |
| `nonce` | random nonce sent in the request, to detect a replayed/substituted response |

The message imprint inside the token is the **raw bytes of the head `record_hash`**
(itself a SHA-256 digest), carried with `hashAlgorithm = sha256` — built exactly the
way `openssl ts -query -digest <hex> -sha256` builds it. Only a genuine 64-char
lowercase SHA-256 head hash is ever submitted; anything else is refused with no request
sent.

### 6.3 How a recipient verifies the token OFFLINE (no trust in StatuteProof)

`app/rfc3161_anchor.py::verify_timestamp_token(token_b64, digest_hex)` runs the
following checks with **no network access**, and returns a fail-closed envelope where
`verified` is `true` only when the imprint **and** the signature pass:

1. **`digest_wellformed`** — `digest_hex` is a 64-char lowercase SHA-256 hex string.
2. **`token_parsed`** — the blob parses as a CMS `SignedData` RFC 3161 timestamp token
   carrying a `TSTInfo`.
3. **`imprint_matches_digest`** — the token's message imprint equals the SHA-256 digest
   you hold (i.e. the head `record_hash`). This is what ties the token to *your* head.
4. **`message_digest_attr_matches_content`** — the signed `message-digest` attribute
   equals the digest of the token's `TSTInfo` eContent, binding the signature to *this*
   TSTInfo.
5. **`signature_valid`** — the TSA's signature over the signed attributes verifies
   against the certificate **embedded in the token** (SHA-2 signature hashes only;
   SHA-1/SHA-224 are refused).

If the signature cannot be checked (no embedded certificate, or the `cryptography`
package is unavailable), the token is reported **unverified** with an explanatory
`skipped` check — never a false pass.

**Standard-tooling equivalent (openssl).** Because the imprint is the raw digest with
`sha256`, the persisted `.tsr` token is verifiable with plain `openssl ts` — nothing
StatuteProof-specific is required:

```bash
# Rebuild the query from the head hash you are checking, then verify the token
# against the TSA roots YOU trust:
openssl ts -query -digest <head_record_hash> -sha256 -out head.tsq
openssl ts -verify -in evidence_chain_head.tsr -queryfile head.tsq \
    -CAfile your-trusted-tsa-roots.pem

# Equivalent, using the digest directly (no query file):
openssl ts -verify -in evidence_chain_head.tsr -digest <head_record_hash> \
    -CAfile your-trusted-tsa-roots.pem
```

`<head_record_hash>` is the bare 64-char hex `record_hash` of the chain head (drop any
`sha256:` prefix); it must equal `anchored_head_record_hash` in the sidecar. The
`-CAfile` you pass is **your own** trusted TSA root set — see §6.4.

### 6.4 Honest scope limit (stated plainly)

`verify_timestamp_token` proves two things and **only** two: that the token was *signed
by the holder of the certificate embedded in it*, and that the imprint it signed
*equals the head `record_hash` you hold*. It does **not** validate the TSA certificate
chain to a trusted root — the module ships **no trust store** — so on its own it does
not establish "signed by a TSA you have independently decided to trust". That final
check is reported as a `skipped` / `not_checked` outcome, never a pass.

The final trust decision belongs to the **recipient**: chain the embedded TSA
certificate to your own trusted TSA roots (the `-CAfile` above). This is deliberate —
whose roots to trust is the verifier's call, not StatuteProof's. We do not overclaim
what the module checks.

This is monitoring evidence, not legal proof. An external anchor strengthens the
integrity signal; it is not a certification, a legal opinion, or a guarantee of
compliance, and it does not change what a record attests in §1.

## 6A. Sealed decision records (reviewer accountability)

Alongside the captured-source evidence trail, StatuteProof can seal a **reviewer's
own decision** about a monitored change into a tamper-evident record. This is a
separate, **per-org**, append-only, hash-chained log (`decision_records`) — it is
NOT the capture chain and does not touch it. Its whole point is individual
accountability: a named reviewer records, **in their own words**, what they
reviewed and what they decided, and StatuteProof seals that statement *unchanged*.
StatuteProof never authors, suggests, scores, or assesses the decision.

### 6A.1 Canonical shape

A sealed decision record is the **same `{content, record_hash, record_hash_method}`
envelope** as an evidence record, so it verifies with the same method (§3, step 4)
and through the same public verifier (§7) with **zero** special handling:

```json
{
  "schema_version": "1.0",
  "decision_id": "dec_<org>_<seq>_<20-hex>",
  "record_hash": "sha256:<64 hex over canonical content>",
  "record_hash_method": "content-sha256-v1",
  "content": {
    "decision_id": "…same…",
    "org_id": 42,
    "chain_seq": 7,
    "prev_decision_hash": "sha256:… (or \"\" for the chain genesis)",
    "decided_by": {"user_id": 108, "display_name": "A. Rahman"},
    "decided_at_utc": "2026-07-12T09:30:00.000000Z",
    "reviewed": { … verbatim copy of the alert's proof block: evidence_record_id,
                  record_hash, run_id, normalized_hash, source_id, source_name,
                  official_url, alert_id … },
    "decision": {"kind": "reviewed", "statement": "<the reviewer's own words>",
                 "checklist_ref": … | null},
    "supersedes_decision_id": null,
    "amendment_reason": null
  }
}
```

Everything load-bearing lives **inside `content`** — including `prev_decision_hash`
and the authoritative `decided_at_utc` — so the single `record_hash` fingerprint
covers all of it. `kind` is one of five neutral, user-selected log labels
(`reviewed` / `acknowledged` / `escalated` / `no_change_needed` /
`action_recorded`); it is never a StatuteProof assessment. Corrections are **new,
linked** records (`supersedes_decision_id` + `amendment_reason`) — the original is
never edited or deleted (database `BEFORE UPDATE`/`BEFORE DELETE` triggers enforce
append-only at the storage layer).

### 6A.2 The seal (identical to evidence records)

`record_hash` is `SHA-256` over the **compact** (`separators=(",", ":")`),
**sorted-key**, **UTF-8** (`ensure_ascii=false`) JSON of the `content` block — the
single shared `app/record_hashing.py::canonical_record_hash`, prefixed `sha256:`.
Recompute it with standard tools over the `content` block you hold; any edit to any
field inside `content` (including the reviewer's `statement`) makes it diverge.

### 6A.3 What a SINGLE decision record proves — and what it does NOT

Verifying one decision record (§3, step 4) proves exactly one thing: **the `content`
block was not edited in place** — the reviewer's sealed words, the time, and the
`reviewed` proof block are intact relative to the seal.

> **Scope limit — read this before trusting a green single-record verify.** A
> self-consistent decision record proves *only its own integrity*. It does **not**
> prove chain membership or authenticity: because a record seals its own `content`,
> **anyone can fabricate a brand-new, internally-consistent decision record** (pick
> any `content`, compute its `record_hash`) and it will verify `true` in isolation.
> A green single-record verify therefore means "these bytes are self-consistent",
> **never** "this decision is a genuine, in-order entry in org X's accountability
> chain". That stronger claim requires verifying the **chain**, not one record.

### 6A.4 Verifying the decision CHAIN (membership + order)

Chain authenticity is established exactly like the evidence trail (§4), over the
per-org sequence:

1. Verify each record individually (§6A.2).
2. Walk the records in `chain_seq` order; for each record after the first, confirm
   `content.prev_decision_hash == the previous record's record_hash` (the first
   record's `prev_decision_hash` is `""` at the chain genesis, or the seal of the
   decision immediately before an exported segment — see below).
3. The **first** broken link is the actionable failure; everything after it is
   untrusted.

Because `prev_decision_hash` is *inside* `content`, editing it breaks the record's
own seal (step 1); the walk (step 2) additionally catches insertion, deletion, and
reordering. `app/decision_records.py::verify_decision_chain` performs exactly this
recompute-and-walk over an org's chain.

**Head divergence (raising "evident" toward "proof").** Like the evidence trail
(§5), the live decision-chain head (`decision_hash` of the MAX-`chain_seq` row) is
also written to a separately-persisted `decision_chain_head.json`.
`app/decision_records.py::verify_decision_head` compares the two and **reports**
divergence (`status: diverged`) — the advisory signal for a full re-seal+relink
with a rewritten head, which the in-table walk alone cannot see. It is advisory and
never mutates anything; a decision chain has no legitimate head rewrite (pure
append), so a divergence always warrants investigation.

### 6A.5 In the Regulator Binder

When a binder is built for an org, it embeds the **contiguous `chain_seq` segment**
of that org's decision chain covering the reporting period, under
`decisions/<decision_id>/decision-record.json`, with a `decisions` sub-manifest
(each record's seal, `prev_decision_hash`, `chain_seq`, and a
`decision_chain_hash` over the sorted decision seals). The first embedded record's
`prev_decision_hash` links to the decision immediately *before* the period
(recorded as `segment_anchor_prev_hash`), which lives in the org's full log outside
the binder. The bundled offline `verify.py` recomputes every decision seal
(§6A.2) **and** asserts each record links to the previous embedded record — so an
examiner confirms both integrity **and** in-segment order with no network and no
StatuteProof code. This is what turns a single-record self-seal (§6A.3) into a
chain-verifiable artifact.

## 7. The Public Verifier (what we expose)

A public, no-login endpoint and page: paste a `record.json` (or upload a bundle /
Evidence Pack), and the verifier runs §3–§4 **client-observable** and returns
`verified` / `divergent` with the exact field that failed — plus, when present, the
external anchor status. The verifier's method is this document; the logic is the
open `verify.py`. Nothing about verification requires trusting StatuteProof's
servers: the math is standard and the bytes are in your hand.

---
*This spec is versioned. v1 covers raw+normalized+record hashing, the append-only
chain, and the head anchor. §6 documents the optional external RFC 3161 timestamp
anchor (implemented, dormant by default); §6A documents sealed reviewer-decision
records (same content-sha256-v1 seal, a separate per-org chain, with the explicit
scope limit that a single-record verify does NOT prove chain membership). Signed
exports remain a tracked addition. These strengthen — never weaken — the above.*
