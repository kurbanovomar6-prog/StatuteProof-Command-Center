"""
source_intake.py — Universal Source Intake Layer

Extends source_tester.py with:
  - Nav-shell detection (catches DFSA-class hash collisions)
  - Per-source config application (wait_for_selector, content_selector)
  - Richer status vocabulary for dashboard display
  - Hash collision detection across enabled sources
  - Optional evidence write (write_evidence=True)

Public API
----------
run_source_intake(source, all_sources=None, write_evidence=False) → dict
is_nav_shell_only(text, threshold=0.65) → bool
classify_intake_status(result_dict) → str

Status constants are on SourceIntakeStatus.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from app.source_tester import validate_public_url
from app.text_normalization import normalize_for_change_hash
from app.source_quality import build_quality_score
from app.source_certification import build_preview_certification, EvidenceLevel

logger = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────────────────────────────

_SOURCES_PATH = Path(__file__).parent.parent / "sources.json"

# ── status vocabulary ─────────────────────────────────────────────────────────


class SourceIntakeStatus:
    CONFIRMED_ACCESSIBLE = "CONFIRMED_ACCESSIBLE"
    JS_RENDERING_NEEDED = "JS_RENDERING_NEEDED"
    PDF_EXTRACTION_NEEDED = "PDF_EXTRACTION_NEEDED"
    NAV_SHELL_ONLY = "NAV_SHELL_ONLY"
    QUALITY_DROP = "QUALITY_DROP"
    NEEDS_SELECTOR_REVIEW = "NEEDS_SELECTOR_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"


class SourceFailureCode:
    URL_STALE = "URL_STALE"
    SELECTOR_NOT_FOUND = "SELECTOR_NOT_FOUND"
    JS_REQUIRED = "JS_REQUIRED"
    PDF_ONLY_SOURCE = "PDF_ONLY_SOURCE"
    LISTING_ADAPTER_REQUIRED = "LISTING_ADAPTER_REQUIRED"
    TABLE_ADAPTER_REQUIRED = "TABLE_ADAPTER_REQUIRED"
    REGISTER_ADAPTER_REQUIRED = "REGISTER_ADAPTER_REQUIRED"
    RULEBOOK_ADAPTER_REQUIRED = "RULEBOOK_ADAPTER_REQUIRED"
    NAV_SHELL_ONLY = "NAV_SHELL_ONLY"
    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    LIKELY_WAF_403 = "LIKELY_WAF_403"
    HIGH_NOISE_RISK = "HIGH_NOISE_RISK"
    DUPLICATE_BOILERPLATE_HASH = "DUPLICATE_BOILERPLATE_HASH"
    SHALLOW_CONTENT = "SHALLOW_CONTENT"
    SOURCE_STRUCTURE_CHANGED = "SOURCE_STRUCTURE_CHANGED"
    MANUAL_CHECK_REQUIRED = "MANUAL_CHECK_REQUIRED"
    DISCOVERY_FOUND_BETTER_ENDPOINT = "DISCOVERY_FOUND_BETTER_ENDPOINT"
    SITEMAP_DISCOVERY_REQUIRED = "SITEMAP_DISCOVERY_REQUIRED"
    NETWORK_ENDPOINT_DISCOVERY_REQUIRED = "NETWORK_ENDPOINT_DISCOVERY_REQUIRED"


# Human-readable labels for dashboard display
STATUS_LABELS: dict[str, str] = {
    SourceIntakeStatus.CONFIRMED_ACCESSIBLE: "Readiness threshold met",
    SourceIntakeStatus.JS_RENDERING_NEEDED: "JS rendering needed",
    SourceIntakeStatus.PDF_EXTRACTION_NEEDED: "PDF extraction needed",
    SourceIntakeStatus.NAV_SHELL_ONLY: "Remediation needed",
    SourceIntakeStatus.QUALITY_DROP: "Quality check",
    SourceIntakeStatus.NEEDS_SELECTOR_REVIEW: "Selector review",
    SourceIntakeStatus.UNSUPPORTED: "Not supported",
    SourceIntakeStatus.BLOCKED: "Blocked",
}

STATUS_SEVERITY: dict[str, str] = {
    SourceIntakeStatus.CONFIRMED_ACCESSIBLE: "good",
    SourceIntakeStatus.JS_RENDERING_NEEDED: "warning",
    SourceIntakeStatus.PDF_EXTRACTION_NEEDED: "warning",
    SourceIntakeStatus.NAV_SHELL_ONLY: "critical",
    SourceIntakeStatus.QUALITY_DROP: "warning",
    SourceIntakeStatus.NEEDS_SELECTOR_REVIEW: "warning",
    SourceIntakeStatus.UNSUPPORTED: "error",
    SourceIntakeStatus.BLOCKED: "error",
}

# ── thresholds ────────────────────────────────────────────────────────────────

_GLOBAL_MIN_CHARS = 500
_NAV_SHELL_LINE_RATIO = 0.65   # ratio of short lines that triggers nav-shell flag
_NAV_SHELL_SHORT_WORDS = 8     # lines with < this many words count as "nav items"
_NAV_SHELL_MAX_CHARS = 10_000  # above this char count, skip nav-shell check

# ── nav-shell detection ───────────────────────────────────────────────────────


def is_nav_shell_only(text: str, threshold: float = _NAV_SHELL_LINE_RATIO) -> bool:
    """
    Detect whether extracted text is primarily navigation shell content.

    A nav-shell is characterized by many short lines (menu items, breadcrumbs,
    link labels) and few substantive sentences. DFSA's extracted content is a
    clear example: "About us Go Back Who we are The DFSA Governance..."

    Returns True only when:
    - Total chars is below _NAV_SHELL_MAX_CHARS (avoids false positives on big pages)
    - Short-line ratio exceeds threshold

    Short line = fewer than _NAV_SHELL_SHORT_WORDS words.
    """
    text = text.strip()
    if not text:
        return False
    if len(text) >= _NAV_SHELL_MAX_CHARS:
        return False

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False

    short = sum(1 for ln in lines if len(ln.split()) < _NAV_SHELL_SHORT_WORDS)
    ratio = short / len(lines)
    return ratio >= threshold


# ── hash helpers ─────────────────────────────────────────────────────────────


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def build_source_lab_contract(result: dict) -> dict:
    """
    Return customer-safe Source Lab gating fields.

    A passing no-save test can be saved for validation, but it cannot activate
    monitoring. Monitoring activation is reserved for completed baseline and
    certified evidence states.
    """
    status = str(result.get("status") or "")
    cert = result.get("certification") or {}
    cert_status = str(cert.get("certification_status") or result.get("certification_status") or "")
    result_evidence_level = str(result.get("evidence_level") or "")
    cert_evidence_level = str(cert.get("evidence_level") or "")
    evidence_level = result_evidence_level or cert_evidence_level or EvidenceLevel.PREVIEW_ONLY
    evidence_written = bool(result.get("evidence_written"))
    baseline_done = int(cert.get("baseline_runs_completed") or 0)
    baseline_required = int(cert.get("baseline_runs_required") or 2)

    if (
        cert_status == "MONITORING_CERTIFIED"
        and cert_evidence_level == EvidenceLevel.CERTIFIED_EVIDENCE
        and baseline_done >= baseline_required
    ):
        evidence_level = cert_evidence_level

    basic_save_condition = (
        status == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
        and not evidence_written
        and evidence_level == EvidenceLevel.PREVIEW_ONLY
    )
    strict_save_gate = bool(result.get("can_save_evidence", True))
    can_save_for_validation = basic_save_condition and strict_save_gate
    can_activate_monitoring = (
        cert_status == "MONITORING_CERTIFIED"
        and evidence_level == EvidenceLevel.CERTIFIED_EVIDENCE
        and baseline_done >= baseline_required
    )

    if can_activate_monitoring:
        activation_readiness = "MONITORING_READY"
    elif status in {
        SourceIntakeStatus.BLOCKED,
        SourceIntakeStatus.UNSUPPORTED,
        SourceIntakeStatus.NAV_SHELL_ONLY,
        SourceIntakeStatus.QUALITY_DROP,
        SourceIntakeStatus.JS_RENDERING_NEEDED,
        SourceIntakeStatus.PDF_EXTRACTION_NEEDED,
        SourceIntakeStatus.NEEDS_SELECTOR_REVIEW,
    }:
        activation_readiness = "NEEDS_REMEDIATION"
    elif cert_status in {"BASELINE_PENDING", "TEST_PASSED", "EVIDENCE_CONFIRMED"}:
        activation_readiness = "BASELINE_REQUIRED"
    else:
        activation_readiness = "NEEDS_REVIEW"

    return {
        "can_save_for_validation": can_save_for_validation,
        "can_save_evidence": can_save_for_validation,
        "can_activate_monitoring": can_activate_monitoring,
        "activation_readiness": activation_readiness,
        "evidence_level": evidence_level,
        "baseline_runs_completed": baseline_done,
        "baseline_runs_required": baseline_required,
    }


def classify_failure_code(result: dict) -> str:
    """Map Source Lab outcome to a machine-readable remediation code."""
    reason = str(result.get("failure_reason") or " ".join(result.get("errors") or [])).lower()
    status = str(result.get("status") or "")
    dom = result.get("dom_investigation") or {}
    recommended_adapter = str(dom.get("recommended_adapter_family") or dom.get("recommended_adapter_name") or "")
    if result.get("hash_collision"):
        return SourceFailureCode.DUPLICATE_BOILERPLATE_HASH
    if result.get("nav_shell_detected") or status == SourceIntakeStatus.NAV_SHELL_ONLY:
        return SourceFailureCode.NAV_SHELL_ONLY
    if "403" in reason or "forbidden" in reason:
        return SourceFailureCode.LIKELY_WAF_403
    if "404" in reason or "not found" in reason:
        return SourceFailureCode.URL_STALE
    if "selector" in reason and ("not found" in reason or "timeout" in reason or "timed out" in reason):
        return SourceFailureCode.SELECTOR_NOT_FOUND
    if status == SourceIntakeStatus.PDF_EXTRACTION_NEEDED:
        return SourceFailureCode.PDF_ONLY_SOURCE
    if recommended_adapter == "listing":
        return SourceFailureCode.LISTING_ADAPTER_REQUIRED
    if recommended_adapter == "table":
        return SourceFailureCode.TABLE_ADAPTER_REQUIRED
    if recommended_adapter == "register":
        return SourceFailureCode.REGISTER_ADAPTER_REQUIRED
    if recommended_adapter in {"dfsa_rulebook", "rulebook"}:
        return SourceFailureCode.RULEBOOK_ADAPTER_REQUIRED
    if "sitemap" in reason:
        return SourceFailureCode.SITEMAP_DISCOVERY_REQUIRED
    if "network" in reason or "xhr" in reason or "api" in reason:
        return SourceFailureCode.NETWORK_ENDPOINT_DISCOVERY_REQUIRED
    if status == SourceIntakeStatus.JS_RENDERING_NEEDED:
        return SourceFailureCode.JS_REQUIRED
    if status == SourceIntakeStatus.QUALITY_DROP:
        return SourceFailureCode.SOURCE_STRUCTURE_CHANGED
    if status == SourceIntakeStatus.BLOCKED:
        return SourceFailureCode.ACCESS_BLOCKED
    if int(result.get("chars_normalized") or 0) < 500:
        return SourceFailureCode.SHALLOW_CONTENT
    return SourceFailureCode.MANUAL_CHECK_REQUIRED


def _has_structured_adapter_content(result: dict) -> bool:
    """Return True when an explicit adapter produced item-level monitorable text."""
    adapter_metadata = result.get("adapter_metadata") or {}
    if not isinstance(adapter_metadata, dict):
        return False
    family = str(adapter_metadata.get("adapter_family") or result.get("adapter_family") or "")
    if adapter_metadata.get("failure_reason"):
        return False
    if family in {"static_html", "custom_element", "playwright_selector"}:
        metadata = adapter_metadata.get("metadata") or {}
        has_focus = bool(metadata.get("focus_keywords"))
        chars = int(result.get("chars_normalized") or 0)
        return bool(result.get("adapter_used")) and has_focus and chars >= 500
    structured_families = {
        "listing",
        "sca_listing",
        "table",
        "dfsa_rulebook",
        "dfsa_notice_listing",
        "document_listing",
        "pdf_listing",
        "cbuae_document_listing",
        "fiu_eocn_document_listing",
        "vara_pdf_listing",
        "register",
        "sitemap_feed",
        "public_json_api",
    }
    if family not in structured_families:
        return False
    item_count = int(adapter_metadata.get("item_count") or 0)
    chars = int(result.get("chars_normalized") or 0)
    document_families = {
        "document_listing",
        "pdf_listing",
        "cbuae_document_listing",
        "fiu_eocn_document_listing",
        "vara_pdf_listing",
    }
    if family in document_families:
        return bool(result.get("adapter_used")) and item_count >= 2 and chars >= 500
    return bool(result.get("adapter_used")) and item_count >= 3


def apply_quality_gate_fields(result: dict) -> None:
    """Add strict Source Lab gate fields without changing evidence semantics."""
    chars = int(result.get("chars_normalized") or 0)
    nav_shell = bool(result.get("nav_shell_detected"))
    duplicate_hash = bool(result.get("hash_collision"))
    quality_score = int(result.get("quality_score") or 0)
    adapter_metadata = result.get("adapter_metadata") or {}
    if isinstance(adapter_metadata, dict):
        adapter_noise = adapter_metadata.get("noise_risk") or adapter_metadata.get("metadata", {}).get("noise_risk")
        adapter_health = adapter_metadata.get("source_health_risk") or adapter_metadata.get("metadata", {}).get("source_health_risk")
    else:
        adapter_noise = None
        adapter_health = None
    noise_risk = str(adapter_noise or result.get("noise_risk") or ("high" if nav_shell else ("medium" if chars < 1000 else "low")))
    source_health_risk = str(adapter_health or result.get("source_health_risk") or ("high" if nav_shell or duplicate_hash else "medium"))

    meaningful = bool(chars >= 500 and not nav_shell and not duplicate_hash)
    shallow = bool(chars < 500)
    result["official_status"] = result.get("official_status") or "unverified_public_source"
    result["access_status"] = result.get("access_status") or ("blocked_or_restricted" if result.get("status") == SourceIntakeStatus.BLOCKED else "public_fetch_attempted")
    result["meaningful_content"] = meaningful
    result["shallow_content"] = shallow
    result["duplicate_hash"] = duplicate_hash
    result["noise_risk"] = noise_risk
    result["source_health_risk"] = source_health_risk
    result["failure_code"] = "" if result.get("status") == SourceIntakeStatus.CONFIRMED_ACCESSIBLE else classify_failure_code(result)
    result["can_save_evidence"] = bool(
        result.get("status") == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
        and result.get("evidence_level") == EvidenceLevel.PREVIEW_ONLY
        and not result.get("evidence_written")
        and meaningful
        and quality_score >= 60
        and noise_risk != "high"
        and source_health_risk != "high"
    )


def _check_hash_collision(
    text_hash: str,
    source_id: str,
    all_sources: list[dict],
) -> tuple[bool, str | None]:
    """
    Check whether `text_hash` matches the stored hash of any other enabled source.

    Returns (collision_found, colliding_source_id | None).
    Requires all_sources to have 'source_id' and 'content_hash' fields.
    """
    for s in all_sources:
        if not s.get("enabled"):
            continue
        if s.get("source_id") == source_id:
            continue
        if s.get("content_hash") == text_hash:
            return True, s["source_id"]
    return False, None


# ── main intake function ──────────────────────────────────────────────────────


def run_source_intake(
    source: dict,
    all_sources: list[dict] | None = None,
    write_evidence: bool = False,
) -> dict:
    """
    Run a full intake check on a source entry.

    Parameters
    ----------
    source : dict
        A sources.json entry. Required keys: 'url'. Optional: 'source_id',
        'expected_min_length', 'wait_for_selector', 'content_selector', 'fetch_method'.
    all_sources : list[dict] | None
        All enabled sources (for hash collision check). Pass the full sources.json list.
    write_evidence : bool
        If True, write raw/normalized snapshots and proof.json. Requires DB access.

    Returns
    -------
    dict with fields:
        source_id, url, status, chars_raw, chars_normalized, pdf_chars,
        nav_shell_detected, hash_collision, collision_source_id, quality,
        evidence_written, errors, notes
    """
    url = source.get("url", "")
    source_id = source.get("source_id", "")
    expected_min = source.get("expected_min_length", _GLOBAL_MIN_CHARS)
    wait_selector = source.get("wait_for_selector")
    content_selector = source.get("content_selector")
    fetch_method = source.get("fetch_method")
    adapter_family = source.get("adapter_family")
    adapter_name = source.get("adapter_name")
    adapter_config = source.get("adapter_config") if isinstance(source.get("adapter_config"), dict) else {}

    result: dict = {
        "source_id": source_id,
        "url": url,
        "status": SourceIntakeStatus.UNSUPPORTED,
        "chars_raw": 0,
        "chars_normalized": 0,
        "pdf_chars": 0,
        "nav_shell_detected": False,
        "hash_collision": False,
        "collision_source_id": None,
        "quality": "POOR",
        "content_hash": "",
        "normalized_hash": "",
        "extraction_method": "",
        "provider_used": "",
        "provider_candidates": [],
        "adapter_used": False,
        "adapter_family": "",
        "adapter_name": "",
        "adapter_version": "",
        "extraction_strategy": "",
        "adapter_metadata": {},
        "adapter_warnings": [],
        "dom_investigation": {},
        "normalized_preview": "",
        "legal_policy_status": "PUBLIC_SOURCE_ONLY",
        "quality_score": 0,
        "quality_breakdown": {},
        "official_status": "unverified_public_source",
        "access_status": "",
        "meaningful_content": False,
        "shallow_content": True,
        "duplicate_hash": False,
        "noise_risk": "unknown",
        "source_health_risk": "unknown",
        "failure_code": "",
        "can_save_evidence": False,
        "evidence_level": EvidenceLevel.PREVIEW_ONLY,
        "proof_path": None,
        "evidence_paths": {},
        "certification_status": "",
        "certification": {},
        "failure_reason": "",
        "remediation_hint": "",
        "evidence_written": False,
        "errors": [],
        "notes": "",
    }

    # ── 1. URL safety ─────────────────────────────────────────────────────────
    safe, reason = validate_public_url(url)
    if not safe:
        result["status"] = SourceIntakeStatus.BLOCKED
        result["failure_reason"] = reason
        result["remediation_hint"] = "Use a public http(s) URL without credentials, login, private network, or restricted portal access."
        result["errors"].append(f"URL blocked: {reason}")
        quality_report = build_quality_score(
            url="",
            fetch_success=False,
            normalized_text="",
            raw_html="",
            normalized_hash=None,
            canonical_url=None,
        )
        result["quality_score"] = quality_report["quality_score"]
        result["quality_breakdown"] = quality_report
        result["certification"] = build_preview_certification(
            source_id=source_id,
            source_url=url,
            canonical_url=url,
            intake_result=result,
            quality_report=quality_report,
            baseline_runs_required=int(source.get("baseline_runs_required") or 2),
        )
        result["certification_status"] = result["certification"].get("certification_status", "")
        apply_quality_gate_fields(result)
        result.update(build_source_lab_contract(result))
        return result

    # ── 2. Fetch ──────────────────────────────────────────────────────────────
    try:
        from app.scraper import fetch_page_with_config
        html = fetch_page_with_config(
            url,
            wait_for_selector=wait_selector,
            content_selector=content_selector,
            force_playwright=(fetch_method == "playwright"),
        )
    except Exception as exc:
        if wait_selector or content_selector or fetch_method == "playwright":
            result["status"] = SourceIntakeStatus.NEEDS_SELECTOR_REVIEW
            result["remediation_hint"] = "Review the configured wait_for_selector/content_selector before activation."
        else:
            result["status"] = SourceIntakeStatus.BLOCKED
            result["remediation_hint"] = "Confirm the source is public and technically accessible."
        result["failure_reason"] = f"Fetch failed: {exc}"
        result["errors"].append(f"Fetch failed: {exc}")
        quality_report = build_quality_score(
            url=url,
            fetch_success=False,
            normalized_text="",
            raw_html="",
            normalized_hash=None,
            canonical_url=url,
        )
        result["quality_score"] = quality_report["quality_score"]
        result["quality_breakdown"] = quality_report
        result["certification"] = build_preview_certification(
            source_id=source_id,
            source_url=url,
            canonical_url=url,
            intake_result=result,
            quality_report=quality_report,
            baseline_runs_required=int(source.get("baseline_runs_required") or 2),
        )
        result["certification_status"] = result["certification"].get("certification_status", "")
        apply_quality_gate_fields(result)
        result.update(build_source_lab_contract(result))
        return result

    result["chars_raw"] = len(html)
    try:
        from app.dom_investigator import investigate_html
        result["dom_investigation"] = investigate_html(html, url=url)
    except Exception as exc:
        result["dom_investigation"] = {
            "failure_reason": f"DOM investigation failed: {type(exc).__name__}",
            "remediation_hint": "Run manual browser/DOM review before activation.",
            "warnings": [str(exc)],
        }

    # ── 3. Extract text ───────────────────────────────────────────────────────
    extracted: dict = {}
    adapter_result = None
    try:
        if adapter_family or adapter_name:
            from app.adapters.adapter_platform import extract_with_adapter
            adapter_result = extract_with_adapter(
                html,
                url=url,
                adapter_family=str(adapter_family or ""),
                adapter_name=str(adapter_name or ""),
                adapter_config=adapter_config,
            )
            result["adapter_used"] = bool(adapter_result.text)
            result["adapter_family"] = adapter_result.adapter_family
            result["adapter_name"] = adapter_result.adapter_name
            result["adapter_version"] = adapter_result.adapter_version
            result["extraction_strategy"] = adapter_result.extraction_strategy
            result["adapter_metadata"] = adapter_result.as_metadata()
            result["adapter_warnings"] = adapter_result.warnings
            if adapter_result.warnings:
                result["errors"].extend(f"Adapter warning: {warning}" for warning in adapter_result.warnings)
            if adapter_result.failure_reason and not adapter_result.text:
                result["errors"].append(f"Adapter failed: {adapter_result.failure_reason}")

        if adapter_result and adapter_result.text:
            extracted = {
                "text": adapter_result.text,
                "method": adapter_result.extraction_strategy,
                "provider_used": adapter_result.adapter_name,
                "confidence": "explicit_adapter",
                "candidates": [adapter_result.as_metadata()],
            }
        else:
            from app.extractors import extract_best_text
            extracted = extract_best_text(html, url=url, content_selector=content_selector)
        if isinstance(extracted, tuple):
            text = str(extracted[0] or "")
            result["extraction_method"] = str(extracted[1] or "")
            result["provider_used"] = result["extraction_method"]
        elif isinstance(extracted, dict):
            text = str(extracted.get("text") or "")
            result["extraction_method"] = str(extracted.get("method") or extracted.get("source") or "")
            result["provider_used"] = str(extracted.get("provider_used") or result["extraction_method"])
            result["provider_candidates"] = extracted.get("candidates") or []
        else:
            text = str(extracted or "")
    except Exception as exc:
        result["errors"].append(f"Extraction failed: {exc}")
        text = ""

    if not result.get("extraction_strategy"):
        result["extraction_strategy"] = result.get("extraction_method") or ""

    normalized_text = normalize_for_change_hash(text)
    result["chars_normalized"] = len(normalized_text)
    result["normalized_preview"] = normalized_text[:500]

    # ── 4. Nav-shell detection ────────────────────────────────────────────────
    dom_nav_shell = (result.get("dom_investigation") or {}).get("nav_shell_risk") == "high"
    structured_adapter_content = _has_structured_adapter_content(result)
    result["structured_adapter_content"] = structured_adapter_content
    nav_shell = False if structured_adapter_content else (is_nav_shell_only(normalized_text) or bool(dom_nav_shell))
    result["nav_shell_detected"] = nav_shell

    # ── 5. Hash collision check ───────────────────────────────────────────────
    content_hash = _content_hash(normalized_text)
    result["content_hash"] = content_hash
    result["normalized_hash"] = _sha256_hash(normalized_text) if normalized_text else ""
    collision_id: str | None = None
    if all_sources and source_id:
        collision, collision_id = _check_hash_collision(content_hash, source_id, all_sources)
        result["hash_collision"] = collision
        result["collision_source_id"] = collision_id
    else:
        collision = False

    # ── 6. PDF chars (best-effort — reuse cached if available) ───────────────
    pdf_chars = source.get("pdf_chars", 0)
    result["pdf_chars"] = pdf_chars

    provider_confidence = ""
    if isinstance(extracted, dict):
        provider_confidence = str(extracted.get("confidence") or "")
    quality_report = build_quality_score(
        url=url,
        fetch_success=bool(html),
        normalized_text=normalized_text,
        raw_html=html,
        nav_shell=nav_shell,
        hash_collision=bool(result["hash_collision"]),
        selector_timeout=False,
        pdf_shallow=bool(pdf_chars and pdf_chars < 500),
        proof_path=None,
        normalized_hash=result["normalized_hash"],
        canonical_url=url,
        provider_confidence=provider_confidence,
        metadata={"canonical_url": url},
    )
    result["quality_score"] = quality_report["quality_score"]
    result["quality_breakdown"] = quality_report
    if quality_report.get("policy_warnings"):
        result["legal_policy_status"] = "POLICY_REVIEW_REQUIRED"

    # ── 7. Status verdict ─────────────────────────────────────────────────────
    chars = result["chars_normalized"]

    if quality_report.get("policy_warnings"):
        result["status"] = SourceIntakeStatus.BLOCKED
        result["failure_reason"] = "Source appears to require login, CAPTCHA, paywall access, or a private portal."
        result["remediation_hint"] = "Use only public pages that are permitted to be monitored without bypassing access controls."
    elif nav_shell or collision:
        result["status"] = SourceIntakeStatus.NAV_SHELL_ONLY
        result["failure_reason"] = "Extracted content is a navigation shell or collides with another source hash."
        result["remediation_hint"] = "Configure a precise content_selector or adapter before marking this source ready."
    elif chars == 0 or result["chars_raw"] < 200:
        result["status"] = SourceIntakeStatus.BLOCKED
        result["failure_reason"] = "No meaningful extractable content was found."
        result["remediation_hint"] = "Confirm the URL is public, accessible, and not a private portal or blocked page."
    elif chars < 100:
        result["status"] = SourceIntakeStatus.JS_RENDERING_NEEDED
        result["failure_reason"] = "Extracted text is too small for reliable monitoring."
        result["remediation_hint"] = "Use Playwright rendering and a stable content selector."
    elif chars < 500 and pdf_chars == 0:
        result["status"] = SourceIntakeStatus.JS_RENDERING_NEEDED
        result["failure_reason"] = "Extracted text is below the minimum reliable threshold."
        result["remediation_hint"] = "Use Playwright rendering and a stable content selector."
    elif chars < 500 and pdf_chars > 1000:
        result["status"] = SourceIntakeStatus.PDF_EXTRACTION_NEEDED
        result["failure_reason"] = "HTML text is thin but PDF text appears available."
        result["remediation_hint"] = "Add a PDF extraction path before activating monitoring."
    elif chars < expected_min:
        result["status"] = SourceIntakeStatus.QUALITY_DROP
        result["failure_reason"] = f"Normalized text length {chars} is below expected minimum {expected_min}."
        result["remediation_hint"] = "Review selector, rendering, or source structure before activation."
    elif chars < 1000 and not (wait_selector or content_selector) and not structured_adapter_content:
        result["status"] = SourceIntakeStatus.NEEDS_SELECTOR_REVIEW
        result["failure_reason"] = "Text is present but too thin without an explicit selector."
        result["remediation_hint"] = "Add wait_for_selector/content_selector and retest."
    else:
        result["status"] = SourceIntakeStatus.CONFIRMED_ACCESSIBLE

    apply_quality_gate_fields(result)

    # ── 8. Quality label ──────────────────────────────────────────────────────
    total = chars + pdf_chars
    if total >= 5_000 and result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE:
        result["quality"] = "GOOD"
    elif result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE:
        result["quality"] = "ACCEPTABLE"
    elif total >= 1_000:
        result["quality"] = "LIMITED"
    else:
        result["quality"] = "POOR"

    # ── 9. Notes ──────────────────────────────────────────────────────────────
    notes_parts = []
    if nav_shell:
        notes_parts.append("Nav-shell detected — extracted text is primarily short navigation items.")
    if collision:
        notes_parts.append(f"Hash collision with {collision_id} — both sources extract identical content.")
    if chars < expected_min and not nav_shell and not collision:
        notes_parts.append(f"Chars ({chars}) below expected minimum ({expected_min}).")
    if pdf_chars > 0:
        notes_parts.append(f"PDF content available: {pdf_chars:,} chars.")
    result["notes"] = " ".join(notes_parts)

    result["certification"] = build_preview_certification(
        source_id=source_id,
        source_url=url,
        canonical_url=url,
        intake_result=result,
        quality_report=quality_report,
        baseline_runs_required=int(source.get("baseline_runs_required") or 2),
    )
    result["certification_status"] = result["certification"].get("certification_status", "")
    apply_quality_gate_fields(result)
    result.update(build_source_lab_contract(result))

    # ── 10. Evidence write (optional) ────────────────────────────────────────
    if write_evidence and result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE:
        try:
            evidence = _write_intake_evidence(
                source=source,
                source_id=source_id,
                url=url,
                html=html,
                text=normalized_text,
                content_hash=content_hash,
                result=result,
                quality_report=quality_report,
            )
            result["evidence_written"] = True
            result["proof_path"] = evidence.get("proof_path")
            result["evidence_paths"] = evidence.get("evidence_paths", {})
            result["evidence_level"] = evidence.get("evidence_level", EvidenceLevel.BASIC_EVIDENCE)
            if evidence.get("certification"):
                result["certification"] = evidence["certification"]
                result["certification_status"] = result["certification"].get("certification_status", "")
        except Exception as exc:
            result["errors"].append(f"Evidence write failed: {exc}")
        finally:
            result.update(build_source_lab_contract(result))

    return result


def _write_intake_evidence(
    *,
    source: dict,
    source_id: str,
    url: str,
    html: str,
    text: str,
    content_hash: str,
    result: dict,
    quality_report: dict,
) -> dict:
    """Write raw/normalized snapshot for the intake result."""
    import datetime
    from app.source_runs import _write_snapshots, append_run, _rel, _read_runs
    from app.source_certification import build_certification_from_runs
    from app.text_normalization import stable_normalized_hash

    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = f"intake-{now.strftime('%Y%m%dT%H%M%SZ')}"
    jur = source_id.split("-")[0] if "-" in source_id else "XX"

    snapshots = _write_snapshots(
        timestamp_utc=timestamp_utc,
        market=jur,
        source_id=source_id,
        run_id=run_id,
        raw_text=html,
        normalized_text=text,
        pdf_text="",
        metadata={
            "source_id": source_id,
            "url": url,
            "run_id": run_id,
            "content_hash": content_hash,
            "normalized_hash": result.get("normalized_hash"),
            "provider_used": result.get("provider_used"),
            "quality_score": result.get("quality_score"),
            "intake_mode": True,
        },
    )
    snapshot_base = (Path(__file__).parent.parent / str(snapshots["snapshot_metadata_path"])).parent
    provider_report_path = snapshot_base / "provider_report.json"
    quality_report_path = snapshot_base / "quality_report.json"
    certification_report_path = snapshot_base / "certification_report.json"
    hash_chain_path = snapshot_base / "hash_chain.json"

    run_quality = result.get("quality") or "ACCEPTABLE"
    if run_quality == "ACCEPTABLE":
        run_quality = "MEDIUM"
    record = {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "market": jur,
        "jurisdiction": jur,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "category": source.get("category", ""),
        "official_url": url,
        "final_url": url,
        "access_status": "accessible",
        "fetch_method": source.get("fetch_method") or "source_lab",
        "extraction_quality": run_quality,
        "extracted_chars": result.get("chars_normalized") or 0,
        "raw_chars": result.get("chars_raw") or 0,
        "normalized_chars": result.get("chars_normalized") or 0,
        "raw_hash": hashlib.sha256((html or "").encode("utf-8", errors="replace")).hexdigest() if html else None,
        "normalized_hash": result.get("normalized_hash") or stable_normalized_hash(text) or None,
        "pdf_text_hash": None,
        "pdf_links_count": 0,
        "pdf_extracted_chars": result.get("pdf_chars") or 0,
        "content_hash": content_hash,
        **snapshots,
        "title": None,
        "publication_date": None,
        "limitations_notes": result.get("notes") or "",
        "error": None,
        "pipeline_version": "source-intake-1.0",
        "normalization_version": "1.0",
        "provider_report_path": _rel(provider_report_path),
        "quality_report_path": _rel(quality_report_path),
        "certification_report_path": _rel(certification_report_path),
        "hash_chain_path": _rel(hash_chain_path),
        "adapter_used": result.get("adapter_used"),
        "adapter_family": result.get("adapter_family"),
        "adapter_name": result.get("adapter_name"),
        "adapter_version": result.get("adapter_version"),
        "extraction_strategy": result.get("extraction_strategy"),
    }
    appended = append_run(record)
    source_history = []
    seen_run_ids = set()
    for existing in _read_runs():
        if existing.get("source_id") != source_id:
            continue
        run_key = existing.get("run_id") or existing.get("timestamp_utc") or existing.get("proof_block_path")
        if run_key in seen_run_ids:
            continue
        seen_run_ids.add(run_key)
        source_history.append(existing)
    if appended.get("run_id") not in seen_run_ids:
        source_history.append(appended)
    certification = build_certification_from_runs(
        source_id=source_id,
        source_url=url,
        runs=source_history,
        baseline_runs_required=int(source.get("baseline_runs_required") or 2),
        quality_score=int(result.get("quality_score") or 0),
    )
    provider_report_path.write_text(json.dumps({
        "provider_used": result.get("provider_used"),
        "extraction_method": result.get("extraction_method"),
        "adapter_used": result.get("adapter_used"),
        "adapter_family": result.get("adapter_family"),
        "adapter_name": result.get("adapter_name"),
        "adapter_version": result.get("adapter_version"),
        "extraction_strategy": result.get("extraction_strategy"),
        "adapter_metadata": result.get("adapter_metadata"),
        "normalized_length": result.get("chars_normalized"),
        "warnings": result.get("errors", []),
    }, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    quality_report_path.write_text(json.dumps(quality_report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    certification_report_path.write_text(json.dumps(certification, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    hash_chain_path.write_text(json.dumps({
        "run_id": run_id,
        "raw_hash": appended.get("raw_hash"),
        "normalized_hash": appended.get("normalized_hash"),
        "content_hash": appended.get("content_hash"),
        "previous_hash": None,
    }, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "proof_path": appended.get("proof_block_path"),
        "evidence_level": EvidenceLevel.FULL_EVIDENCE if appended.get("proof_block_path") else EvidenceLevel.BASIC_EVIDENCE,
        "evidence_paths": {
            **{k: v for k, v in appended.items() if k.endswith("_path")},
        },
        "certification": certification,
    }


# ── batch readiness summary ───────────────────────────────────────────────────


def load_sources_json() -> list[dict]:
    if not _SOURCES_PATH.exists():
        return []
    with open(_SOURCES_PATH, encoding="utf-8") as f:
        return json.load(f)


def readiness_summary(sources: list[dict] | None = None) -> dict:
    """
    Return a readiness summary for all enabled sources.

    Uses stored run data (source_runs.jsonl) rather than live fetch.
    Falls back to sources.json 'status' field if no run record exists.
    """
    if sources is None:
        sources = load_sources_json()

    enabled = [s for s in sources if s.get("enabled")]

    try:
        from app.source_runs import latest_runs, _read_runs
        runs = latest_runs()
        all_run_rows = _read_runs()
    except Exception:
        runs = {}
        all_run_rows = []

    breakdown = []
    ready = 0
    remediation = 0
    evidence_confirmed = 0
    monitoring_certified = 0
    baseline_pending = 0
    blocked = 0

    hash_to_source_ids: dict[str, list[str]] = {}
    for sid, run in runs.items():
        h = run.get("normalized_hash")
        if h:
            hash_to_source_ids.setdefault(str(h), []).append(str(sid))
    colliding_source_ids = {
        sid
        for source_ids in hash_to_source_ids.values()
        if len(set(source_ids)) > 1
        for sid in source_ids
    }

    for s in enabled:
        sid = s.get("source_id", "")
        run = runs.get(sid)
        failure_reason = ""
        remediation_hint = ""

        if run:
            chars = int(run.get("normalized_chars") or run.get("extracted_chars") or 0)
            last_run = run.get("timestamp_utc", "")[:10] if run.get("timestamp_utc") else ""
            change_status = str(run.get("change_status") or "")
            access_status = str(run.get("access_status") or "")
            quality = str(run.get("extraction_quality") or "")
            normalized_hash = run.get("normalized_hash")
            proof_path = run.get("proof_block_path")
            limitations = " ".join(str(x) for x in (run.get("limitations_notes") or []))
            expected_min = int(s.get("expected_min_length") or _GLOBAL_MIN_CHARS)

            bad_change = change_status in {"FAILED", "QUALITY_DROP", "SOURCE_STRUCTURE_CHANGED"}
            bad_access = access_status in {"failed", "blocked", "restricted"}
            bad_quality = quality not in {"GOOD", "MEDIUM", "ACCEPTABLE"}
            collision = sid in colliding_source_ids
            nav_shell = "nav" in limitations.lower() and "shell" in limitations.lower()

            if bad_change or bad_access:
                status = SourceIntakeStatus.BLOCKED
                failure_reason = f"Latest run status is not usable: change_status={change_status}, access_status={access_status}."
                remediation_hint = "Fix source access or extraction before marking this source ready."
                remediation += 1
            elif nav_shell or collision:
                status = SourceIntakeStatus.NAV_SHELL_ONLY
                failure_reason = "Latest run appears to be a nav shell or shares a normalized hash with another source."
                remediation_hint = "Add a precise selector/adapter and rerun evidence validation."
                remediation += 1
            elif bad_quality or chars < expected_min or not normalized_hash or not proof_path:
                status = SourceIntakeStatus.QUALITY_DROP
                failure_reason = "Latest run does not meet extraction quality, hash, length, or proof artifact requirements."
                remediation_hint = "Rerun source validation and confirm normalized hash plus proof artifact exist."
                remediation += 1
            else:
                status = SourceIntakeStatus.CONFIRMED_ACCESSIBLE
                ready += 1
        else:
            status = SourceIntakeStatus.UNSUPPORTED
            last_run = ""
            remediation += 1
            chars = 0
            failure_reason = "No stored source run record exists."
            remediation_hint = "Run a safe source validation with evidence recording before activation."

        from app.source_certification import build_certification_from_runs
        certification = build_certification_from_runs(
            source_id=sid,
            source_url=s.get("url", ""),
            runs=all_run_rows,
            baseline_runs_required=int(s.get("baseline_runs_required") or 2),
            quality_score=100 if status == SourceIntakeStatus.CONFIRMED_ACCESSIBLE else 40 if status == SourceIntakeStatus.QUALITY_DROP else 0,
        )
        cert_status = certification.get("certification_status")
        if certification.get("evidence_level") in {"BASIC_EVIDENCE", "FULL_EVIDENCE", "CERTIFIED_EVIDENCE"}:
            evidence_confirmed += 1
        if cert_status == "MONITORING_CERTIFIED":
            monitoring_certified += 1
        elif cert_status == "BASELINE_PENDING":
            baseline_pending += 1
        elif status in {SourceIntakeStatus.BLOCKED, SourceIntakeStatus.UNSUPPORTED}:
            blocked += 1

        breakdown.append({
            "source_id": sid,
            "name": s.get("name", ""),
            "status": status,
            "status_label": STATUS_LABELS.get(status, status),
            "severity": STATUS_SEVERITY.get(status, "error"),
            "chars": chars,
            "last_run": last_run,
            "failure_reason": failure_reason,
            "remediation_hint": remediation_hint,
            "certification_status": cert_status,
            "evidence_level": certification.get("evidence_level"),
            "baseline_runs_completed": certification.get("baseline_runs_completed"),
            "baseline_runs_required": certification.get("baseline_runs_required"),
        })

    return {
        "total_enabled": len(enabled),
        "confirmed_ready": ready,
        "evidence_confirmed": evidence_confirmed,
        "monitoring_certified": monitoring_certified,
        "baseline_pending": baseline_pending,
        "blocked": blocked,
        "remediation_needed": remediation,
        "breakdown": breakdown,
    }
