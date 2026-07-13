"""Tests for the external RFC 3161 trusted-timestamp anchor (branch tenten).

The anchor upgrades the internal hash chain from tamper-evident to
externally-anchored: a third-party TSA signs a token binding the head record_hash
to a time StatuteProof cannot backdate. It is ADDITIVE and DORMANT by default.

Every test uses a MOCKED TSA — a self-signed test cert and a locally-assembled
RFC 3161 token — so NO real network is ever touched. Coverage:

* disabled-by-default is a complete no-op (None, and the transport is never called);
* the request builds a well-formed message imprint (raw SHA-256 digest, sha256);
* verify PASSES on a matching token and FAILS on a mismatched digest / tampered token;
* graceful degradation: TSA timeout / error / non-granted status -> None, never raises;
* the additive sidecar is written (JSON + raw .tsr) and re-anchoring the same head is
  idempotent (no second network call);
* the source_runs head-update wiring stays dormant when unset (no sidecar) and anchors
  when enabled;
* existing evidence records without a token stay 100% valid (no regression);
* the public verifier optionally reports the external timestamp (absence is silent);
* the regulator binder embeds + reports the anchor only when a sidecar exists.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The anchor's crypto path relies on asn1crypto (optional dep) + cryptography
# (present in prod via pdfminer.six). Skip cleanly on a stripped env rather than error.
asn1crypto = pytest.importorskip("asn1crypto")
pytest.importorskip("cryptography")

from asn1crypto import algos, cms, core, tsp
from asn1crypto import x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from app import rfc3161_anchor as anchor


# ── mocked-TSA test material ─────────────────────────────────────────────────────

_GEN_TIME = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)


def _make_test_ca() -> tuple[Any, bytes]:  # type: ignore[valid-type]
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "StatuteProof Test TSA")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime(2020, 1, 1, tzinfo=timezone.utc))
        .not_valid_after(datetime(2035, 1, 1, tzinfo=timezone.utc))
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.TIME_STAMPING]), critical=True
        )
        .sign(key, hashes.SHA256())
    )
    return key, cert.public_bytes(serialization.Encoding.DER)


_TSA_KEY, _TSA_CERT_DER = _make_test_ca()


def _make_token(
    digest_hex: str,
    *,
    gen_time: datetime = _GEN_TIME,
    embed_cert: bool = True,
    key=_TSA_KEY,
    cert_der: bytes = _TSA_CERT_DER,
    serial: int = 42,
) -> bytes:
    """Assemble a genuine RFC 3161 timestamp token (CMS SignedData) for a digest."""
    digest = bytes.fromhex(digest_hex)
    tst = tsp.TSTInfo(
        {
            "version": "v1",
            "policy": "1.2.3.4.1",
            "message_imprint": tsp.MessageImprint(
                {
                    "hash_algorithm": algos.DigestAlgorithm({"algorithm": "sha256"}),
                    "hashed_message": digest,
                }
            ),
            "serial_number": serial,
            "gen_time": gen_time,
        }
    )
    tst_der = tst.dump()
    signed_attrs = cms.CMSAttributes(
        [
            cms.CMSAttribute({"type": "content_type", "values": ["tst_info"]}),
            cms.CMSAttribute({"type": "message_digest", "values": [hashlib.sha256(tst_der).digest()]}),
        ]
    )
    signature = key.sign(signed_attrs.dump(), padding.PKCS1v15(), hashes.SHA256())
    asn1cert = asn1_x509.Certificate.load(cert_der)
    signer_info = cms.SignerInfo(
        {
            "version": "v1",
            "sid": cms.SignerIdentifier(
                {
                    "issuer_and_serial_number": cms.IssuerAndSerialNumber(
                        {"issuer": asn1cert.issuer, "serial_number": asn1cert.serial_number}
                    )
                }
            ),
            "digest_algorithm": algos.DigestAlgorithm({"algorithm": "sha256"}),
            "signed_attrs": signed_attrs,
            "signature_algorithm": algos.SignedDigestAlgorithm({"algorithm": "rsassa_pkcs1v15"}),
            "signature": signature,
        }
    )
    signed_data = cms.SignedData(
        {
            "version": "v3",
            "digest_algorithms": [algos.DigestAlgorithm({"algorithm": "sha256"})],
            "encap_content_info": cms.EncapsulatedContentInfo(
                {"content_type": "tst_info", "content": core.ParsableOctetString(tst_der)}
            ),
            "certificates": ([asn1cert] if embed_cert else []),
            "signer_infos": [signer_info],
        }
    )
    return cms.ContentInfo({"content_type": "signed_data", "content": signed_data}).dump()


def _granted_response(token_der: bytes) -> bytes:
    return tsp.TimeStampResp(
        {
            "status": tsp.PKIStatusInfo({"status": "granted"}),
            "time_stamp_token": cms.ContentInfo.load(token_der),
        }
    ).dump()


def _digest(data: bytes = b"chain-head") -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def enabled(monkeypatch):
    """Enable the anchor and route the transport to a canned, echoing mock TSA."""
    monkeypatch.setenv(anchor.ENV_TSA_URL, "https://tsa.test.invalid/tsr")
    calls: list[bytes] = []

    def _fake_post(url, req_der, timeout):
        calls.append(req_der)
        parsed = tsp.TimeStampReq.load(req_der)
        imprint = parsed["message_imprint"]["hashed_message"].native
        return _granted_response(_make_token(imprint.hex()))

    monkeypatch.setattr(anchor, "_post_timestamp_query", _fake_post)
    return calls


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Guarantee the anchor is dormant unless a test opts in."""
    monkeypatch.delenv(anchor.ENV_TSA_URL, raising=False)
    yield


