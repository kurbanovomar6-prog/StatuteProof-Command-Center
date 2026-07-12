"""External RFC 3161 trusted-timestamp anchor for the evidence chain head.

THE CAPSTONE OF THE MOAT (and why it is OFF by default):

The internal hash chain (``app/source_runs.py``) is tamper-**evident**: it detects
in-place, un-relinked edits. Its honest limit (documented in
``docs/EVIDENCE-VERIFICATION-SPEC.md`` §1/§5) is that an actor with write access who
also *relinks* the whole trail produces a chain that re-verifies clean. Only an
anchor that StatuteProof **cannot forge** closes that gap: a third-party RFC 3161
Time-Stamping Authority (TSA) signs a token binding the head ``record_hash`` to a
time. A relinked trail cannot reproduce a TSA token that predates the relink. That
upgrades the guarantee from *tamper-evident* to *externally-anchored
tamper-evident* — verifiable by anyone who trusts the TSA, not StatuteProof.

SAFETY POSTURE — this module touches the evidence core on a live product, so every
default is chosen to do NOTHING until an operator opts in:

* **DORMANT BY DEFAULT.** Every entry point is gated on :func:`anchor_enabled`,
  which is true ONLY when the ``RFC3161_TSA_URL`` environment variable is set to a
  non-empty value. There is NO default TSA. If unset, :func:`request_timestamp`,
  :func:`maybe_anchor_head`, and :func:`spawn_head_anchor` are complete no-ops:
  zero network calls, zero threads, zero files, and the capture pipeline is
  byte-for-byte unchanged.
* **ADDITIVE + BACKWARD-COMPATIBLE.** The token is persisted as an ADDITIVE sidecar
  next to the head-anchor file (``evidence_chain_head.tsr.json`` +
  ``evidence_chain_head.tsr``). No existing evidence record, trail line, or head
  file is ever mutated. Records without a timestamp token stay 100% valid.
* **OUT OF THE CAPTURE HOT PATH.** :func:`spawn_head_anchor` fires the network
  request on a daemon thread with a single-in-flight guard, so a source capture
  never blocks on the TSA and the TSA is never hammered per-append.
* **GRACEFUL DEGRADATION.** Any failure — TSA unreachable, timeout, malformed
  response, missing optional dependency — is logged and swallowed. Nothing here
  ever raises into the pipeline, and evidence is never lost or corrupted.

DEPENDENCIES (lazy, only on the enabled path):

* ``asn1crypto`` — pure-Python ASN.1 with a purpose-built ``asn1crypto.tsp``
  module (``TimeStampReq`` / ``TimeStampResp`` / ``TSTInfo``). Used to BUILD the
  request and PARSE the token. Imported lazily; when the anchor is dormant it is
  never imported. Declared as an OPTIONAL, pinned dependency in requirements.txt.
* ``cryptography`` — used only to VERIFY the TSA signature against an embedded
  signing certificate. Already a guaranteed transitive dependency in production
  (required by ``pdfminer.six``). If it is ever absent, the signature check
  degrades to ``skipped`` (fail-closed: the token is then reported unverified),
  never an exception.

HONEST SCOPE OF :func:`verify_timestamp_token` (stated plainly, not oversold):
it confirms OFFLINE that (a) the token parses, (b) the message imprint equals the
digest you hold, (c) the signed message-digest attribute binds the signature to the
token's TSTInfo, and (d) the TSA's signature verifies against the certificate
embedded in the token. It does **not** validate the certificate chain to a trusted
root TSA CA — this module ships no trust store — so it proves "signed by the holder
of this embedded key", not "signed by a CA you have independently decided to trust".
That final trust decision belongs to the verifier, who can check the embedded cert
against their own trusted TSA roots (e.g. with ``openssl ts -verify``).
"""

from __future__ import annotations

import base64
import logging
import os
import re
import tempfile
import threading
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── configuration (environment-driven; read fresh at call time) ─────────────────
#
# Read via os.environ at call time (never cached at import) so operators can flip
# the anchor on/off without a restart and so tests can monkeypatch cleanly.
ENV_TSA_URL = "RFC3161_TSA_URL"
ENV_TIMEOUT_S = "RFC3161_TSA_TIMEOUT_S"
ENV_CERT_REQ = "RFC3161_TSA_CERT_REQ"
ENV_POLICY_OID = "RFC3161_TSA_POLICY_OID"

