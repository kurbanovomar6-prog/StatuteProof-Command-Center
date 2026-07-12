# StatuteProof — Evidence Integrity Whitepaper

**Audience:** compliance officers, internal audit, and the external auditors or
examiners who will be asked to rely on StatuteProof evidence.
**Last reviewed:** 2026-07-12. This is a buyer-facing summary of the full open
specification, `docs/EVIDENCE-VERIFICATION-SPEC.md` (published, versioned,
no secrets). Every mechanism below is implemented in the referenced module.

**The one-sentence claim, stated precisely:** StatuteProof evidence records are
**tamper-evident** — any in-place alteration of a sealed record is detectable
by anyone holding the record, using standard SHA-256 and no trust in
StatuteProof. They are not tamper-*proof*, and this document says exactly where
that boundary lies (§6).

---

## 1. What an evidence record attests

When StatuteProof captures a monitored official source, it stores:

- `raw.txt` — the source text exactly as captured;
- `normalized.txt` — a content-stable form used for change detection (strips
  volatile markup/whitespace so a cosmetic republish is not a false change);
  the normalization function is published (`app/text_normalization.py`);
- a UTC capture timestamp;
- SHA-256 hashes of both byte streams (`raw_hash`, `current_hash`);
- the previous capture's hash (`previous_hash`), giving each record its place
  in the source's timeline.

The record attests **what the source said, when it was captured, and that the
stored bytes have not been altered in place since**. It does not attest legal
meaning, completeness of regulatory coverage, or compliance status.

## 2. The self-seal

The canonical `evidence-record.json` seals its own `content` block: a single
top-level `record_hash` is the SHA-256 of the compact, sorted-key, UTF-8 JSON
serialization of that block, under the published scheme id
`content-sha256-v1`. One shared function computes this hash for both the
writer and the verifier, so the two can never drift —
`app/record_hashing.py::canonical_record_hash`, used by
`app/evidence_records.py` (writer) and `app/public_verify.py` (verifier).

Because `content` includes `raw_hash`, `current_hash` and the previous-state
fields, altering **any** field inside the record makes `record_hash` fail to
recompute. The serialization is byte-stable across machines and Python
versions, so an auditor can reproduce it with standard tools.

## 3. The chain

Capture records for all sources are appended to a hash-linked trail
(`data/source_runs/source_runs.jsonl`): each record carries
`prev_record_hash` — the `record_hash` of the record before it — and its own
`record_hash` folds that pointer in (`app/source_runs.py::compute_record_hash`).
Appends are serialized under an exclusive file lock (`fcntl`), and in
normal operation the trail has no update path — records are only ever
appended. The single exception is the audited retention compaction described
below, which necessarily re-links the surviving records — and is precisely
why the separately persisted head anchor (§4) and the external RFC 3161
anchor (§7) exist.

Verifying the chain means: verify each record (§5), then walk the trail
confirming each `prev_record_hash` equals the previous line's `record_hash`.
A clean walk proves the sequence was not altered in place or reordered. The
first broken link is reported; everything after it is untrusted.

Retention compaction (removal of redundant UNCHANGED heartbeats older than 30
days) necessarily re-links the surviving records; this is done through a
single audited code path that recomputes the chain over the survivors
(`app/retention.py`, `app/source_runs.py::relink_chain`) — and it is exactly
why the head anchor and external anchor below exist (§6).

## 4. The head anchor and the daily self-check

- **Head anchor (implemented, always on):** every head update writes the
  current head `record_hash` to a separately persisted head file
  (`app/source_runs.py::_write_chain_head`). Verification compares the live
  chain head against that anchor; a mismatch is reported as a likely
  delete-then-relink (`anchor_status: divergent`).
- **Daily integrity self-check (implemented, always on in production):** a
  read-only systemd job re-hashes every stored snapshot against its sealed
  hash and re-verifies the chain daily; any divergence pages the operator and
  the job exits non-zero (`deploy/systemd/statuteproof-verify.*`,
  `run.py verify-trail-watch`). Divergence never auto-heals — it is the signal.

## 5. How an auditor verifies independently

None of the following requires a StatuteProof account, StatuteProof software,
or trust in StatuteProof's servers.

**a) One record, by hand.** Given `raw.txt`, `normalized.txt`, `record.json`:

```bash
sha256sum raw.txt normalized.txt
# compare against raw_hash / current_hash in record.json
```

