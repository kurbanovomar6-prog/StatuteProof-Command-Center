"""Canonical evidence-record hashing — the ONE shared self-seal function.

The canonical ``evidence-record.json`` (``evidence/.../evidence-record.json`` — the
object shipped inside every Evidence Pack and held by the customer) seals its own
``content`` block with a top-level ``record_hash``. Both the writer
(:func:`app.evidence_records.create_canonical_evidence_record`) and the public
verifier (:mod:`app.public_verify`) compute that hash through THIS function, so the
two sides can never drift: if the canonicalization ever changes, it changes for the
writer and the verifier at the same time.

The input is the record's ``content`` block (the dict stored at
``record["content"]``). The output is the bare, lowercase, 64-character hex SHA-256
digest of the compact, sorted-key, UTF-8 JSON serialization of that block. Callers
that store the digest in the record prefix it with ``sha256:`` to match the record's
other hash fields; the verifier strips that prefix before comparing.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Published scheme identifier stamped into the record as ``record_hash_method``.
# The verifier branches on this exact string, so it is part of the wire contract:
# bump it only alongside a coordinated writer + verifier change.
RECORD_HASH_METHOD = "content-sha256-v1"


def canonical_record_hash(content: dict[str, Any]) -> str:
    """Return the bare lowercase-hex SHA-256 of a record's ``content`` block.

    The block is serialized as compact (``separators=(",", ":")``), sorted-key,
    non-ASCII-preserving (``ensure_ascii=False``) UTF-8 JSON. That serialization is
    byte-stable across machines and Python versions, so any auditor who holds the
    record's ``content`` block can reproduce the digest with standard tools.

    Parameters
    ----------
    content:
        The record's ``content`` block — the exact dict stored at
        ``record["content"]``.

    Returns
    -------
    str
        The 64-character lowercase hex SHA-256 digest (no ``sha256:`` prefix).
    """
    # allow_nan=False: NaN/Infinity would serialize as non-RFC-8259 tokens that no
    # standard JSON parser (jq, Go, JS) accepts, so an auditor could not reproduce
    # the digest — silently breaking the "reproducible with standard tools" promise
    # above. Fail loudly at seal time instead of sealing an unverifiable record.
    payload = json.dumps(
        content, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
