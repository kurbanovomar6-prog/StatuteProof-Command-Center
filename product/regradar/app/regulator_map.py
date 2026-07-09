"""Deterministic source -> regulator resolver.

Maps an alert's ``source_id`` / ``source_name`` / URL host to a single
regulator code drawn from a fixed, testable allow-list. The resolver is
pure and side-effect free: identical input always yields the same code.

Signal precedence (most authoritative first):
    1. source_id prefix   (e.g. "AE-cbuae-rulebook" -> CBUAE)
    2. URL host           (e.g. "rulebook.centralbank.ae" -> CBUAE)
    3. source_name tokens (e.g. "DFSA AML Rulebook" -> DFSA)
Anything with no recognised signal resolves to OTHER (never silently
dropped — OTHER is an explicit bucket).

Allowed codes: CBUAE, DFSA, FSRA, VARA, SCA, FTA, DIFC, OTHER.

DIFC note: DIFC is a legal jurisdiction, not a prudential regulator, but
DIFC legal sources (difc.com, difc.ae) are monitored and a customer may
scope to them, so DIFC is an addressable code. DFSA (the DIFC financial
regulator) is kept distinct from DIFC (DIFC laws/regulations portal).
"""

from __future__ import annotations

from urllib.parse import urlparse

# The single source of truth for valid regulator codes.
REGULATOR_CODES: tuple[str, ...] = (
    "CBUAE",
    "DFSA",
    "FSRA",
    "VARA",
    "SCA",
    "FTA",
    "DIFC",
    "OTHER",
)

# source_id prefix -> code. Prefixes are matched case-insensitively.
_SOURCE_ID_PREFIXES: tuple[tuple[str, str], ...] = (
    ("ae-cbuae-", "CBUAE"),
    ("ae-dfsa-", "DFSA"),
    ("ae-adgm-", "FSRA"),
    ("ae-fsra-", "FSRA"),
    ("ae-vara-", "VARA"),
    ("ae-sca-", "SCA"),
    ("ae-cma-", "SCA"),
    ("ae-fta-", "FTA"),
    ("ae-mof-", "FTA"),
    ("ae-difc-", "DIFC"),
)

# Exact / suffix host matches -> code. Order matters: DIFC before generic
# fallbacks, and DFSA thomsonreuters host resolved explicitly.
_HOST_RULES: tuple[tuple[str, str], ...] = (
    ("rulebook.centralbank.ae", "CBUAE"),
    ("centralbank.ae", "CBUAE"),
    ("dfsaen.thomsonreuters.com", "DFSA"),
    ("dfsa.ae", "DFSA"),
    ("fsra.adgm.com", "FSRA"),
    ("adgm.com", "FSRA"),
    ("rulebooks.vara.ae", "VARA"),
    ("vara.ae", "VARA"),
    ("uaecma.gov.ae", "SCA"),
    ("tax.gov.ae", "FTA"),
    ("mof.gov.ae", "FTA"),
    ("difc.com", "DIFC"),
    ("difc.ae", "DIFC"),
)

# Substring tokens in source_name -> code (last resort). Ordered so more
# specific tokens win before broader ones.
_NAME_RULES: tuple[tuple[str, str], ...] = (
    ("cbuae", "CBUAE"),
    ("central bank of the uae", "CBUAE"),
    ("central bank of uae", "CBUAE"),
    ("dfsa", "DFSA"),
    ("fsra", "FSRA"),
    ("adgm", "FSRA"),
    ("vara", "VARA"),
    ("virtual assets regulatory", "VARA"),
    ("capital market authority", "SCA"),
    ("securities and commodities authority", "SCA"),
    ("federal tax authority", "FTA"),
    ("ministry of finance", "FTA"),
    ("difc", "DIFC"),
)


def _host(url: str | None) -> str:
    if not url:
        return ""
    text = str(url).strip()
    if not text:
        return ""
    parsed = urlparse(text)
    host = (parsed.netloc or parsed.path).lower().strip()
    return host.removeprefix("www.")


def _from_source_id(source_id: str | None) -> str | None:
    text = str(source_id or "").strip().lower()
    if not text:
        return None
    for prefix, code in _SOURCE_ID_PREFIXES:
        if text.startswith(prefix):
            return code
    return None


def _from_host(host: str) -> str | None:
    if not host:
        return None
    for needle, code in _HOST_RULES:
        if host == needle or host.endswith("." + needle):
            return code
    return None


def _from_name(source_name: str | None) -> str | None:
    text = str(source_name or "").strip().lower()
    if not text:
        return None
    for token, code in _NAME_RULES:
        if token in text:
            return code
    return None


def resolve_regulator(alert: dict) -> str:
    """Resolve an alert dict to one regulator code (never None).

    Falls back to ``OTHER`` when no signal matches, so callers can rely on
    a code always being present — there is no silent failure.
    """
    if not isinstance(alert, dict):
        return "OTHER"

    from_id = _from_source_id(alert.get("source_id"))
    if from_id:
        return from_id

    host = _host(alert.get("source_url") or alert.get("url"))
    from_host = _from_host(host)
    if from_host:
        return from_host

    from_name = _from_name(alert.get("source_name") or alert.get("source_id"))
    if from_name:
        return from_name

    return "OTHER"