# ── 1. dormant by default = complete no-op ──────────────────────────────────────

def test_disabled_by_default_no_network(monkeypatch):
    boom = lambda *a, **k: pytest.fail("transport must NOT be called when disabled")  # noqa: E731
    monkeypatch.setattr(anchor, "_post_timestamp_query", boom)

    assert anchor.anchor_enabled() is False
    assert anchor.request_timestamp(_digest()) is None


def test_maybe_anchor_head_disabled_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(anchor, "_post_timestamp_query", lambda *a, **k: pytest.fail("no network"))
    head_file = tmp_path / "data" / "evidence_chain_head.json"

    assert anchor.maybe_anchor_head(_digest(), head_file) is None
    assert not anchor.sidecar_path_for(head_file).exists()


def test_spawn_head_anchor_disabled_is_noop(tmp_path):
    head_file = tmp_path / "data" / "evidence_chain_head.json"
    before = threading.active_count()
    anchor.spawn_head_anchor(_digest(), head_file)
    # No thread spawned, no sidecar created.
    assert threading.active_count() == before
    assert not anchor.sidecar_path_for(head_file).exists()


# ── 2. request builds a well-formed imprint ─────────────────────────────────────

def test_request_builds_wellformed_imprint(enabled):
    digest = _digest(b"well-formed")
    out = anchor.request_timestamp(digest)

    assert out is not None
    assert len(enabled) == 1
    req = tsp.TimeStampReq.load(enabled[0])
    assert req["version"].native == "v1"
    assert req["message_imprint"]["hash_algorithm"]["algorithm"].native == "sha256"
    # The imprint carries the RAW digest bytes (openssl-compatible), not a re-hash.
    assert req["message_imprint"]["hashed_message"].native == bytes.fromhex(digest)
    assert req["cert_req"].native is True
    assert req["nonce"].native is not None


def test_request_returns_none_for_non_sha256_digest(enabled):
    assert anchor.request_timestamp("not-a-hash") is None
    assert anchor.request_timestamp("abc123") is None
    assert enabled == []  # never reached the transport


def test_request_timestamp_fields(enabled):
    digest = _digest(b"fields")
    out = anchor.request_timestamp(digest)

    assert out["token_format"] == anchor.TOKEN_FORMAT
    assert out["tsa_url"] == "https://tsa.test.invalid/tsr"
    assert out["digest_hex"] == digest
    assert out["digest_algorithm"] == "sha256"
    assert out["asserted_time_utc"] == "2026-07-12T10:00:00Z"
    assert base64.b64decode(out["token_b64"])  # decodes


# ── 3/4. verify passes on match, fails on mismatch / tamper ──────────────────────

def test_verify_passes_on_matching_token():
    digest = _digest(b"match")
    token_b64 = base64.b64encode(_make_token(digest)).decode()

    result = anchor.verify_timestamp_token(token_b64, digest)

    assert result["verified"] is True
    assert result["timestamp_utc"] == "2026-07-12T10:00:00Z"
    assert result["tsa_name"] == "StatuteProof Test TSA"
    statuses = {c["name"]: c["status"] for c in result["checks"]}
    assert statuses["imprint_matches_digest"] == "pass"
    assert statuses["signature_valid"] == "pass"
    assert statuses["cert_chain_to_trusted_root"] == "skipped"  # honest scope


