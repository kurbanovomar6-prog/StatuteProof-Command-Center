"""
RegRadar — source run history.

Lightweight JSONL run evidence for source-readiness checks. This is intentionally
append-only and filesystem-based so it can support first pilots without a DB
migration.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.chunk_diff import build_chunk_diff, build_incomplete_diff, render_diff_markdown, utc_now
from app.proof import build_source_proof
from app.text_normalization import NORMALIZATION_VERSION, normalize_for_change_hash, stable_content_hash, stable_normalized_hash


# D8: the artifact base dir is resolved from the environment with a sane
# default (repo root). Everything under data/ derives from this one anchor.
_BASE_DIR = Path(os.environ.get("STATUTEPROOF_BASE_DIR") or Path(__file__).parent.parent).resolve()
_RUN_DIR = _BASE_DIR / "data" / "source_runs"
_RUN_FILE = _RUN_DIR / "source_runs.jsonl"
_SNAPSHOT_DIR = _BASE_DIR / "data" / "source_snapshots"

_GOOD_ORDER = {"FAILED": 0, "THIN": 1, "MEDIUM": 2, "GOOD": 3}
_MIN_NORMALIZED_CHARS = 500

# The intake path records quality as GOOD/MEDIUM/THIN/FAILED while the
# monitor pipeline records good/low_content/failed — normalize both
# vocabularies before ranking so classification never depends on casing.
_QUALITY_ALIASES = {"LOW_CONTENT": "THIN", "OK": "MEDIUM"}


def _canonical_quality(value: str | None) -> str:
    label = str(value or "FAILED").strip().upper()
    return _QUALITY_ALIASES.get(label, label)

_RUNS_CACHE: list[dict] | None = None
_CACHE_VALID: bool = False
# Fingerprint of the file the cache was built from (mtime_ns, size).
# The API and the scheduler run as separate processes — a warm cache must
# notice appends/rewrites made by the other process (eval finding N1).
_CACHE_STAMP: tuple[int, int] | None = None


def source_run_path() -> Path:
    return _RUN_FILE


def source_snapshot_dir() -> Path:
    return _SNAPSHOT_DIR


# Max attempts to re-acquire the append lock on the CURRENT inode when a
# retention rewrite swaps the file out from under us mid-append.
_APPEND_RELOCK_ATTEMPTS = 5


# ── G-hashchain: tamper-evident hash chain over the evidence trail ───────────
#
# Each appended record carries prev_record_hash (the record_hash of the
# immediately preceding trail line) and record_hash (a sha256 over this
# record's identifying fields plus prev_record_hash).
#
# SCOPE — what the chain does and does NOT prove (be honest here):
#   The chain detects IN-PLACE, UN-RELINKED tampering: inserting, deleting,
#   reordering, or editing an identifying field of a record WITHOUT rebuilding
#   the downstream links breaks the chain at that point, detectable by
#   recomputation (see tools/verify_evidence_trail.py --chain). It verifies the
#   on-disk integrity of the trail since the last known head.
#
#   It is NOT proof against an actor who can ALSO relink. relink_chain() is a
#   public, un-anchored self-repair (used by legitimate retention compaction):
#   anyone with write access who deletes records and then relinks the survivors
#   produces a chain that verifies clean. Detecting that requires an EXTERNAL
#   anchor the local trail cannot forge — e.g. the head-hash file this module
#   also maintains (compared by the verifier, reported not fail-hard because
#   legitimate compaction moves the head), or ultimately an off-box/signed
#   anchor. Absent such an anchor, "the chain verifies" means only "no in-place,
#   un-relinked tampering since the last head", not "no tampering at all".
#
# The chain is ADDITIVE: record_hash is derived from — but never feeds back
# into — normalized_hash / content_hash, so it can never change the values the
# monitor compares for change detection and can never cause a spurious CHANGED.
# The identifying fields are the ones a consumer relies on to prove "this source
# had this content/status at this time"; a tamperer who edits any of them is
# caught. Fields that are cosmetic or derivable (paths, chars, notes) are left
# out so unrelated cosmetic edits do not require a chain rewrite.
_CHAIN_FIELDS = (
    "source_id",
    "timestamp_utc",
    "change_status",
    "normalized_hash",
    "content_hash",
    "prev_record_hash",
)


def _chain_payload(record: dict) -> str:
    """Canonical serialization of a record's identifying fields for hashing.

    Deterministic and order-stable: a JSON object of exactly _CHAIN_FIELDS,
    sorted keys, missing values rendered as null. Because the field set and the
    serialization are fixed, the same record always hashes to the same value on
    any machine and across Python versions.
    """
    payload = {field: record.get(field) for field in _CHAIN_FIELDS}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def compute_record_hash(record: dict, prev_record_hash: str) -> str:
    """Compute record_hash = sha256 over the record's identifying fields.

    ``prev_record_hash`` is folded in (via the record's own field) so the hash
    binds each record to its predecessor — the essence of the chain. This does
    NOT read or mutate normalized_hash/content_hash; it only reads them.
    """
    staged = dict(record)
    staged["prev_record_hash"] = prev_record_hash
    return hashlib.sha256(_chain_payload(staged).encode("utf-8")).hexdigest()


def _last_record_hash_from_lines(lines: list[str]) -> str:
    """Return the record_hash of the last non-blank JSONL line, or "".

    Tolerates legacy pre-chain records (no record_hash) and malformed lines:
    the chain simply (re)starts at the first record that carries a record_hash.
    """
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            return ""
        return str(rec.get("record_hash") or "")
    return ""


def _apply_chain_fields(record: dict, prev_record_hash: str) -> dict:
    """Set prev_record_hash + record_hash on ``record`` in place and return it."""
    record["prev_record_hash"] = prev_record_hash
    record["record_hash"] = compute_record_hash(record, prev_record_hash)
    return record


# ── G-anchor: separate head-hash file (a lightweight external anchor) ────────
#
# The in-file chain alone cannot catch a delete-then-relink (see the SCOPE note
# above): an actor who relinks produces a clean-verifying chain. This anchor
# persists the CURRENT chain head record_hash to a SEPARATE file on every
# chained append AND on the retention relink path. The verifier compares the
# live head to the anchored head and REPORTS (never fails hard) when they
# diverge without a recorded compaction — legitimate compaction moves the head
# and updates the anchor, so it never flags as tampering.
#
# This is deliberately NOT tamper-proof on its own (an attacker with write
# access to data/ can also rewrite this file). It raises the bar one notch and
# gives an honest signal; a truly tamper-proof guarantee needs an off-box /
# signed anchor — tracked as a documented follow-up.
def _chain_head_file() -> Path:
    # Derived from the live _RUN_DIR so test monkeypatching of the trail dirs
    # relocates the anchor too (kept beside the trail, under data/).
    return _RUN_DIR.parent / "evidence_chain_head.json"


def _write_chain_head(head_record_hash: str, *, compaction: bool = False) -> None:
    """Persist the current chain head record_hash to the anchor file.

    ``compaction=True`` records that the head moved because of a legitimate
    retention compaction (relink), so the verifier does not misread the expected
    head change as tampering. Best-effort: a failed write is non-fatal (the
    anchor is an ADDITIVE signal, never a gate on evidence durability).
    """
    try:
        path = _chain_head_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "head_record_hash": str(head_record_hash or ""),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "last_update_kind": "compaction" if compaction else "append",
        }
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
        # G-anchor-external (DORMANT by default): optionally submit this head to a
        # third-party RFC 3161 Time-Stamping Authority so the head cannot be
        # backdated by anyone with local write access (see docs
        # EVIDENCE-VERIFICATION-SPEC.md §5). This is the SINGLE chokepoint for every
        # head update (append + compaction), so wiring it here covers them all.
        _maybe_external_anchor(head_record_hash, path)
    except OSError:
        pass


def _maybe_external_anchor(head_record_hash: str, head_anchor_path: Path) -> None:
    """Best-effort, DORMANT-by-default external timestamp anchor of the chain head.

    Complete no-op unless the operator has set ``RFC3161_TSA_URL`` — no network, no
    thread, no files, capture byte-for-byte unchanged. When enabled, the anchor
    runs on a daemon thread so source capture never blocks on the TSA. Never raises
    into the append path (the tamper-evident chain is never at risk from this).
    """
    try:
        from app.rfc3161_anchor import anchor_enabled, spawn_head_anchor

        if not anchor_enabled():
            return
        spawn_head_anchor(head_record_hash, head_anchor_path)
    except Exception:
        pass


def read_chain_head() -> dict | None:
    """Return the anchored head payload dict, or None if no anchor exists."""
    path = _chain_head_file()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _locked_append_record(record: dict) -> dict:
    """Chain-and-append one record under a single exclusive flock.

    The tamper-evident chain requires the tail read (last record_hash) and the
    write to be atomic with respect to other appenders, so both happen while the
    SAME flock is held on the current inode. Reuses the inode-swap safety and
    fsync durability of _locked_append_line, then mutates ``record`` in place
    with the computed chain fields (so callers see record_hash/prev_record_hash
    on the returned dict).
    """
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    for _ in range(_APPEND_RELOCK_ATTEMPTS):
        fh = _RUN_FILE.open("a+", encoding="utf-8")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX)
            fd_ino = os.fstat(fh.fileno()).st_ino
            try:
                path_ino = os.stat(_RUN_FILE).st_ino
            except OSError:
                path_ino = None
            if path_ino is not None and path_ino != fd_ino:
                fcntl.flock(fh, fcntl.LOCK_UN)
                fh.close()
                continue
            # Read the current tail under the SAME lock so the prev pointer is
            # consistent with the file we are about to append to.
            fh.seek(0)
            existing_lines = fh.read().splitlines()
            prev_hash = _last_record_hash_from_lines(existing_lines)
            _apply_chain_fields(record, prev_hash)
            line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            try:
                fh.seek(0, os.SEEK_END)
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
            # G-anchor: this record is now the chain head — persist it.
            _write_chain_head(record.get("record_hash", ""))
            return record
        finally:
            if not fh.closed:
                fh.close()
    # Last-ditch: append without the inode dance rather than dropping the record.
    with _RUN_FILE.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.seek(0)
            existing_lines = fh.read().splitlines()
            prev_hash = _last_record_hash_from_lines(existing_lines)
            _apply_chain_fields(record, prev_hash)
            fh.seek(0, os.SEEK_END)
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    # G-anchor: update the head after the last-ditch append too.
    _write_chain_head(record.get("record_hash", ""))
    return record


def relink_chain(records: list[dict]) -> list[dict]:
    """Re-link a list of trail records into a valid chain, in order.

    Used by retention compaction: after heartbeat / QUALITY_DROP repeats are
    dropped, the survivors' prev_record_hash pointers reference records that no
    longer exist, so the chain must be rebuilt over the survivors. Each survivor
    is re-pointed at its predecessor's freshly recomputed record_hash and its
    own record_hash is recomputed — producing a chain that verifies clean over
    exactly the records that remain.

    Legacy pre-chain records (those without a record_hash) are left untouched so
    a compaction of an all-legacy trail is a no-op and stays byte-identical
    (idempotency): chaining only takes effect once records carry record_hash.
    Mutates the dicts in place and returns the same list for convenience.

    NOTE (G-anchor): relink is exactly the operation the in-file chain CANNOT
    detect — a relinked trail always verifies clean. Legitimate callers
    (retention compaction) MUST update the head anchor after relinking (they
    call ``_write_chain_head(new_head, compaction=True)`` once the survivors are
    persisted) so the verifier reads the moved head as an expected compaction,
    not tampering. See the SCOPE note at the top of this module.
    """
    prev_hash = ""
    for record in records:
        if not record.get("record_hash"):
            # Pre-chain record: do not manufacture a chain over legacy data.
            # A later chained survivor links from the last chained record_hash
            # (prev_hash), so legacy records simply pass through.
            continue
        _apply_chain_fields(record, prev_hash)
        prev_hash = record["record_hash"]
    return records


def _locked_append_line(line: str) -> None:
    """
    Append one line to _RUN_FILE under an exclusive flock, safe against a
    concurrent os.replace() inode swap (retention compaction).

    flock is bound to the open file description (the inode), not the path.
    A naive ``open('a') → flock`` can therefore win the lock on an inode that
    a retention rewrite already unlinked via os.replace(): the write lands in
    the dead inode and is silently lost while the path now points at a fresh
    file. After acquiring the lock we re-stat the path and compare its inode
    to the fd's inode; if they differ the file was replaced, so we drop the
    lock, reopen the current path, and retry. Only when the locked fd and the
    live path agree on the inode do we write — guaranteeing the record lands
    in the file readers will see.
    """
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    for _ in range(_APPEND_RELOCK_ATTEMPTS):
        fh = _RUN_FILE.open("a", encoding="utf-8")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX)
            fd_ino = os.fstat(fh.fileno()).st_ino
            try:
                path_ino = os.stat(_RUN_FILE).st_ino
            except OSError:
                path_ino = None
            if path_ino is not None and path_ino != fd_ino:
                # The file was replaced (retention rewrite) after we opened but
                # before we locked. Our fd points at the now-unlinked old inode;
                # writing here would be lost. Reopen the current path and retry.
                fcntl.flock(fh, fcntl.LOCK_UN)
                fh.close()
                continue
            try:
                fh.write(line)
                # Durability (A-durability): the evidence record must be on
                # stable storage before this function returns, so an "alert
                # sent" state can never outrun an "evidence recorded" state
                # across a crash/power-loss. flush() empties Python's buffer
                # into the kernel; os.fsync() forces the kernel page cache for
                # this fd out to disk. Done while the flock is still held.
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
            return
        finally:
            if not fh.closed:
                fh.close()
    # Last-ditch: append without the inode dance rather than dropping the record.
    with _RUN_FILE.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def make_source_id(source: dict) -> str:
    existing = source.get("id") or source.get("source_id")
    if existing:
        return str(existing)
    market = str(source.get("jurisdiction") or source.get("market") or "XX").upper()
    name = str(source.get("name") or source.get("url") or "source").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", name).strip("-")[:72] or "source"
    return f"{market}-{slug}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _raw_hash(text: str) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(_BASE_DIR))
    except ValueError:
        return str(path)


def _path_from_rel(path: str | None) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    resolved = candidate if candidate.is_absolute() else _BASE_DIR / candidate
    try:
        resolved.relative_to(_BASE_DIR)
    except ValueError:
        return None
    return resolved


def _snapshot_paths(timestamp_utc: str, market: str, source_id: str, run_id: str) -> Path:
    date_part = timestamp_utc[:10] if timestamp_utc else datetime.now(timezone.utc).date().isoformat()
    return _SNAPSHOT_DIR / date_part / market.upper() / source_id / run_id


def write_snapshots(
    *,
    timestamp_utc: str,
    market: str,
    source_id: str,
    run_id: str,
    raw_text: str,
    normalized_text: str,
    pdf_text: str,
    metadata: dict,
) -> dict[str, str | None]:
    base = _snapshot_paths(timestamp_utc, market, source_id, run_id)
    base.mkdir(parents=True, exist_ok=True)

    raw_path = base / "raw.txt"
    normalized_path = base / "normalized.txt"
    metadata_path = base / "metadata.json"
    pdf_path = base / "pdf_text.txt" if pdf_text else None

    raw_path.write_text(raw_text or "", encoding="utf-8")
    normalized_path.write_text(normalized_text or "", encoding="utf-8")
    if pdf_path is not None:
        pdf_path.write_text(pdf_text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return {
        "snapshot_raw_path": _rel(raw_path),
        "snapshot_normalized_path": _rel(normalized_path),
        "snapshot_pdf_text_path": _rel(pdf_path),
        "snapshot_metadata_path": _rel(metadata_path),
    }


def _file_stamp() -> tuple[int, int] | None:
    try:
        st = _RUN_FILE.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _read_runs() -> list[dict]:
    global _RUNS_CACHE, _CACHE_VALID, _CACHE_STAMP
    stamp = _file_stamp()
    if _CACHE_VALID and _RUNS_CACHE is not None and stamp == _CACHE_STAMP:
        return _RUNS_CACHE
    if not _RUN_FILE.exists():
        _RUNS_CACHE = []
        _CACHE_VALID = True
        _CACHE_STAMP = None
        return _RUNS_CACHE
    rows: list[dict] = []
    try:
        for line in _RUN_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except FileNotFoundError:
        rows = []
    _RUNS_CACHE = rows
    _CACHE_VALID = True
    _CACHE_STAMP = stamp
    return _RUNS_CACHE


def latest_runs(
    market: str | None = None,
    source_filter: str | None = None,
) -> dict[str, dict]:
    market_norm = market.upper() if market else None
    source_norm = source_filter.lower() if source_filter else None
    latest: dict[str, dict] = {}

    for rec in _read_runs():
        if market_norm and str(rec.get("market", "")).upper() != market_norm:
            continue
        if source_norm:
            sid = str(rec.get("source_id", "")).lower()
            name = str(rec.get("source_name", "")).lower()
            if source_norm not in sid and source_norm not in name:
                continue
        sid = str(rec.get("source_id") or rec.get("official_url") or "")
        if not sid:
            continue
        latest[sid] = rec
    return latest


def previous_run(source_id: str) -> dict | None:
    for rec in reversed(_read_runs()):
        if rec.get("source_id") == source_id:
            return rec
    return None


def changed_runs(
    market: str | None = None,
    source_filter: str | None = None,
    limit: int = 20,
) -> list[dict]:
    market_norm = market.upper() if market else None
    source_norm = source_filter.lower() if source_filter else None
    rows: list[dict] = []
    for rec in _read_runs():
        if rec.get("change_status") != "CHANGED":
            continue
        if market_norm and str(rec.get("market", "")).upper() != market_norm:
            continue
        if source_norm:
            sid = str(rec.get("source_id", "")).lower()
            name = str(rec.get("source_name", "")).lower()
            if source_norm not in sid and source_norm not in name:
                continue
        rows.append(rec)
    rows.sort(key=lambda r: r.get("timestamp_utc", ""), reverse=True)
    return rows[:limit]


def classify_change(current: dict, previous: dict | None) -> str:
    quality = _canonical_quality(current.get("extraction_quality"))
    chars = int(current.get("extracted_chars") or 0)
    normalized_chars = int(current.get("normalized_chars") or 0)
    if current.get("access_status") == "failed" or quality == "FAILED":
        return "FAILED"
    if previous is None:
        return "FIRST_SEEN"

    prev_quality = _canonical_quality(previous.get("extraction_quality"))
    prev_chars = int(previous.get("extracted_chars") or 0)
    prev_norm_chars = int(previous.get("normalized_chars") or 0)
    if prev_quality == "FAILED" and quality != "FAILED":
        return "FIRST_SEEN"
    if _GOOD_ORDER.get(prev_quality, 0) >= _GOOD_ORDER["MEDIUM"] and _GOOD_ORDER.get(quality, 0) <= _GOOD_ORDER["THIN"]:
        return "QUALITY_DROP"
    if prev_chars > 0 and chars < prev_chars * 0.4:
        return "QUALITY_DROP"
    if normalized_chars and normalized_chars < _MIN_NORMALIZED_CHARS:
        return "QUALITY_DROP"
    if prev_norm_chars > 0 and normalized_chars and normalized_chars < prev_norm_chars * 0.7:
        return "QUALITY_DROP"

    if previous.get("normalized_hash"):
        prev_hash = previous.get("normalized_hash")
        cur_hash = current.get("normalized_hash") or current.get("content_hash")
    else:
        prev_hash = previous.get("content_hash")
        cur_hash = current.get("content_hash")
    if prev_hash and cur_hash and prev_hash != cur_hash:
        return "CHANGED"
    return "UNCHANGED"


def append_run(record: dict) -> dict:
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    prev = previous_run(record["source_id"])
    record["change_status"] = classify_change(record, prev)
    if (
        record["change_status"] == "UNCHANGED"
        and prev
        and record.get("raw_hash")
        and prev.get("raw_hash")
        and record.get("raw_hash") != prev.get("raw_hash")
        and record.get("normalized_hash")
        and record.get("normalized_hash") == prev.get("normalized_hash")
    ):
        _append_limitation(record, "Raw content changed; normalized regulatory content unchanged.")
    diff_artifact = None
    snapshot_base = _snapshot_base_from_record(record)
    if snapshot_base is not None:
        if record["change_status"] == "CHANGED":
            diff_artifact = _write_diff_artifacts(record, prev, snapshot_base)
        _write_proof_artifact(record, diff_artifact, snapshot_base)
    # G-hashchain: chain-and-append under one flock (reads the current tail's
    # record_hash and stamps prev_record_hash + record_hash on this record).
    _locked_append_record(record)
    global _CACHE_VALID
    _CACHE_VALID = False
    if record.get("change_status") == "CHANGED":
        queue_changed_alert(record)  # type: ignore[reportUndefinedVariable]
    return record


def mark_alert_sent(source_id: str, run_id: str, *, alert_sent: bool = True) -> bool:
    """Patch a persisted trail record's ``alert_sent`` flag in place.

    A-HIGH: the dedup gate (``alert_dedup.should_send_alert``) keys on the trail
    record's ``alert_sent``. So the record must reflect ACTUAL delivery: a run is
    appended with ``alert_sent=False`` (evidence recorded, but delivery not yet
    confirmed), and this flips it to True ONLY after a confirmed Telegram send.
    If the send fails, the record stays ``alert_sent=False`` and the next sweep
    re-attempts the alert for the same hash instead of suppressing it forever.

    ``alert_sent`` is NOT a chain field (see ``_CHAIN_FIELDS``), so flipping it
    does not change any ``record_hash`` and leaves the tamper-evident chain
    intact — no re-link is needed. The rewrite is atomic (temp file + rename)
    under the same exclusive flock the appenders use, so it is safe against a
    concurrent append/compaction.

    Returns True if a matching record was found and updated, else False.
    """
    if not _RUN_FILE.exists():
        return False
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    with _RUN_FILE.open("r+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            rows: list[dict] = []
            updated = False
            for line in fh.read().splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    str(rec.get("source_id") or "") == str(source_id)
                    and str(rec.get("run_id") or "") == str(run_id)
                ):
                    if bool(rec.get("alert_sent")) != bool(alert_sent):
                        rec["alert_sent"] = bool(alert_sent)
                        updated = True
                rows.append(rec)
            if not updated:
                return False
            tmp = _RUN_FILE.with_suffix(".jsonl.mark.tmp")
            with tmp.open("w", encoding="utf-8") as out:
                for row in rows:
                    out.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                out.flush()
                os.fsync(out.fileno())
            tmp.replace(_RUN_FILE)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    global _CACHE_VALID
    _CACHE_VALID = False
    return True


def record_heartbeat(
    source: dict,
    *,
    normalized_hash: str,
    raw_hash: str | None = None,
    extracted_chars: int = 0,
    raw_chars: int = 0,
    normalized_chars: int = 0,
    extraction_quality: str = "",
) -> dict:
    """
    D6: write a compact heartbeat record for an UNCHANGED monitor run so the
    evidence trail can prove "we checked on date X" between change events.

    The record goes through append_run, so classification is re-verified
    against the previous trail record — a heartbeat is never trusted blindly.
    No snapshots or proof artifacts are written (compact by design).
    """
    market = str(source.get("jurisdiction", source.get("market", "AE"))).upper()
    record = {
        "record_type": "heartbeat",
        "run_id": uuid.uuid4().hex[:8],
        "timestamp_utc": now_utc(),
        "source_id": make_source_id(source),
        "source_name": source.get("name", ""),
        "official_url": source.get("url", ""),
        "url": source.get("url", ""),
        "market": market,
        "jurisdiction": source.get("jurisdiction", market),
        "category": source.get("category", ""),
        "change_status": "UNCHANGED",
        "normalized_hash": normalized_hash,
        "content_hash": normalized_hash,
        "raw_hash": raw_hash,
        "extraction_quality": extraction_quality,
        "extracted_chars": extracted_chars,
        "raw_chars": raw_chars,
        "normalized_chars": normalized_chars,
    }
    return append_run(record)


def record_quality_drop(
    source: dict,
    *,
    reason: str,
    alert_suppressed_reason: str = "content_shrink",
    observed_raw_chars: int = 0,
    observed_normalized_chars: int = 0,
    prev_raw_chars: int | None = None,
    prev_normalized_chars: int | None = None,
    extraction_method: str = "",
) -> dict:
    """A-MEDIUM(1): write a durable QUALITY_DROP audit record for a suppressed
    run (e.g. a content-shrink scraper break) so the gap is auditable instead of
    living only in a log line.

    Critical baseline-safety invariants:

      * ``normalized_hash`` / ``content_hash`` are BOTH None, so
        ``previous_run`` can never resolve this record as a baseline — the true
        baseline (SQLite / the prior good trail record) survives the scraper
        break, exactly as before this record existed.
      * ``change_status`` is forced to ``"QUALITY_DROP"`` and the record is
        chain-appended DIRECTLY (bypassing ``append_run``/``classify_change``),
        so nothing reclassifies it to CHANGED/UNCHANGED and it emits no alert or
        alert queue entry.
      * ``alert_sent`` is False (nothing was delivered) and
        ``alert_suppressed_reason`` records WHY, so the dedup gate is untouched.
      * The baseline-relevant size fields (``extracted_chars`` /
        ``normalized_chars``) carry the PREVIOUS good sizes forward so the next
        sweep's shrink guard still compares against the true baseline size, not
        the shrunk one. The shrunk sizes are kept under ``observed_*`` for audit.

    Chained like any other trail record, so the tamper-evident chain stays
    continuous. No snapshots/proof/diff artifacts (compact, by design).
    """
    market = str(source.get("jurisdiction", source.get("market", "AE"))).upper()
    record = {
        "record_type": "quality_drop",
        "run_id": uuid.uuid4().hex[:8],
        "timestamp_utc": now_utc(),
        "source_id": make_source_id(source),
        "source_name": source.get("name", ""),
        "official_url": source.get("url", ""),
        "url": source.get("url", ""),
        "market": market,
        "jurisdiction": source.get("jurisdiction", market),
        "category": source.get("category", ""),
        "change_status": "QUALITY_DROP",
        # Baseline-safety: no usable hash → never resolved as a baseline.
        "normalized_hash": None,
        "content_hash": None,
        "raw_hash": None,
        "extraction_quality": "FAILED",
        "extraction_method": extraction_method,
        # Carry the previous good sizes forward so the next shrink guard still
        # compares against the true baseline size (0/None when unknown).
        "extracted_chars": int(prev_raw_chars or 0),
        "normalized_chars": int(prev_normalized_chars or 0),
        # The shrunk sizes actually observed this run — audit only.
        "observed_raw_chars": int(observed_raw_chars or 0),
        "observed_normalized_chars": int(observed_normalized_chars or 0),
        "alert_sent": False,
        "alert_suppressed_reason": alert_suppressed_reason,
        "limitations_notes": reason,
    }
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    _locked_append_record(record)
    global _CACHE_VALID
    _CACHE_VALID = False
    return record


def _append_limitation(record: dict, note: str) -> None:
    existing = str(record.get("limitations_notes") or "").strip()
    if note in existing:
        return
    record["limitations_notes"] = f"{existing}; {note}" if existing else note


def _snapshot_base_from_record(record: dict) -> Path | None:
    for key in ("snapshot_normalized_path", "snapshot_raw_path", "snapshot_metadata_path"):
        path = _path_from_rel(record.get(key))
        if path is not None:
            return path.parent
    return None


def _read_snapshot_text(path: str | None) -> str | None:
    snapshot_path = _path_from_rel(path)
    if snapshot_path is None or not snapshot_path.exists():
        return None
    return snapshot_path.read_text(encoding="utf-8", errors="replace")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_diff_artifacts(record: dict, prev: dict | None, snapshot_base: Path) -> dict:
    previous_path = prev.get("snapshot_normalized_path") if prev else None
    current_path = record.get("snapshot_normalized_path")
    previous_text = _read_snapshot_text(previous_path)
    current_text = _read_snapshot_text(current_path)

    if previous_text is None or current_text is None:
        artifact = build_incomplete_diff(
            previous_run_id=prev.get("run_id") if prev else None,
            current_run_id=record.get("run_id"),
            previous_snapshot_normalized_path=previous_path,
            current_snapshot_normalized_path=current_path,
            limitation="Previous normalized snapshot unavailable; diff cannot be generated.",
        )
    else:
        artifact = build_chunk_diff(previous_text, current_text)
        artifact.update({
            "previous_run_id": prev.get("run_id") if prev else None,
            "current_run_id": record.get("run_id"),
            "previous_snapshot_normalized_path": previous_path,
            "current_snapshot_normalized_path": current_path,
            "generated_at_utc": utc_now(),
        })

    diff_json_path = snapshot_base / "diff.json"
    diff_md_path = snapshot_base / "diff.md"
    _write_json(diff_json_path, artifact)
    diff_md_path.write_text(render_diff_markdown(artifact), encoding="utf-8")
    record["diff_json_path"] = _rel(diff_json_path)
    record["diff_md_path"] = _rel(diff_md_path)
    record["meaningful_change_detected"] = artifact.get("meaningful_change_detected")
    record["diff_quality"] = artifact.get("diff_quality")
    return artifact


def _write_proof_artifact(record: dict, diff_artifact: dict | None, snapshot_base: Path) -> None:
    proof_path = snapshot_base / "proof.json"
    record["proof_block_path"] = _rel(proof_path)
    proof = build_source_proof(record, diff_artifact)
    _write_json(proof_path, proof)


def record_from_source_result(
    *,
    run_id: str,
    source: dict,
    result: dict,
    limitations_notes: list[str] | None = None,
) -> dict:
    doc_info = result.get("document_info") or {}
    pdf_text = doc_info.get("combined_text") or ""
    page_text = result.get("extracted_text") or ""
    combined_raw_text = _combine_text(page_text, pdf_text)
    normalized_text = normalize_for_change_hash(combined_raw_text)
    extracted_chars = int(result.get("extracted_chars") or 0)
    pdf_chars = int(doc_info.get("combined_chars") or 0)
    quality = _quality_from_chars(extracted_chars + pdf_chars)
    timestamp_utc = now_utc()
    market = str(source.get("jurisdiction") or "").upper()
    source_id = make_source_id(source)

    fetch_method = result.get("fetch_method") or result.get("recommended_method") or "failed"
    if pdf_chars > 0 and fetch_method not in ("failed", "pdf"):
        fetch_method = "mixed"

    access_status = "accessible" if result.get("status") == "ok" else "failed"
    if result.get("verdict") == "needs_adapter":
        access_status = "dynamic/adapter_needed"
    elif source.get("status") in ("disabled_external_access", "disabled_navigation_only"):
        access_status = "restricted"

    notes = list(limitations_notes or [result.get("reason") or ""])
    if int(doc_info.get("pdf_links_count") or 0) > 0 and pdf_chars == 0:
        notes.append("PDF links found but no extractable text; manual validation/OCR may be required.")
    if normalized_text and len(normalized_text) < _MIN_NORMALIZED_CHARS and quality != "FAILED":
        notes.append("Normalized regulatory text is thin; manual validation may be required.")

    pdf_text_hash = stable_normalized_hash(pdf_text) or None
    metadata = {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "official_url": source.get("url", ""),
        "final_url": result.get("final_url") or result.get("url") or source.get("url", ""),
        "raw_chars": len(combined_raw_text),
        "normalized_chars": len(normalized_text),
        "pdf_extracted_chars": pdf_chars,
    }
    snapshots = write_snapshots(
        timestamp_utc=timestamp_utc,
        market=market,
        source_id=source_id,
        run_id=run_id,
        raw_text=combined_raw_text,
        normalized_text=normalized_text,
        pdf_text=pdf_text,
        metadata=metadata,
    )

    return {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "market": market,
        "jurisdiction": market,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "category": source.get("category", ""),
        "official_url": source.get("url", ""),
        "final_url": result.get("final_url") or result.get("url") or source.get("url", ""),
        "access_status": access_status,
        "fetch_method": fetch_method,
        "extraction_quality": quality,
        "extracted_chars": extracted_chars,
        "raw_chars": len(combined_raw_text),
        "normalized_chars": len(normalized_text),
        "raw_hash": _raw_hash(combined_raw_text),
        "normalized_hash": stable_normalized_hash(combined_raw_text) or None,
        "pdf_text_hash": pdf_text_hash,
        "pdf_links_count": int(doc_info.get("pdf_links_count") or 0),
        "pdf_extracted_chars": pdf_chars,
        "content_hash": stable_content_hash(page_text + "\n\n" + pdf_text),
        **snapshots,
        "title": result.get("title"),
        "publication_date": result.get("publication_date"),
        "limitations_notes": "; ".join(n for n in notes if n),
        "error": result.get("error") or (result.get("reason") if result.get("status") != "ok" else None),
        "pipeline_version": "4.2",
        "normalization_version": str(NORMALIZATION_VERSION),
    }


def restricted_record(
    *,
    run_id: str,
    source: dict,
    limitations_notes: list[str],
) -> dict:
    timestamp_utc = now_utc()
    market = str(source.get("jurisdiction") or "").upper()
    source_id = make_source_id(source)
    metadata = {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "official_url": source.get("url", ""),
        "restricted": True,
    }
    snapshots = write_snapshots(
        timestamp_utc=timestamp_utc,
        market=market,
        source_id=source_id,
        run_id=run_id,
        raw_text="",
        normalized_text="",
        pdf_text="",
        metadata=metadata,
    )
    return {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "market": market,
        "jurisdiction": market,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "category": source.get("category", ""),
        "official_url": source.get("url", ""),
        "final_url": source.get("url", ""),
        "access_status": "restricted",
        "fetch_method": "failed",
        "extraction_quality": "FAILED",
        "extracted_chars": 0,
        "raw_chars": 0,
        "normalized_chars": 0,
        "raw_hash": None,
        "normalized_hash": None,
        "pdf_text_hash": None,
        "pdf_links_count": 0,
        "pdf_extracted_chars": 0,
        "content_hash": None,
        **snapshots,
        "title": None,
        "publication_date": None,
        "limitations_notes": "; ".join(limitations_notes),
        "error": "Source is marked restricted/blocked in sources.json.",
        "pipeline_version": "4.2",
        "normalization_version": str(NORMALIZATION_VERSION),
    }


def _combine_text(page_text: str, pdf_text: str) -> str:
    if page_text and pdf_text:
        return f"{page_text.strip()}\n\n--- PDF TEXT ---\n\n{pdf_text.strip()}"
    return (page_text or pdf_text or "").strip()


def _quality_from_chars(chars: int) -> str:
    if chars >= 2_000:
        return "GOOD"
    if chars >= 800:
        return "MEDIUM"
    if chars > 0:
        return "THIN"
    return "FAILED"


def queue_changed_alert(record: dict) -> Path:
    """Write a CHANGED run record to the alert queue for human review.

    Returns the path to the queued alert file.
    """
    queue_dir = _BASE_DIR / "data" / "alert_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)

    source_id = str(record.get("source_id") or "unknown")
    run_id = str(record.get("run_id") or "unknown")
    import uuid as _uuid
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    filename = f"{ts}-{source_id}-{run_id[:8]}-{_uuid.uuid4().hex[:4]}.json"

    alert = {
        "queued_at": now_utc(),
        "status": "PENDING_REVIEW",
        "source_id": source_id,
        "run_id": run_id,
        "change_status": record.get("change_status"),
        "run_at": record.get("run_at") or record.get("timestamp_utc"),
        "normalized_hash": record.get("normalized_hash"),
        "diff_json_path": record.get("diff_json_path"),
        "proof_block_path": record.get("proof_block_path"),
        "human_reviewed": False,
        "reviewer": None,
        "reviewed_at": None,
        "delivery_approved": False,
        "notes": "",
    }

    out = queue_dir / filename
    out.write_text(json.dumps(alert, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return out


def list_alert_queue(status: str | None = None) -> list[dict]:
    """Return all alerts in the queue, optionally filtered by status."""
    queue_dir = _BASE_DIR / "data" / "alert_queue"
    if not queue_dir.exists():
        return []
    alerts = []
    for f in sorted(queue_dir.glob("*.json")):
        try:
            alert = json.loads(f.read_text(encoding="utf-8"))
            alert["_filename"] = f.name
            if status is None or alert.get("status") == status:
                alerts.append(alert)
        except (json.JSONDecodeError, OSError):
            continue
    return alerts


def build_weekly_status_summary(days: int = 7) -> dict:
    """Build a summary of all source runs in the last N days.

    Returns a dict with:
    - total_sources: int
    - changed_count: int
    - no_change_count: int
    - failed_count: int
    - first_seen_count: int
    - sources_with_changes: list[str]
    - sources_with_failures: list[str]
    - zero_change_sources: list[str]
    - period_days: int
    - generated_at: str
    """
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = _read_runs()

    in_period = [r for r in rows if str(r.get("run_at") or r.get("timestamp_utc") or "") >= cutoff]

    seen_sources: set[str] = set()
    changed: list[str] = []
    failed: list[str] = []
    first_seen: list[str] = []
    no_change: list[str] = []

    for r in in_period:
        sid = str(r.get("source_id") or "")
        seen_sources.add(sid)
        status = r.get("change_status")
        if status == "CHANGED" and sid not in changed:
            changed.append(sid)
        elif status == "FAILED" and sid not in failed:
            failed.append(sid)
        elif status == "FIRST_SEEN" and sid not in first_seen:
            first_seen.append(sid)
        elif status == "NO_CHANGE" and sid not in no_change:
            no_change.append(sid)

    zero_change = [s for s in seen_sources if s not in changed and s not in failed]

    return {
        "period_days": days,
        "generated_at": now_utc(),
        "total_sources_active": len(seen_sources),
        "changed_count": len(changed),
        "no_change_count": len(no_change),
        "first_seen_count": len(first_seen),
        "failed_count": len(failed),
        "sources_with_changes": sorted(changed),
        "sources_with_failures": sorted(failed),
        "zero_change_sources": sorted(zero_change),
    }


def backfill_run_artifacts(*, dry_run: bool = False) -> list[dict]:
    """
    Retroactively generate proof.json and diff.json for CHANGED run records
    that are missing these artifacts (e.g. runs made before the proof-writing
    code was in place).

    Rewrites source_runs.jsonl in-place with updated path fields.
    Safe to run multiple times — skips records that already have both artifacts,
    and does not overwrite files that already exist on disk.

    Returns a list of result dicts: {source_id, run_id, action, detail}.
    action is one of: "skipped", "backfilled", "no_snapshot", "dry_run".
    """
    rows = _read_runs()
    results: list[dict] = []
    changed = False

    for i, record in enumerate(rows):
        source_id = str(record.get("source_id") or "")
        run_id = str(record.get("run_id") or "")

        if record.get("change_status") != "CHANGED":
            continue

        has_proof = bool(record.get("proof_block_path"))
        has_diff = bool(record.get("diff_json_path"))
        if has_proof and has_diff:
            results.append({"source_id": source_id, "run_id": run_id, "action": "skipped", "detail": "already has both artifacts"})
            continue

        snapshot_base = _snapshot_base_from_record(record)
        if snapshot_base is None:
            results.append({"source_id": source_id, "run_id": run_id, "action": "no_snapshot", "detail": "cannot resolve snapshot base path"})
            continue

        if dry_run:
            results.append({"source_id": source_id, "run_id": run_id, "action": "dry_run", "detail": f"would backfill: proof={not has_proof} diff={not has_diff}"})
            continue

        # Find the previous run for this source (all records before index i)
        prior = [r for r in rows[:i] if r.get("source_id") == source_id]
        prev = prior[-1] if prior else None

        # Diff artifact — write only if file missing from disk
        diff_artifact = None
        if not has_diff:
            diff_json_path = snapshot_base / "diff.json"
            diff_md_path = snapshot_base / "diff.md"
            if diff_json_path.exists():
                # File exists but path not recorded — just wire up the record
                _loaded: dict = json.loads(diff_json_path.read_text(encoding="utf-8"))
                diff_artifact = _loaded
                record["diff_json_path"] = _rel(diff_json_path)
                record["diff_md_path"] = _rel(diff_md_path) if diff_md_path.exists() else None
                record["meaningful_change_detected"] = _loaded.get("meaningful_change_detected")
                record["diff_quality"] = _loaded.get("diff_quality")
            else:
                diff_artifact = _write_diff_artifacts(record, prev, snapshot_base)
            changed = True

        # Proof artifact — write only if file missing from disk
        if not has_proof:
            proof_json_path = snapshot_base / "proof.json"
            if proof_json_path.exists():
                record["proof_block_path"] = _rel(proof_json_path)
            else:
                _write_proof_artifact(record, diff_artifact, snapshot_base)
            changed = True

        results.append({
            "source_id": source_id,
            "run_id": run_id,
            "action": "backfilled",
            "detail": f"proof={not has_proof} diff={not has_diff}",
        })

    if changed and not dry_run:
        # Rewrite JSONL with updated path fields (atomic via rename)
        tmp = _RUN_FILE.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        tmp.replace(_RUN_FILE)
        global _CACHE_VALID
        _CACHE_VALID = False

    return results


def deduplicate_alerts(
    alerts: list[dict],
    similarity_threshold: float = 0.85,
) -> list[dict]:
    """
    Remove duplicate alerts where two sources detected the same regulatory event.

    Uses normalised text overlap (difflib.SequenceMatcher ratio on the first 500
    chars of change_text) to identify near-identical change excerpts.

    When duplicates are found:
    - Keep the alert from the higher-tier source (tier 1 > 2 > 3 > 99 for unknown).
    - Add a ``merged_sources`` field listing all source_ids that detected the event.
    """
    import difflib

    _TIER_ORDER = {"1": 1, "2": 2, "3": 3}

    def _tier(alert: dict) -> int:
        return _TIER_ORDER.get(str(alert.get("tier") or ""), 99)

    def _excerpt(alert: dict) -> str:
        text = (
            alert.get("change_text")
            or alert.get("executive_summary")
            or alert.get("ai_summary")
            or ""
        )
        return str(text)[:500].lower()

    if not alerts:
        return alerts

    kept: list[dict] = []
    used: list[bool] = [False] * len(alerts)

    for i, a in enumerate(alerts):
        if used[i]:
            continue
        group = [i]
        exc_a = _excerpt(a)
        for j in range(i + 1, len(alerts)):
            if used[j]:
                continue
            exc_b = _excerpt(alerts[j])
            ratio = difflib.SequenceMatcher(None, exc_a, exc_b).ratio()
            if ratio >= similarity_threshold:
                group.append(j)
                used[j] = True

        if len(group) == 1:
            a.setdefault("merged_sources", [a.get("source_id", "")])
            kept.append(a)
        else:
            best = min(group, key=lambda idx: _tier(alerts[idx]))
            winner = dict(alerts[best])
            winner["merged_sources"] = [
                alerts[idx].get("source_id", "") for idx in group
            ]
            kept.append(winner)

        used[i] = True

    return kept


# ── Rebaseline primitive (D) ────────────────────────────────────────────────
#
# Repairing a poisoned baseline (e.g. the VARA mojibake incident, 2026-07-10)
# previously required stopping the scheduler and re-running the full suppressed
# 116-source cycle. rebaseline_source() rebaselines ONE source in place: it
# fetches + normalizes exactly like the monitor pipeline, applies the SAME
# guards (empty / undecodable / quality gate), and — only when the content is
# good — appends a fresh FIRST_SEEN baseline record that supersedes the current
# baseline. It never alerts and never requires stopping the scheduler.

_REBASELINE_STATUS = "FIRST_SEEN"


def _find_source_by_id(source_id: str) -> dict | None:
    """Return the source dict whose make_source_id() matches source_id, or None."""
    from app.sources import load_sources

    for src in load_sources():
        if make_source_id(src) == source_id:
            return src
    return None


def _rebaseline_fetch(url: str, source: dict) -> str:
    """
    Fetch source content using the SAME adapter-aware path the monitor uses.

    Mirrors run_pipeline Step 0: prefer the source adapter when it returns
    quality content, otherwise fall back to the generic fetch_page +
    extract_best_text seams (which the guard tests patch). Fetching through the
    exact path the monitor prefers guarantees the baselined text — and therefore
    the baselined hash — matches what the next sweep will compute for an
    adapter-backed source, closing the second route to a spurious CHANGED.

    Returns the extracted text (possibly empty); guards in rebaseline_source
    decide whether it is fit to baseline. May raise on network/scrape failure —
    the caller converts that into a fetch_failed refusal.
    """
    from app.adapters.base import is_quality_content
    from app.adapters.registry import get_adapter_for_url
    from app.pipeline import fetch_page, extract_best_text  # patched by tests

    adapter = get_adapter_for_url(url, source)
    if adapter is not None:
        try:
            adapter_text = adapter.fetch_content(url, source)
        except Exception:  # adapter failure → fall through to generic scraper
            adapter_text = None
        if is_quality_content(adapter_text):
            return adapter_text or ""

    html = fetch_page(url)
    extraction = extract_best_text(html, url)
    return (extraction.get("text") or "") if extraction else ""


def _append_baseline_record(record: dict) -> dict:
    """
    Append a record to the trail as an authoritative new baseline.

    Unlike append_run(), the change_status is forced (never recomputed by
    classify_change) so a rebaseline is treated as the new canonical baseline
    even when the prior record was poisoned. Proof artifacts are written; no
    diff and no alert are produced (a baseline supersedes rather than diffs).
    """
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    record["change_status"] = _REBASELINE_STATUS
    record["rebaseline"] = True
    snapshot_base = _snapshot_base_from_record(record)
    if snapshot_base is not None:
        _write_proof_artifact(record, None, snapshot_base)
    # G-hashchain: a rebaseline record is chained like any other trail record.
    _locked_append_record(record)
    global _CACHE_VALID
    _CACHE_VALID = False
    return record


def rebaseline_source(source_id: str) -> dict:
    """
    Rebaseline a single source in place, reusing the monitor fetch/extract path.

    Returns a result dict describing the outcome:
        {"status": "rebaselined", "source_id", "run_id", "normalized_hash",
         "extracted_chars", "extraction_quality", "change_status"}   on success
        {"status": "not_found",  "source_id", "message"}             unknown id
        {"status": "refused",    "source_id", "reason", "message"}   bad content

    On refusal or an unknown id, NOTHING is written to the trail — a poisoned or
    undecodable body can never become a baseline. No Telegram/email alert is
    ever sent, and the scheduler does not need to be stopped.
    """
    import uuid as _uuid

    from app.text_quality import is_mostly_unreadable

    source = _find_source_by_id(source_id)
    if source is None:
        return {
            "status": "not_found",
            "source_id": source_id,
            "message": f"No source in sources.json matches source_id={source_id!r}.",
        }

    url = source.get("url", "")

    # ── Fetch + extract (same adapter-aware path the monitor pipeline uses) ─
    try:
        content = _rebaseline_fetch(url, source).strip()
    except Exception as exc:  # network / scrape failure → refuse, write nothing
        return {
            "status": "refused",
            "source_id": source_id,
            "reason": "fetch_failed",
            "message": f"Fetch/extract failed for {url}: {type(exc).__name__}: {exc}",
        }

    # ── Guard 1: empty content ────────────────────────────────────────────
    if not content:
        return {
            "status": "refused",
            "source_id": source_id,
            "reason": "empty_content",
            "message": f"No extractable text from {url}; refusing to baseline.",
        }

    # ── Guard 2: undecodable / mojibake / error-page bytes ────────────────
    # Same write-layer chokepoint the pipeline applies (VARA mojibake incident):
    # a mis-decoded or binary body is saturated with replacement/control chars
    # and must never be hashed, snapshotted, or baselined.
    if is_mostly_unreadable(content):
        return {
            "status": "refused",
            "source_id": source_id,
            "reason": "undecodable_content",
            "message": (
                f"Content from {url} is undecodable/error-page text "
                "(saturated with replacement/control characters); refusing to baseline."
            ),
        }

    # ── Guard 3: quality gate (same threshold as the pipeline) ────────────
    from app.adapters.base import is_quality_content

    if not is_quality_content(content):
        return {
            "status": "refused",
            "source_id": source_id,
            "reason": "low_quality",
            "message": (
                f"Content from {url} failed the quality gate "
                f"({len(content)} chars); refusing to baseline."
            ),
        }

    # ── Build the record via the shared machinery, then baseline it ───────
    run_id = _uuid.uuid4().hex[:8]
    result = {
        "url": url,
        "final_url": url,
        "status": "ok",
        "extracted_text": content,
        "extracted_chars": len(content),
        "fetch_method": "rebaseline",
        "reason": "",
    }
    record = record_from_source_result(
        run_id=run_id,
        source=source,
        result=result,
        limitations_notes=["Baseline reset via rebaseline primitive."],
    )

    # ── Align the baseline hash with what the LIVE pipeline will compute ───
    # run_pipeline resolves the baseline from this record's normalized_hash and
    # compares it against stable_content_hash(normalize_for_change_hash(content))
    # (pipeline.py Step 3/5). record_from_source_result stores the *normalized*
    # hash flavor — sha256(normalize_for_change_hash(text)) — which collapses
    # whitespace differently, so a byte-identical next sweep would read
    # baseline != new and fire a spurious CHANGED alert. Overwrite both hash
    # fields with the pipeline's canonical content-flavor hash so the trail
    # baseline and the SQLite derived index carry the exact value the monitor
    # compares against. `content` here == combined_raw_text (no PDF text on the
    # rebaseline path) and normalize_for_change_hash strips internally, so this
    # is identical to run_pipeline's new_hash for the same fetched content.
    canonical_hash = stable_content_hash(normalize_for_change_hash(content))
    record["normalized_hash"] = canonical_hash
    record["content_hash"] = canonical_hash

    # Contract guard: the stored baseline hash MUST equal the hash the live
    # pipeline computes for byte-identical content, or the next sweep spuriously
    # reclassifies CHANGED. run_pipeline's new_hash is
    # stable_content_hash(normalize_for_change_hash(content)); we recompute it
    # here through the pipeline's own imported hashing functions so this can't
    # silently drift if the pipeline changes its hashing.
    from app.pipeline import (
        normalize_for_change_hash as _pl_normalize,
        stable_content_hash as _pl_content_hash,
    )

    pipeline_new_hash = _pl_content_hash(_pl_normalize(content))
    assert record["normalized_hash"] == pipeline_new_hash, (
        "rebaseline baseline hash must equal run_pipeline's new_hash for the "
        f"same content; got {record['normalized_hash']!r} != {pipeline_new_hash!r} "
        "— hash flavors have drifted apart"
    )

    final = _append_baseline_record(record)

    # ── Align the SQLite derived index (consistency.py, owner decision 2) ──
    # check_baseline_consistency compares the trail normalized_hash against the
    # SQLite documents content_hash for the same URL. Insert an aligned row so a
    # freshly rebaselined source reports no divergence. Non-fatal: the derived
    # index is repopulated by the next monitor run if this write fails.
    try:
        from app.db import save_document

        save_document(url=url, content=content, content_hash=canonical_hash)
    except Exception as _db_err:  # derived index is best-effort; trail is truth
        import logging as _logging

        _logging.getLogger(__name__).warning(
            "rebaseline: SQLite derived-index alignment failed (non-fatal): %s",
            _db_err,
        )

    return {
        "status": "rebaselined",
        "source_id": source_id,
        "run_id": final.get("run_id"),
        "normalized_hash": final.get("normalized_hash"),
        "extracted_chars": final.get("extracted_chars"),
        "extraction_quality": final.get("extraction_quality"),
        "change_status": final.get("change_status"),
    }


def render_history_terminal(
    *,
    market: str = "AE",
    source_filter: str | None = None,
    limit: int = 20,
) -> None:
    latest = list(latest_runs(market, source_filter).values())
    latest.sort(key=lambda r: r.get("timestamp_utc", ""), reverse=True)
    rows = latest[:limit]

    print(f"\nStatuteProof — Source History  {market.upper()}")
    print("─" * 96)
    if not rows:
        print("No source run records found.")
        return
    for rec in rows:
        name = rec.get("source_name", "source")[:42]
        ts = rec.get("timestamp_utc", "unknown")
        quality = rec.get("extraction_quality", "UNKNOWN")
        chars = int(rec.get("extracted_chars") or 0)
        norm_chars = int(rec.get("normalized_chars") or 0)
        pdf_chars = int(rec.get("pdf_extracted_chars") or 0)
        change = rec.get("change_status", "UNKNOWN")
        limit_note = rec.get("limitations_notes") or rec.get("error") or ""
        norm_hash = str(rec.get("normalized_hash") or "")[:10] or "—"
        raw_hash = str(rec.get("raw_hash") or "")[:10] or "—"
        snap = rec.get("snapshot_normalized_path") or rec.get("snapshot_raw_path") or ""
        print(
            f"{ts}  {quality:<7} {change:<12} "
            f"{chars:>7,}c n={norm_chars:>7,} h={norm_hash:<10} "
            f"raw={raw_hash:<10} + {pdf_chars:>7,}pdf  {name}"
        )
        if limit_note:
            print(f"  - {limit_note[:140]}")
        if snap:
            print(f"  - snapshot: {snap}")
        if rec.get("diff_json_path"):
            print(f"  - diff: {rec.get('diff_json_path')}")
        if rec.get("proof_block_path"):
            print(f"  - proof: {rec.get('proof_block_path')}")