Then recompute `record_hash`: serialize `record.content` as compact
(`separators=(",", ":")`), sorted-key, UTF-8 JSON and SHA-256 it; it must
equal the stored `record_hash` (drop the `sha256:` prefix). The exact recipe
is in the open spec §3.

**b) The public verifier (no login).** `POST /api/verify` and the public
`/verify` page accept a pasted record (plus optional raw/normalized bytes) and
run the same checks server-side using the same shared functions — it is
stateless and pure: no filesystem, database, network or auth is touched on
that path (`app/public_verify.py`). The endpoint is rate-limited per IP. The
method it applies is the published spec, so its results can be reproduced
offline by anyone who distrusts it.

**c) Offline `verify.py` in every Evidence Pack.** Every customer-downloadable
Evidence Pack ZIP ships `manifest.json`, the captured bytes, and a standalone,
stdlib-only `verify.py` that re-reads every included snapshot, recomputes its
SHA-256, and prints PASS/FAIL per record — no network, no app imports, no
StatuteProof dependency (`app/evidence_pack.py`). The Regulator Binder's
`verify.py` additionally re-seals every included `evidence-record.json` and
recomputes the binder-level hash (`app/regulator_binder.py`).

**d) The Auditor Evidence Room (optional).** A customer can create a
time-boxed (max 90 days), revocable, read-only link exposing a frozen scope of
sealed records to an external examiner — no account needed. The link token is
a 256-bit secret stored only as a SHA-256 hash and compared in constant time;
scope is entitlement-clipped and frozen at creation; every view (allowed or
denied) is written to the append-only access log (`app/evidence_room.py`).

## 6. Honest scope: tamper-evident, not tamper-proof

Stated plainly, as in the open spec §1:

- A clean record proves the bytes were not edited *in place* after sealing.
- A clean chain proves the sequence was not altered in place or reordered.
- **The limit:** an actor with full write access to the store who re-seals and
  re-links the *entire* trail can produce a trail that re-verifies clean. The
  separately persisted head anchor raises the bar (a relink diverges from the
  anchored head), and the external RFC 3161 anchor (§7) raises it further with
  a signature StatuteProof cannot forge. We do not claim "immutable" or
  "tamper-proof", and any StatuteProof material that did would be wrong.

## 7. External RFC 3161 timestamp anchor — implemented, dormant by default

`app/rfc3161_anchor.py` implements external anchoring of the chain head to a
third-party RFC 3161 Time-Stamping Authority (TSA):

- **Status: dormant by default.** It activates only when the operator sets
  `RFC3161_TSA_URL`; with no configuration it is a complete no-op — no network
  calls, no threads, no files. [CONFIRM WITH OPERATOR] whether it is enabled
  in the current production deployment.
- **What it adds when enabled:** the TSA signs a token binding the head
  `record_hash` to a time StatuteProof cannot backdate. A re-linked trail
  cannot reproduce a TSA token predating the relink — upgrading the guarantee
  from *tamper-evident* to *externally-anchored tamper-evident*, checkable by
  anyone who trusts the TSA rather than StatuteProof.
- **What is sent:** a single SHA-256 digest. No content, no personal data.
- **Independent verification:** the token is persisted both as JSON metadata
  and as a raw DER `.tsr` file readable by standard `openssl ts` tooling; the
  spec (§6.3) gives the exact `openssl ts -verify` commands. The bundled
  offline verifier checks the imprint and the TSA signature against the
  certificate embedded in the token, and honestly reports that
  chain-to-trusted-root is the *verifier's* decision (it ships no trust
  store) — never a false pass.

## 8. Related guarantees around the evidence

- **Evidence-first gating:** a risk brief is not drafted without a complete
  canonical evidence record, and canonical records failing validation are
  blocked from brief eligibility (`app/evidence_records.py`).
- **Forbidden-claims guard:** authored prose in customer-facing evidence
  artifacts (packs, binders, evidence rooms) is checked against a
  forbidden-claims list before writing; a banned claim refuses the artifact
  (`app/evidence_pack.py::assert_no_forbidden_claims`).
- **Bounded exports:** every export path enforces hard record caps so an
  export can neither be silently truncated into misleading "complete-looking"
  evidence nor exhaust the host (`app/evidence_pack.py`,
  `app/audit_export.py`, `app/evidence_room.py`).

---

*For monitoring information only. Not legal advice and not a guarantee of
compliance.*

Questions: security@statuteproof.com [CONFIRM WITH OPERATOR]