def test_verify_fails_on_mismatched_digest():
    token_b64 = base64.b64encode(_make_token(_digest(b"anchored"))).decode()

    result = anchor.verify_timestamp_token(token_b64, _digest(b"different"))

    assert result["verified"] is False
    statuses = {c["name"]: c["status"] for c in result["checks"]}
    assert statuses["imprint_matches_digest"] == "fail"


def test_verify_fails_on_tampered_token():
    digest = _digest(b"tamper")
    token = bytearray(_make_token(digest))
    token[-40] ^= 0xFF  # flip a byte inside the signature region
    token_b64 = base64.b64encode(bytes(token)).decode()

    result = anchor.verify_timestamp_token(token_b64, digest)

    assert result["verified"] is False


def test_verify_fails_closed_on_malformed_inputs():
    good = base64.b64encode(_make_token(_digest())).decode()
    assert anchor.verify_timestamp_token(good, "not-hex")["verified"] is False
    assert anchor.verify_timestamp_token("!!!not-base64!!!", _digest())["verified"] is False
    assert anchor.verify_timestamp_token("", _digest())["verified"] is False
    # A valid-base64 but non-token blob fails token_parsed, never raises.
    assert anchor.verify_timestamp_token(base64.b64encode(b"junk").decode(), _digest())["verified"] is False


def test_verify_without_embedded_cert_is_unverified_not_crash():
    digest = _digest(b"no-cert")
    token_b64 = base64.b64encode(_make_token(digest, embed_cert=False)).decode()

    result = anchor.verify_timestamp_token(token_b64, digest)

    # Imprint still matches, but with no embedded cert the signature can't be
    # checked -> reported unverified (fail-closed), never a false pass.
    assert result["verified"] is False
    statuses = {c["name"]: c["status"] for c in result["checks"]}
    assert statuses["imprint_matches_digest"] == "pass"
    assert statuses["signature_valid"] == "skipped"


# ── 5. graceful degradation ─────────────────────────────────────────────────────

def test_graceful_degradation_on_timeout(monkeypatch):
    monkeypatch.setenv(anchor.ENV_TSA_URL, "https://tsa.test.invalid/tsr")

    def _timeout(url, req_der, timeout):
        raise TimeoutError("TSA did not respond in time")

    monkeypatch.setattr(anchor, "_post_timestamp_query", _timeout)
    # Never raises; returns None so the pipeline continues.
    assert anchor.request_timestamp(_digest()) is None


def test_graceful_degradation_on_transport_error(monkeypatch):
    monkeypatch.setenv(anchor.ENV_TSA_URL, "https://tsa.test.invalid/tsr")
    monkeypatch.setattr(
        anchor, "_post_timestamp_query", lambda *a, **k: (_ for _ in ()).throw(OSError("conn refused"))
    )
    assert anchor.request_timestamp(_digest()) is None


def test_graceful_degradation_on_non_granted_status(monkeypatch):
    monkeypatch.setenv(anchor.ENV_TSA_URL, "https://tsa.test.invalid/tsr")

    def _rejection(url, req_der, timeout):
        return tsp.TimeStampResp({"status": tsp.PKIStatusInfo({"status": "rejection"})}).dump()

    monkeypatch.setattr(anchor, "_post_timestamp_query", _rejection)
    assert anchor.request_timestamp(_digest()) is None


def test_graceful_degradation_on_garbage_response(monkeypatch):
    monkeypatch.setenv(anchor.ENV_TSA_URL, "https://tsa.test.invalid/tsr")
    monkeypatch.setattr(anchor, "_post_timestamp_query", lambda *a, **k: b"\x00\x01not-a-response")
    assert anchor.request_timestamp(_digest()) is None


# ── 6. storage sidecar + idempotency ────────────────────────────────────────────

def test_sidecar_written_and_roundtrip_verifies(tmp_path, enabled):
    head_file = tmp_path / "data" / "evidence_chain_head.json"
    digest = _digest(b"stored-head")

    out = anchor.maybe_anchor_head(digest, head_file)

    assert out is not None
    assert out["anchored_head_record_hash"] == digest
    sidecar = anchor.sidecar_path_for(head_file)
    tsr = head_file.with_name(anchor.SIDECAR_TSR_NAME)
    assert sidecar.exists() and tsr.exists()
    stored = json.loads(sidecar.read_text())
    assert stored["anchored_head_record_hash"] == digest
    # The raw .tsr is the exact DER token and re-verifies offline.
    reloaded = base64.b64encode(tsr.read_bytes()).decode()
    assert anchor.verify_timestamp_token(reloaded, digest)["verified"] is True