# The imprint is always SHA-256 (matching the head record_hash flavor). Fixed, not
# operator-tunable: the head record_hash is a SHA-256 digest and the sidecar/verify
# path assume this one algorithm end to end.
_IMPRINT_ALGORITHM = "sha256"

# Bounded transport timeout. Clamped so a hostile/typo'd env value can neither hang
# the caller forever nor set an absurdly long ceiling.
_DEFAULT_TIMEOUT_S = 10.0
_MIN_TIMEOUT_S = 1.0
_MAX_TIMEOUT_S = 60.0

# RFC 3161 wire content types.
_CONTENT_TYPE_QUERY = "application/timestamp-query"
_CONTENT_TYPE_REPLY = "application/timestamp-reply"

# Storage: additive sidecar filenames written NEXT TO evidence_chain_head.json.
SIDECAR_JSON_NAME = "evidence_chain_head.tsr.json"
SIDECAR_TSR_NAME = "evidence_chain_head.tsr"

# Marker stamped into the sidecar so a recipient knows exactly what token_b64 holds.
TOKEN_FORMAT = "rfc3161-timestamp-token-der-base64"

_SHA256_HEX_RE = re.compile(r"^[a-f0-9]{64}$")

# A single-in-flight guard so per-append head updates can never spawn an unbounded
# number of anchor threads or hammer the TSA: while one anchor request is running,
# further spawn requests are dropped (the next head update will anchor the newer
# head once the current one finishes).
_INFLIGHT = threading.Lock()


# ── configuration accessors ─────────────────────────────────────────────────────

def _tsa_url() -> str:
    """The configured TSA URL, stripped; empty string when unset (=> dormant)."""
    return str(os.environ.get(ENV_TSA_URL) or "").strip()


def anchor_enabled() -> bool:
    """True only when an operator has configured a TSA URL.

    This is THE dormant-by-default guard. Every side-effecting entry point checks
    it first; when it returns False the anchor is a complete no-op (no network, no
    thread, no files). There is intentionally no default TSA.
    """
    return bool(_tsa_url())


