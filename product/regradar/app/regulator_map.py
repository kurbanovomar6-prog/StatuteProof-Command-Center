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

Allowed codes: CBUAE, DFSA, FSRA, VARA, SCA, FTA, DIFC, EOCN, MOEC, DLP,
MOJ, DFM, ICP, TDRA, MOCCAE, JAFZA, DMCC, OTHER.

DIFC note: DIFC is a legal jurisdiction, not a prudential regulator, but
DIFC legal sources (difc.com, difc.ae) are monitored and a customer may
scope to them, so DIFC is an addressable code. DFSA (the DIFC financial
regulator) is kept distinct from DIFC (DIFC laws/regulations portal).

Non-prudential authority codes (added so enabled monitored sources never
fall into the OTHER hard-exclusion bucket, which silently dropped ~23 of
116 enabled sources from scoped-customer delivery):
    EOCN   — Executive Office for Control & Non-Proliferation (UAE
             sanctions / targeted financial sanctions / TFS). The
             uaeiec.gov.ae portal is the same office and shares this code.
    MOEC   — UAE Ministry of Economy (AML/CFT, economic substance,
             competition, auditing). Sources live on moet.gov.ae / moe.gov.ae.
    DLP    — Dubai Legislation Portal (dlp.dubai.gov.ae).
    MOJ    — UAE Ministry of Justice (moj.gov.ae).
    DFM    — Dubai Financial Market (dfm.ae).
    ICP    — Federal Authority for Identity, Citizenship, Customs & Port
             Security (icp.gov.ae).
    TDRA   — Telecommunications & Digital Government Regulatory Authority.
    MOCCAE — Ministry of Climate Change & Environment.
    JAFZA  — Jebel Ali Free Zone Authority (jafza.ae).
    DMCC   — Dubai Multi Commodities Centre (dmcc.ae).
These are stable, addressable codes a customer may scope to; they are not
merged into any prudential regulator.
"""

from __future__ import annotations

from urllib.parse import urlparse

# The single source of truth for valid regulator codes. app.profile derives
# ALLOWED_REGULATOR_CODES from this tuple, so any code added here is
# automatically a scopable regulator for customers.
REGULATOR_CODES: tuple[str, ...] = (
    "CBUAE",
    "DFSA",
    "FSRA",
    "VARA",
    "SCA",
    "FTA",
    "DIFC",
    # Non-prudential UAE authorities and free zones (see module docstring).
    "EOCN",
    "MOEC",
    "DLP",
    "MOJ",
    "DFM",
    "ICP",
    "TDRA",
    "MOCCAE",
    "JAFZA",
    "DMCC",
    "OTHER",
)

# source_id prefix -> code. Prefixes are matched case-insensitively.
# Order matters: longer / more-specific prefixes must precede any shorter
# prefix they contain so the specific rule wins.
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
    # --- non-prudential UAE authorities and free zones (see docstring) ---
    # No prefix below is a string-prefix of another, so order among them is
    # not correctness-critical; grouped by entity for readability.
    # UAE Executive Office / sanctions portals (EOCN and the uaeiec.gov.ae
    # mirror are the same office).
    ("ae-eocn-", "EOCN"),
    ("ae-uaeiec-", "EOCN"),
    ("ae-uaeic-", "EOCN"),
    # Ministry of Economy. "ae-moet-" covers per-topic MOET sources;
    # "ae-uae-ministry-of-economy" covers the legacy top-level source_id;
    # "ae-moe-" covers the moe.gov.ae variant.
    ("ae-moet-", "MOEC"),
    ("ae-uae-ministry-of-economy", "MOEC"),
    ("ae-moe-", "MOEC"),
    ("ae-dlp-", "DLP"),
    ("ae-moj-", "MOJ"),
    ("ae-dfm-", "DFM"),
    ("ae-icp-", "ICP"),
    ("ae-tdra-", "TDRA"),
    ("ae-moccae-", "MOCCAE"),
    ("ae-jafza-", "JAFZA"),
    ("ae-dmcc-", "DMCC"),
)

# Exact / suffix host matches -> code. Order matters: more-specific hosts
# (e.g. rulebook.centralbank.ae) must precede the broader host they end with
# (centralbank.ae). A rule matches when host == needle or host ends with
# "." + needle, so no rule may be a dotted suffix of a later rule.
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
    # difccourts.ae is NOT a dotted suffix of difc.ae, so the DIFC Courts
    # sources resolve via the "difc" name token, not here.
    ("difc.com", "DIFC"),
    ("difc.ae", "DIFC"),
    # Non-prudential UAE authorities and free zones.
    ("eocn.gov.ae", "EOCN"),
    ("uaeiec.gov.ae", "EOCN"),
    # Sanctions-layer origins (2026-07-18 monitoring-census additions): the
    # customer-facing scope for the sanctions job is EOCN — the UAE TFS
    # regime keys on UN designations, and OFAC/UK screening is part of the
    # same obligation set. FATF-layer (MENAFATF) feeds the same scope. The
    # UAE FIU is the AML/CFT reporting authority — same scope family.
    ("scsanctions.un.org", "EOCN"),
    ("ofsistorage.blob.core.windows.net", "EOCN"),
    ("ofac.treasury.gov", "EOCN"),
    ("menafatf.org", "EOCN"),
    ("uaefiu.gov.ae", "EOCN"),
    # Basel Committee publications: prudential banking policy — CBUAE scope.
    ("bis.org", "CBUAE"),
    ("moet.gov.ae", "MOEC"),
    ("moe.gov.ae", "MOEC"),
    ("dlp.dubai.gov.ae", "DLP"),
    ("moj.gov.ae", "MOJ"),
    ("dfm.ae", "DFM"),
    ("icp.gov.ae", "ICP"),
    ("tdra.gov.ae", "TDRA"),
    ("moccae.gov.ae", "MOCCAE"),
    ("jafza.ae", "JAFZA"),
    ("dmcc.ae", "DMCC"),
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
    # Non-prudential authorities. "ministry of economy" is checked before the
    # shorter "eocn"/"executive office" tokens so a MOE source that mentions
    # the (formerly Executive Office) history still resolves to MOEC.
    ("ministry of economy", "MOEC"),
    ("eocn", "EOCN"),
    ("uaeiec", "EOCN"),
    ("executive office for control", "EOCN"),
    ("dubai legislation portal", "DLP"),
    ("ministry of justice", "MOJ"),
    # DFM sources are resolved by the dfm.ae host or an "ae-dfm-" source_id.
    # A bare "dfm" name token is deliberately NOT used because it substring-
    # matches unrelated names (e.g. "ARDFM Kazakhstan"). Only the unambiguous
    # full name is a name-level signal.
    ("dubai financial market", "DFM"),
    ("tdra", "TDRA"),
    ("moccae", "MOCCAE"),
    ("jafza", "JAFZA"),
    ("dmcc", "DMCC"),
    ("icp", "ICP"),
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