def test_reanchoring_same_head_is_idempotent(tmp_path, enabled):
    head_file = tmp_path / "data" / "evidence_chain_head.json"
    digest = _digest(b"idem")

    first = anchor.maybe_anchor_head(digest, head_file)
    assert len(enabled) == 1
    second = anchor.maybe_anchor_head(digest, head_file)  # same head -> cached
    assert len(enabled) == 1  # NO second network call
    assert second == first

    other = anchor.maybe_anchor_head(_digest(b"advanced"), head_file)  # new head -> anchored
    assert len(enabled) == 2
    assert other["anchored_head_record_hash"] == _digest(b"advanced")


def test_spawn_head_anchor_async_writes_sidecar(tmp_path, enabled):
    head_file = tmp_path / "data" / "evidence_chain_head.json"
    digest = _digest(b"async")

    anchor.spawn_head_anchor(digest, head_file)

    # Wait (bounded) for the daemon thread to release the in-flight guard.
    assert anchor._INFLIGHT.acquire(timeout=5.0)
    anchor._INFLIGHT.release()
    sidecar = anchor.sidecar_path_for(head_file)
    assert sidecar.exists()
    assert json.loads(sidecar.read_text())["anchored_head_record_hash"] == digest


# ── 7. source_runs head-update wiring stays dormant / anchors when enabled ───────

def _isolate_trail(tmp_path, monkeypatch):
    from app import source_runs

    run_dir = tmp_path / "data" / "source_runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(source_runs, "_RUN_DIR", run_dir)
    monkeypatch.setattr(source_runs, "_RUN_FILE", run_dir / "source_runs.jsonl")
    return source_runs


def test_write_chain_head_dormant_writes_no_sidecar(tmp_path, monkeypatch):
    source_runs = _isolate_trail(tmp_path, monkeypatch)
    monkeypatch.setattr(anchor, "_post_timestamp_query", lambda *a, **k: pytest.fail("no network"))

    source_runs._write_chain_head("a" * 64)

    head_file = source_runs._chain_head_file()
    assert head_file.exists()  # head anchor still written (existing behavior intact)
    assert not anchor.sidecar_path_for(head_file).exists()  # no external anchor


def test_write_chain_head_enabled_anchors(tmp_path, monkeypatch):
    source_runs = _isolate_trail(tmp_path, monkeypatch)
    monkeypatch.setenv(anchor.ENV_TSA_URL, "https://tsa.test.invalid/tsr")
    monkeypatch.setattr(
        anchor,
        "_post_timestamp_query",
        lambda url, req_der, timeout: _granted_response(
            _make_token(tsp.TimeStampReq.load(req_der)["message_imprint"]["hashed_message"].native.hex())
        ),
    )
    # Run the anchor synchronously so the wiring is deterministic to assert.
    monkeypatch.setattr(anchor, "spawn_head_anchor", anchor.maybe_anchor_head)

    head = "b" * 64
    source_runs._write_chain_head(head)

    sidecar = anchor.sidecar_path_for(source_runs._chain_head_file())
    assert sidecar.exists()
    assert json.loads(sidecar.read_text())["anchored_head_record_hash"] == head


# ── 8. no regression: records without a token stay valid; public verifier additive ─

def _sealed_record(tmp_path):
    from app.evidence_records import create_canonical_evidence_record
    from app.text_normalization import normalize_for_change_hash

    text = "Official regulatory text for external-anchor regression checks.\n"
    normalized = normalize_for_change_hash(text)
    run_dir = tmp_path / "data" / "source_snapshots" / "2026-03-15" / "AE" / "cbuae-anchor" / "run-x"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw.txt").write_text(text, encoding="utf-8")
    (run_dir / "normalized.txt").write_text(normalized, encoding="utf-8")
    (run_dir / "metadata.json").write_text(json.dumps({"provider": "fixture"}), encoding="utf-8")
    (run_dir / "proof.json").write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")
    run = {
        "run_id": "run-x",
        "timestamp_utc": "2026-03-15T10:00:00Z",
        "market": "AE",
        "source_id": "cbuae-anchor",
        "source_name": "CBUAE Anchor Test",
        "category": "regulatory",
        "official_url": "https://example.gov/cbuae-anchor",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "FIRST_SEEN",
        "normalized_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(tmp_path)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(tmp_path)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(tmp_path)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(tmp_path)),
    }
    record = create_canonical_evidence_record(run, base_dir=tmp_path)
    return record, text, normalized