def _timeout_s() -> float:
    raw = str(os.environ.get(ENV_TIMEOUT_S) or "").strip()
    if not raw:
        return _DEFAULT_TIMEOUT_S
    try:
        value = float(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT_S
    return max(_MIN_TIMEOUT_S, min(_MAX_TIMEOUT_S, value))


def _cert_req() -> bool:
    # Default true: ask the TSA to embed its signing cert so the token is
    # independently verifiable offline. Operators can disable for TSAs that
    # reject certReq, at the cost of offline signature verification.
    raw = str(os.environ.get(ENV_CERT_REQ) or "true").strip().lower()
    return raw not in {"false", "0", "no", "off"}


def _policy_oid() -> str:
    return str(os.environ.get(ENV_POLICY_OID) or "").strip()


def _imprint_bytes(digest_hex: str) -> bytes | None:
    """Return the raw digest bytes for the message imprint, or None if malformed.

    The head ``record_hash`` is a bare 64-char lowercase SHA-256 hex digest. The
    RFC 3161 message imprint carries the raw digest bytes directly with
    ``hashAlgorithm = sha256`` — exactly how ``openssl ts -query -digest <hex>
    -sha256`` builds it — so a token produced here is also verifiable with plain
    ``openssl ts``. We only anchor genuine SHA-256 head hashes; anything else is
    refused (logged, no request sent).
    """
    text = str(digest_hex or "").strip().lower()
    if not _SHA256_HEX_RE.match(text):
        return None
    return bytes.fromhex(text)


# ── request side (network) ──────────────────────────────────────────────────────

# An RFC 3161 timestamp response is a few KB; anything larger is a misbehaving or
# hostile TSA. Cap the read (the project's bounded-transport policy — commit
# 14981dd, VARA mojibake incident: never read an unbounded network body).
_MAX_TSR_BYTES = 1_048_576  # 1 MB

# Max accepted base64 length of a submitted timestamp token before it is decoded +
# ASN.1-parsed offline. A real RFC 3161 token is a few KB; 64 KB is generous.
_MAX_TOKEN_B64_LEN = 65_536


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects: a compromised/MITM'd TSA must not be able to pivot the
    request to an internal target (SSRF). We only ever talk to the exact
    operator-configured TSA URL."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: A002,D102
        return None


# One opener with redirects disabled, reused for every (operator-configured) TSA call.
_TSA_OPENER = urllib.request.build_opener(_NoRedirect)


def _post_timestamp_query(tsa_url: str, request_der: bytes, timeout: float) -> bytes:
    """POST a DER TimeStampReq to the TSA and return the raw response bytes (bounded).

    Isolated as the single transport seam so tests can monkeypatch it with a canned
    response (no real network). Raises on any transport error, an unsupported scheme,
    or an over-cap body; callers convert that into graceful degradation. Redirects are
    disabled and the read is bounded (defense-in-depth for a semi-external party).
    """
    if not (tsa_url.startswith("http://") or tsa_url.startswith("https://")):
        raise ValueError("TSA URL must use the http(s) scheme")
    request = urllib.request.Request(
        tsa_url,
        data=request_der,
        method="POST",
        headers={
            "Content-Type": _CONTENT_TYPE_QUERY,
            "Accept": _CONTENT_TYPE_REPLY,
            "Content-Length": str(len(request_der)),
        },
    )
    with _TSA_OPENER.open(request, timeout=timeout) as response:  # noqa: S310 (operator-configured URL; redirects disabled)
        body = response.read(_MAX_TSR_BYTES + 1)
    if len(body) > _MAX_TSR_BYTES:
        raise ValueError("TSA response exceeds the 1 MB bound")
    return body


def request_timestamp(digest_hex: str) -> dict[str, Any] | None:
    """Request an RFC 3161 timestamp token for ``digest_hex`` from the configured TSA.

    Returns a JSON-serializable dict describing the token on success, or ``None`` on
    ANY failure (disabled, malformed digest, missing dependency, network/timeout,
    non-granted TSA status, parse error) — every failure is logged, never raised.

    Dormant-by-default: returns ``None`` immediately when :func:`anchor_enabled` is
    False, before importing anything heavy or touching the network.
    """
    if not anchor_enabled():
        return None

    imprint = _imprint_bytes(digest_hex)
    if imprint is None:
        logger.warning(
            "rfc3161_anchor: refusing to timestamp a non-SHA-256 digest (got %r).",
            (str(digest_hex) or "")[:16],
        )
        return None

    try:
        from asn1crypto import algos, core, tsp
    except Exception:  # dependency not installed on the enabled path
        logger.warning(
            "rfc3161_anchor: asn1crypto is not installed; cannot build a "
            "TimeStampReq. Install the optional dependency to enable anchoring."
        )
        return None

    tsa_url = _tsa_url()
    timeout = _timeout_s()
    requested_at = _utc_now_iso()

    try:
        # A random nonce lets the caller detect a replayed/substituted response.
        nonce = int.from_bytes(os.urandom(16), "big")
        req_fields: dict[str, Any] = {
            "version": "v1",
            "message_imprint": tsp.MessageImprint(
                {
                    "hash_algorithm": algos.DigestAlgorithm({"algorithm": _IMPRINT_ALGORITHM}),
                    "hashed_message": imprint,
                }
            ),
            "nonce": core.Integer(nonce),
            "cert_req": _cert_req(),
        }
        policy = _policy_oid()
        if policy:
            req_fields["req_policy"] = policy
        request_der = tsp.TimeStampReq(req_fields).dump()
    except Exception as exc:
        logger.warning("rfc3161_anchor: failed to build TimeStampReq: %s", type(exc).__name__)
        return None

    try:
        response_der = _post_timestamp_query(tsa_url, request_der, timeout)
    except Exception as exc:  # network error / timeout / HTTP error
        logger.warning(
            "rfc3161_anchor: TSA request to %s failed (%s); continuing without an "
            "external anchor.",
            tsa_url,
            type(exc).__name__,
        )
        return None

    try:
        token_der, asserted_time = _extract_token(response_der, nonce=nonce)
    except Exception as exc:
        logger.warning("rfc3161_anchor: could not parse TSA response: %s", type(exc).__name__)
        return None
    if token_der is None:
        return None

    return {
        "schema_version": "1.0",
        "token_format": TOKEN_FORMAT,
        "token_b64": base64.b64encode(token_der).decode("ascii"),
        "tsa_url": tsa_url,
        "digest_hex": str(digest_hex).strip().lower(),
        "digest_algorithm": _IMPRINT_ALGORITHM,
        "requested_at": requested_at,
        "asserted_time_utc": asserted_time,
        "nonce": str(nonce),
    }


def _extract_token(response_der: bytes, *, nonce: int | None = None) -> tuple[bytes | None, str | None]:
    """Parse a TimeStampResp, enforce a granted status, and return (token_der, time).

    ``time`` is the best-effort asserted UTC time lifted from the token's TSTInfo
    (advisory in the sidecar; the authoritative check is :func:`verify_timestamp_token`).
    A non-granted status or a nonce mismatch returns ``(None, None)``.
    """
    from asn1crypto import tsp

    resp = tsp.TimeStampResp.load(response_der)
    status = resp["status"]["status"].native
    # PKIStatus: granted(0) / granted_with_mods(1) are success; anything else fails.
    if status not in {"granted", "granted_with_mods"}:
        logger.warning("rfc3161_anchor: TSA returned non-granted status %r.", status)
        return None, None

    token = resp["time_stamp_token"]
    if token.native is None:
        logger.warning("rfc3161_anchor: TSA response carried no timeStampToken.")
        return None, None
    token_der = token.dump()

    asserted_time: str | None = None
    try:
        tst = _tst_info_from_token(token_der)
        if tst is not None:
            if nonce is not None:
                token_nonce = tst["nonce"].native
                if token_nonce is not None and int(token_nonce) != int(nonce):
                    logger.warning("rfc3161_anchor: TSA response nonce mismatch; rejecting.")
                    return None, None
            gen_time = tst["gen_time"].native
            if isinstance(gen_time, datetime):
                asserted_time = _to_utc_iso(gen_time)
    except Exception:
        # Advisory time only — never fail the request over it.
        asserted_time = None

    return token_der, asserted_time


# ── verify side (offline, fail-closed) ──────────────────────────────────────────

def verify_timestamp_token(token_b64: str, digest_hex: str) -> dict[str, Any]:
    """Verify an RFC 3161 timestamp token OFFLINE against ``digest_hex``.

    This is what a recipient / auditor runs. It performs NO network access. Returns
    a fail-closed envelope and NEVER raises::

        {
          "ok": True,
          "verified": <bool>,          # true only if imprint AND signature pass
          "checks": [ {name, status, detail}, ... ],
          "timestamp_utc": <str|None>, # asserted TSA time (advisory unless verified)
          "tsa_name": <str|None>,
          "serial_number": <str|None>,
          "digest_algorithm": "sha256",
        }

    ``verified`` is True only when the message imprint matches ``digest_hex`` AND the
    TSA signature verifies against an embedded certificate. If the signature cannot
    be checked (no embedded cert, or ``cryptography`` unavailable), the token is
    reported UNVERIFIED with an explanatory ``skipped`` check — never a false pass.
    Certificate-chain-to-trusted-root is intentionally out of scope and reported as
    ``not_checked`` (see the module docstring).
    """
    try:
        return _verify_timestamp_token_impl(token_b64, digest_hex)
    except Exception:  # absolute fail-closed backstop — never leak a stacktrace
        return {
            "ok": True,
            "verified": False,
            "checks": [_fail("internal_error", "Verification could not be completed for the submitted token.")],
            "timestamp_utc": None,
            "tsa_name": None,
            "serial_number": None,
            "digest_algorithm": _IMPRINT_ALGORITHM,
        }


def _verify_timestamp_token_impl(token_b64: str, digest_hex: str) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    result: dict[str, Any] = {
        "ok": True,
        "verified": False,
        "checks": checks,
        "timestamp_utc": None,
        "tsa_name": None,
        "serial_number": None,
        "digest_algorithm": _IMPRINT_ALGORITHM,
    }

    expected = _imprint_bytes(digest_hex)
    if expected is None:
        checks.append(_fail("digest_wellformed", "digest_hex is not a 64-char lowercase SHA-256 hex string."))
        return result
    checks.append(_pass("digest_wellformed", "digest_hex is a valid SHA-256 hex digest."))

    raw_b64 = str(token_b64 or "").strip()
    # Bound the token BEFORE any ASN.1 parsing so this offline verifier is safe
    # standalone regardless of caller (e.g. if later wired to the public, unauth
    # /api/verify): a real RFC 3161 token is a few KB; a larger blob is hostile.
    # Mirrors the bounded-transport discipline applied to the TSA response side.
    if len(raw_b64) > _MAX_TOKEN_B64_LEN:
        checks.append(_fail("token_bounded", "token_b64 exceeds the maximum accepted size."))
        return result
    try:
        token_der = base64.b64decode(raw_b64, validate=False)
    except Exception:
        checks.append(_fail("token_decodable", "token_b64 is not valid base64."))
        return result
    if not token_der:
        checks.append(_fail("token_decodable", "token_b64 decoded to empty bytes."))
        return result

    try:
        from asn1crypto import cms
    except Exception:
        checks.append(
            _skip(
                "token_parsed",
                "asn1crypto is not installed; cannot parse the token offline.",
            )
        )
        return result

    try:
        content_info = cms.ContentInfo.load(token_der)
        if content_info["content_type"].native != "signed_data":
            checks.append(_fail("token_parsed", "Token is not a CMS SignedData timestamp token."))
            return result
        signed_data = content_info["content"]
        tst = _tst_info_from_signed_data(signed_data)
        if tst is None:
            checks.append(_fail("token_parsed", "Token has no TSTInfo eContent."))
            return result
    except Exception:
        checks.append(_fail("token_parsed", "Token could not be parsed as an RFC 3161 timestamp token."))
        return result
    checks.append(_pass("token_parsed", "Token parsed as a CMS SignedData RFC 3161 timestamp token."))

    # (b) imprint matches the digest we hold.
    imprint_ok = _check_imprint(tst, expected, checks, result)

    # asserted time + serial, lifted for the envelope (advisory unless verified).
    try:
        gen_time = tst["gen_time"].native
        if isinstance(gen_time, datetime):
            result["timestamp_utc"] = _to_utc_iso(gen_time)
        serial = tst["serial_number"].native
        if serial is not None:
            result["serial_number"] = str(serial)
    except Exception:
        pass

    # (c)+(d) signed message-digest binding + TSA signature over the signed attrs.
    signature_ok = _check_signature(signed_data, checks, result)

    # Chain-to-trusted-root is deliberately out of scope (no bundled trust store).
    checks.append(
        _skip(
            "cert_chain_to_trusted_root",
            "Certificate chain to a trusted TSA root is not checked here (no trust "
            "store shipped); verify the embedded certificate against your own trusted "
            "TSA roots, e.g. with `openssl ts -verify`.",
        )
    )

    result["verified"] = bool(imprint_ok and signature_ok)
    return result


def _check_imprint(
    tst: Any,
    expected: bytes,
    checks: list[dict[str, str]],
    result: dict[str, Any],
) -> bool:
    try:
        imprint = tst["message_imprint"]
        algo = imprint["hash_algorithm"]["algorithm"].native
        hashed = imprint["hashed_message"].native
    except Exception:
        checks.append(_fail("imprint_matches_digest", "Token has no readable message imprint."))
        return False
    if algo != _IMPRINT_ALGORITHM:
        checks.append(
            _fail(
                "imprint_matches_digest",
                f"Token imprint uses {algo!r}, not {_IMPRINT_ALGORITHM}; cannot match this digest.",
            )
        )
        return False
    if hashed == expected:
        checks.append(
            _pass(
                "imprint_matches_digest",
                "The token's message imprint equals the SHA-256 digest you hold.",
            )
        )
        return True
    checks.append(
        _fail(
            "imprint_matches_digest",
            "The token's message imprint does NOT match the digest you hold — the "
            "token attests a different value.",
        )
    )
    return False


def _check_signature(
    signed_data: Any,
    checks: list[dict[str, str]],
    result: dict[str, Any],
) -> bool:
    """Verify the message-digest binding and the TSA signature. Returns pass/fail.

    A ``skipped`` outcome (no embedded cert, or ``cryptography`` unavailable) returns
    False so the token is reported UNVERIFIED — fail-closed, never a false pass.
    """
    try:
        signer_infos = signed_data["signer_infos"]
        if len(signer_infos) < 1:
            checks.append(_fail("signature_valid", "Token carries no SignerInfo to verify."))
            return False
        signer_info = signer_infos[0]
        econtent = signed_data["encap_content_info"]["content"]
        econtent_bytes = econtent.parsed.dump() if hasattr(econtent, "parsed") else bytes(econtent.native)
    except Exception:
        checks.append(_fail("signature_valid", "Token structure is missing fields required to verify."))
        return False

    # (c) signed message-digest attribute must equal the digest of the eContent,
    # which is what actually binds the signature to this TSTInfo.
    try:
        signed_attrs = signer_info["signed_attrs"]
        if signed_attrs.native is None:
            checks.append(
                _skip(
                    "signature_valid",
                    "Token has no signed attributes; offline signature verification is "
                    "not supported for this token shape.",
                )
            )
            return False
        digest_algo = signer_info["digest_algorithm"]["algorithm"].native
        content_digest = _hash_bytes(digest_algo, econtent_bytes)
        if content_digest is None:
            checks.append(_skip("signature_valid", f"Unsupported digest algorithm {digest_algo!r}."))
            return False
        md_attr = None
        for attr in signed_attrs:
            if attr["type"].native == "message_digest":
                md_attr = attr["values"][0].native
                break
        if md_attr != content_digest:
            checks.append(
                _fail(
                    "message_digest_attr_matches_content",
                    "Signed message-digest attribute does not match the token content.",
                )
            )
            return False
        checks.append(
            _pass(
                "message_digest_attr_matches_content",
                "Signed message-digest attribute matches the token's TSTInfo content.",
            )
        )
        signed_attrs_der = signed_attrs.untag().dump()
    except Exception:
        checks.append(_fail("signature_valid", "Could not evaluate the signed message-digest attribute."))
        return False

    # (d) verify the signature over the signed attributes against the embedded cert.
    signer_cert_der = _embedded_signer_cert(signed_data, signer_info)
    if signer_cert_der is None:
        checks.append(
            _skip(
                "signature_valid",
                "No signing certificate is embedded in the token (request cert_req=true); "
                "the TSA signature cannot be verified offline. Reported as unverified.",
            )
        )
        return False

    try:
        from cryptography import x509
    except Exception:
        checks.append(
            _skip(
                "signature_valid",
                "The 'cryptography' package is unavailable; the TSA signature cannot be "
                "verified offline. Reported as unverified.",
            )
        )
        return False

    try:
        cert = x509.load_der_x509_certificate(signer_cert_der)
        result["tsa_name"] = _cert_common_name(cert)
        sig = signer_info["signature"].native
        sig_algo = _safe_signature_algo(signer_info["signature_algorithm"])
        # The signature hash for a CMS SignerInfo is the SignerInfo.digestAlgorithm
        # when the signatureAlgorithm OID does not itself pin one (the common
        # rsaEncryption / rsassa_pkcs1v15 case, where asn1crypto's .hash_algo
        # RAISES rather than returning None). Resolve it robustly for real tokens.
        hash_algo = _safe_hash_algo(signer_info["signature_algorithm"]) or signer_info["digest_algorithm"]["algorithm"].native
        ok = _verify_signature(cert.public_key(), sig, signed_attrs_der, sig_algo, hash_algo)
    except Exception:
        checks.append(_fail("signature_valid", "TSA signature verification raised while evaluating the token."))
        return False

    if ok:
        checks.append(
            _pass(
                "signature_valid",
                "The TSA signature verifies against the certificate embedded in the token.",
            )
        )
        return True
    checks.append(
        _fail(
            "signature_valid",
            "The TSA signature does NOT verify against the embedded certificate — the "
            "token was altered or is not authentic.",
        )
    )
    return False


def _safe_signature_algo(signature_algorithm: Any) -> str:
    """SignerInfo signature algorithm family ('rsassa_pkcs1v15'|'rsassa_pss'|'ecdsa').

    asn1crypto raises for unknown OIDs; default to PKCS#1 v1.5 (by far the most
    common for RFC 3161 TSAs) so a token with an unusual algorithm OID is still
    attempted rather than silently unverifiable.
    """
    try:
        return signature_algorithm.signature_algo
    except Exception:
        return "rsassa_pkcs1v15"


def _safe_hash_algo(signature_algorithm: Any) -> str | None:
    """The hash pinned by the signature algorithm OID, or None if it pins none.

    asn1crypto RAISES (does not return None) when the OID — e.g. plain
    rsaEncryption / rsassa_pkcs1v15 — carries no hash; the caller then falls back
    to the SignerInfo.digestAlgorithm.
    """
    try:
        return signature_algorithm.hash_algo
    except Exception:
        return None


def _verify_signature(public_key: Any, signature: bytes, message: bytes, sig_algo: str, hash_algo: str) -> bool:
    """Verify ``signature`` over ``message`` using the embedded cert's public key."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

    # SHA-2 only: a weak SignerInfo/signature digest (SHA-1, SHA-224) is refused so
    # a collision-weak hash can't be used to bind a forged token. Modern RFC 3161
    # TSAs sign with SHA-256+; anything else is reported unverified (fail-closed).
    hash_cls = {
        "sha256": hashes.SHA256,
        "sha384": hashes.SHA384,
        "sha512": hashes.SHA512,
    }.get(str(hash_algo).lower())
    if hash_cls is None:
        return False
    hash_obj = hash_cls()

    try:
        if isinstance(public_key, rsa.RSAPublicKey):
            if sig_algo == "rsassa_pss":
                public_key.verify(
                    signature,
                    message,
                    padding.PSS(mgf=padding.MGF1(hash_obj), salt_length=padding.PSS.DIGEST_LENGTH),
                    hash_obj,
                )
            else:
                public_key.verify(signature, message, padding.PKCS1v15(), hash_obj)
            return True
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(signature, message, ec.ECDSA(hash_obj))
            return True
    except Exception:
        return False
    return False


# ── storage: additive sidecar next to the head-anchor file ──────────────────────

def sidecar_path_for(head_anchor_path: Path) -> Path:
    """Path of the additive JSON sidecar, next to ``evidence_chain_head.json``."""
    return Path(head_anchor_path).with_name(SIDECAR_JSON_NAME)


def _tsr_path_for(head_anchor_path: Path) -> Path:
    return Path(head_anchor_path).with_name(SIDECAR_TSR_NAME)


def read_head_anchor_sidecar(head_anchor_path: Path) -> dict[str, Any] | None:
    """Return the stored sidecar dict, or ``None`` if absent/unreadable."""
    import json

    path = sidecar_path_for(head_anchor_path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_head_anchor_sidecar(head_anchor_path: Path, anchor: dict[str, Any]) -> None:
    """Persist the anchor sidecar atomically (JSON) plus the raw ``.tsr`` DER token.

    Best-effort: a write failure is logged and swallowed (the sidecar is an
    ADDITIVE signal, never a gate on evidence durability). Never mutates the
    head-anchor file or any evidence record.
    """
    import json

    json_path = sidecar_path_for(head_anchor_path)
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_replace(
            json_path,
            json.dumps(anchor, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8"),
        )
        # Also drop the raw DER token so standard tooling (openssl ts) can read it.
        token_b64 = str(anchor.get("token_b64") or "")
        if token_b64:
            _atomic_replace(_tsr_path_for(head_anchor_path), base64.b64decode(token_b64))
    except Exception as exc:
        logger.warning("rfc3161_anchor: failed to write anchor sidecar: %s", type(exc).__name__)


def _atomic_replace(path: Path, data: bytes) -> None:
    """Atomically write ``data`` to ``path`` via a UNIQUE temp file in the same dir.

    Unique temp names (``tempfile.mkstemp``) mean the two possible writers — the
    hourly cron (:func:`anchor_head_now`) and the capture-triggered background
    thread (:func:`spawn_head_anchor`) — never collide on a fixed ``.tmp`` name.
    """
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ── orchestration: anchor the current chain head (best-effort) ──────────────────

def maybe_anchor_head(head_record_hash: str, head_anchor_path: Path) -> dict[str, Any] | None:
    """Anchor ``head_record_hash`` to the TSA and persist the sidecar. Best-effort.

    Dormant-by-default: returns ``None`` immediately when the anchor is disabled.
    Idempotent: if the sidecar already anchors this exact head hash, returns it
    WITHOUT a network call. Any failure returns ``None`` (logged, never raised).
    """
    if not anchor_enabled():
        return None
    head = str(head_record_hash or "").strip().lower()
    if not head:
        return None

    existing = read_head_anchor_sidecar(head_anchor_path)
    if existing and str(existing.get("anchored_head_record_hash") or "").strip().lower() == head:
        return existing

    anchor = request_timestamp(head)
    if anchor is None:
        return None

    anchor = dict(anchor)
    anchor["anchored_head_record_hash"] = head
    write_head_anchor_sidecar(head_anchor_path, anchor)
    logger.info("rfc3161_anchor: anchored chain head %s… to %s", head[:12], anchor.get("tsa_url"))
    return anchor


def spawn_head_anchor(head_record_hash: str, head_anchor_path: Path) -> None:
    """Fire :func:`maybe_anchor_head` on a daemon thread, out of the capture path.

    Parameter order mirrors :func:`maybe_anchor_head` exactly so the two are
    interchangeable (e.g. a test can substitute the synchronous variant).

    Dormant-by-default: returns immediately (spawning nothing) when disabled. A
    single-in-flight guard ensures per-append head updates never spawn unbounded
    threads or hammer the TSA. Never blocks the caller; never raises.
    """
    if not anchor_enabled():
        return
    if not _INFLIGHT.acquire(blocking=False):
        # An anchor request is already running; skip — the next head update anchors
        # the newer head once this one finishes.
        return

    def _run() -> None:
        try:
            maybe_anchor_head(head_record_hash, head_anchor_path)
        except Exception:  # absolute backstop — a background thread must never crash
            pass
        finally:
            _INFLIGHT.release()

    try:
        thread = threading.Thread(target=_run, name="rfc3161-head-anchor", daemon=True)
        thread.start()
    except Exception:
        # Could not start the thread; release the guard so a later attempt can run.
        try:
            _INFLIGHT.release()
        except Exception:
            pass


def anchor_head_now(base_dir: Path | None = None) -> dict[str, Any] | None:
    """Synchronously anchor the CURRENT chain head. The periodic-cron entry point.

    Reads the live head from ``app.source_runs`` and anchors it best-effort. This is
    the intended production usage (call on a cadence — hourly cron / scheduler),
    fully out of band from source capture. Returns the anchor dict, or ``None`` when
    disabled / no head / on any failure.
    """
    if not anchor_enabled():
        return None
    try:
        from app import source_runs

        head_anchor_path = source_runs._chain_head_file()
        head_payload = source_runs.read_chain_head()
        if not head_payload:
            return None
        head_record_hash = str(head_payload.get("head_record_hash") or "").strip()
        if not head_record_hash:
            return None
        if base_dir is not None:
            # Allow callers/tests to relocate the sidecar next to a chosen head file.
            head_anchor_path = Path(base_dir) / "data" / "evidence_chain_head.json"
        return maybe_anchor_head(head_record_hash, head_anchor_path)
    except Exception:  # cron entry point — never propagate
        return None


# ── ASN.1 / time helpers ────────────────────────────────────────────────────────

def _tst_info_from_token(token_der: bytes) -> Any | None:
    from asn1crypto import cms

    content_info = cms.ContentInfo.load(token_der)
    if content_info["content_type"].native != "signed_data":
        return None
    return _tst_info_from_signed_data(content_info["content"])


def _tst_info_from_signed_data(signed_data: Any) -> Any | None:
    from asn1crypto import tsp

    eci = signed_data["encap_content_info"]
    if eci["content_type"].native != "tst_info":
        return None
    content = eci["content"]
    raw = content.parsed.dump() if hasattr(content, "parsed") else bytes(content.native)
    return tsp.TSTInfo.load(raw)


def _embedded_signer_cert(signed_data: Any, signer_info: Any) -> bytes | None:
    """Return the DER of the signing certificate embedded in the token, or None.

    Prefers an exact match on the SignerInfo's ``sid`` (issuer+serial or SKI); falls
    back to the sole embedded certificate when only one is present.
    """
    certs = signed_data["certificates"]
    if certs.native is None:
        return None
    parsed = []
    for choice in certs:
        cert = choice.chosen
        if cert.__class__.__name__ == "Certificate":
            parsed.append(cert)
    if not parsed:
        return None

    try:
        sid = signer_info["sid"]
        if sid.name == "issuer_and_serial_number":
            want_issuer = sid.chosen["issuer"]
            want_serial = sid.chosen["serial_number"].native
            for cert in parsed:
                if cert.serial_number == want_serial and cert.issuer == want_issuer:
                    return cert.dump()
        elif sid.name == "subject_key_identifier":
            want_ski = sid.chosen.native
            for cert in parsed:
                ski = cert.key_identifier
                if ski is not None and ski == want_ski:
                    return cert.dump()
    except Exception:
        pass

    # Exactly one embedded cert → unambiguously the signer. With multiple certs
    # (leaf + intermediates, common for real TSAs) and no sid match above, do NOT
    # guess an arbitrary cert — fail closed (None → signature reported unverified)
    # rather than verify a real signature against a possibly-wrong public key.
    return parsed[0].dump() if len(parsed) == 1 else None


def _cert_common_name(cert: Any) -> str | None:
    try:
        from cryptography.x509.oid import NameOID

        values = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        return values[0].value if values else None
    except Exception:
        return None


def _hash_bytes(algo: str, data: bytes) -> bytes | None:
    import hashlib

    name = str(algo).lower()
    # SHA-2 only (see _verify_signature): the message-digest binding must not rest
    # on a collision-weak hash either. Weak/unknown algorithms => None => unverified.
    if name not in {"sha256", "sha384", "sha512"}:
        return None
    try:
        return hashlib.new(name, data).digest()
    except Exception:
        return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ── check-envelope helpers ──────────────────────────────────────────────────────

def _pass(name: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": "pass", "detail": detail}


def _fail(name: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": "fail", "detail": detail}


def _skip(name: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": "skipped", "detail": detail}