def test_existing_record_without_token_still_verifies(tmp_path):
    from app.public_verify import verify_submission

    record, raw, normalized = _sealed_record(tmp_path)
    result = verify_submission(record, raw=raw, normalized=normalized)

    assert result["verified"] is True
    assert "external_timestamp" not in result  # absence is silent, not a failure


def test_public_verifier_reports_external_timestamp_when_present(tmp_path):
    from app.public_verify import verify_submission

    record, raw, normalized = _sealed_record(tmp_path)
    # Anchor the record's own record_hash so the optional token matches it.
    record_hash = str(record["record_hash"]).removeprefix("sha256:")
    token_b64 = base64.b64encode(_make_token(record_hash)).decode()

    result = verify_submission(
        record, raw=raw, normalized=normalized, timestamp_token=token_b64
    )

    # Record-integrity gate is unaffected; the external block is additive.
    assert result["verified"] is True
    ext = result["external_timestamp"]
    assert ext["present"] is True
    assert ext["verified"] is True
    assert ext["timestamp_utc"] == "2026-07-12T10:00:00Z"


def test_public_verifier_external_timestamp_reports_mismatch(tmp_path):
    from app.public_verify import verify_submission

    record, raw, normalized = _sealed_record(tmp_path)
    token_b64 = base64.b64encode(_make_token(_digest(b"unrelated-head"))).decode()

    result = verify_submission(
        record, raw=raw, normalized=normalized, timestamp_token=token_b64,
        timestamp_digest=_digest(b"unrelated-head"),
    )

    # A valid token for a DIFFERENT digest: record still verified, token verified
    # against its own digest, but does not claim to attest this record.
    assert result["verified"] is True
    assert result["external_timestamp"]["verified"] is True
    assert result["external_timestamp"]["checked_digest"] == _digest(b"unrelated-head")


# ── 9. regulator binder embeds + reports the anchor only when present ────────────

def test_binder_omits_external_timestamp_when_no_sidecar(tmp_path):
    from app.regulator_binder import build_regulator_binder

    _sealed_record(tmp_path)  # one FIRST_SEEN record in range
    out = build_regulator_binder(
        ["cbuae-anchor"], "2026-03-01", "2026-03-31", base_dir=tmp_path,
        output_dir=tmp_path / "out",
    )
    assert out["status"] == "ok"
    assert out["has_external_timestamp"] is False
    assert "external_timestamp" not in out["manifest"]


def test_binder_includes_and_reports_external_timestamp(tmp_path):
    from app.regulator_binder import build_regulator_binder

    _sealed_record(tmp_path)
    # Write a head-anchor sidecar exactly as the enabled anchor would.
    head_file = tmp_path / "data" / "evidence_chain_head.json"
    head_file.parent.mkdir(parents=True, exist_ok=True)
    head_file.write_text(json.dumps({"head_record_hash": "c" * 64}), encoding="utf-8")
    digest = _digest(b"binder-head")
    anchor.write_head_anchor_sidecar(
        head_file,
        {
            "token_b64": base64.b64encode(_make_token(digest)).decode(),
            "token_format": anchor.TOKEN_FORMAT,
            "tsa_url": "https://tsa.test.invalid/tsr",
            "digest_algorithm": "sha256",
            "anchored_head_record_hash": digest,
            "asserted_time_utc": "2026-07-12T10:00:00Z",
            "requested_at": "2026-07-12T10:00:01Z",
        },
    )

    out = build_regulator_binder(
        ["cbuae-anchor"], "2026-03-01", "2026-03-31", base_dir=tmp_path,
        output_dir=tmp_path / "out",
    )

    assert out["status"] == "ok"
    assert out["has_external_timestamp"] is True
    ext = out["manifest"]["external_timestamp"]
    assert ext["anchored_head_record_hash"] == digest
    assert ext["tsa_url"] == "https://tsa.test.invalid/tsr"

    import zipfile

    with zipfile.ZipFile(out["binder_path"]) as zf:
        names = zf.namelist()
        assert ext["token_file"] in names
        # The embedded standalone verify.py reports the external anchor.
        verify_src = zf.read("verify.py").decode("utf-8")
        assert "external_timestamp" in verify_src
        assert "External RFC 3161 timestamp anchor present" in verify_src


# ── transport hardening (bounded read + no redirect + scheme) ────────────────────

def test_post_query_rejects_non_http_scheme():
    """A non-http(s) TSA URL is refused before any network I/O (SSRF/scheme guard)."""
    with pytest.raises(ValueError):
        anchor._post_timestamp_query("ftp://tsa.example/tsr", b"req", 5.0)
    with pytest.raises(ValueError):
        anchor._post_timestamp_query("file:///etc/passwd", b"req", 5.0)


def test_post_query_bounds_oversized_response(monkeypatch):
    """A TSA that returns more than the cap raises (bounded transport, VARA policy)."""
    class _FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, size=-1):
            # Hand back more than the cap regardless of the requested size.
            return b"x" * (anchor._MAX_TSR_BYTES + 10)

    monkeypatch.setattr(anchor._TSA_OPENER, "open", lambda *a, **k: _FakeResp())
    with pytest.raises(ValueError):
        anchor._post_timestamp_query("https://tsa.example/tsr", b"req", 5.0)


def test_oversized_response_degrades_to_none(monkeypatch):
    """End to end: an oversized TSA body makes request_timestamp degrade to None,
    never raising into the (best-effort) anchor path."""
    monkeypatch.setenv("RFC3161_TSA_URL", "https://tsa.example/tsr")

    class _FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, size=-1):
            return b"x" * (anchor._MAX_TSR_BYTES + 10)

    monkeypatch.setattr(anchor._TSA_OPENER, "open", lambda *a, **k: _FakeResp())
    digest = hashlib.sha256(b"head").hexdigest()
    assert anchor.request_timestamp(digest) is None


def test_verify_rejects_oversized_token_before_parse():
    """A token past the size cap is refused (token_bounded) before any ASN.1 parse."""
    huge = "A" * (anchor._MAX_TOKEN_B64_LEN + 4)
    report = anchor.verify_timestamp_token(huge, hashlib.sha256(b"x").hexdigest())
    assert report["verified"] is False
    assert "token_bounded" in json.dumps(report)


def _anchor_dict(n: int) -> dict:
    digest = _digest(f"head-{n}".encode())
    return {
        "token_b64": base64.b64encode(_make_token(digest)).decode(),
        "token_format": anchor.TOKEN_FORMAT,
        "tsa_url": "https://tsa.test.invalid/tsr",
        "digest_algorithm": "sha256",
        "anchored_head_record_hash": digest,
        "asserted_time_utc": f"2026-07-12T10:0{n}:00Z",
    }


def test_reanchor_preserves_prior_tokens_in_history(tmp_path):
    """A new anchor must NEVER destroy an earlier RFC 3161 token — prior anchors
    accumulate in ``history`` with their token_b64 intact."""
    head_file = tmp_path / "data" / "evidence_chain_head.json"
    head_file.parent.mkdir(parents=True, exist_ok=True)

    a1, a2, a3 = _anchor_dict(1), _anchor_dict(2), _anchor_dict(3)
    anchor.write_head_anchor_sidecar(head_file, a1)
    anchor.write_head_anchor_sidecar(head_file, a2)
    anchor.write_head_anchor_sidecar(head_file, a3)

    side = anchor.read_head_anchor_sidecar(head_file)
    # Current anchor is the latest.
    assert side["anchored_head_record_hash"] == a3["anchored_head_record_hash"]
    # History preserves BOTH prior anchors, oldest first, tokens intact.
    hist_heads = [h["anchored_head_record_hash"] for h in side["history"]]
    assert hist_heads == [a1["anchored_head_record_hash"], a2["anchored_head_record_hash"]]
    assert side["history"][0]["token_b64"] == a1["token_b64"]  # prior token NOT destroyed
    assert side["history"][1]["token_b64"] == a2["token_b64"]
    # History entries never nest their own history.
    assert all("history" not in h for h in side["history"])


def test_idempotent_reanchor_same_head_does_not_duplicate(tmp_path):
    head_file = tmp_path / "data" / "evidence_chain_head.json"
    head_file.parent.mkdir(parents=True, exist_ok=True)
    a = _anchor_dict(1)
    anchor.write_head_anchor_sidecar(head_file, a)
    anchor.write_head_anchor_sidecar(head_file, a)  # same head written again
    side = anchor.read_head_anchor_sidecar(head_file)
    # The identical anchor is not folded in twice — no history key is written.
    assert side.get("history", []) == []
