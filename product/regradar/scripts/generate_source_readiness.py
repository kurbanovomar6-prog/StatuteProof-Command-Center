#!/usr/bin/env python3
"""Generate a manual StatuteProof Source Readiness Review HTML report."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "app" / "templates" / "source_readiness_report.html"
CANDIDATES_PATH = ROOT / "data" / "uae_source_candidates.json"
UNDER_VALIDATION_PATH = ROOT / "data" / "uae_under_validation_sources.json"
SOURCES_PATH = ROOT / "sources.json"

BUYER_PROFILES = {
    "vasp_crypto": {
        "label": "VASP / Crypto",
        "keys": {"vasp", "crypto_exchange", "crypto", "virtual_assets"},
        "summary": "This review maps official UAE source layers relevant to VASP / Crypto compliance teams.",
        "sample_title": "VARA — VASP Licensing Framework Update (SAMPLE)",
    },
    "payments_fintech": {
        "label": "Payments & Fintech",
        "keys": {"payments", "fintech", "payment_services"},
        "summary": "This review maps official UAE source layers relevant to payments, stored value and fintech compliance teams.",
        "sample_title": "CBUAE — Payment Services Circular Update (SAMPLE)",
    },
    "difc_dfsa": {
        "label": "DIFC / DFSA",
        "keys": {"difc_firm", "difc", "dfsa"},
        "summary": "This review maps official UAE source layers relevant to DIFC firms and DFSA-regulated compliance teams.",
        "sample_title": "DFSA — Rulebook Amendment Notice (SAMPLE)",
    },
    "adgm_fsra": {
        "label": "ADGM / FSRA",
        "keys": {"adgm_firm", "adgm", "fsra"},
        "summary": "This review maps official UAE source layers relevant to ADGM firms and FSRA-regulated compliance teams.",
        "sample_title": "FSRA — Regulatory Circular (SAMPLE)",
    },
    "aml_fiu": {
        "label": "AML / FIU",
        "keys": {"aml_compliance", "aml", "fiu", "mlro"},
        "summary": "This review maps official UAE source layers relevant to AML, MLRO, sanctions and financial crime teams.",
        "sample_title": "UAE FIU — AML/CFT Typologies Update (SAMPLE)",
    },
    "tax_corporate": {
        "label": "Tax / Corporate",
        "keys": {"tax", "corporate", "corporate_tax"},
        "summary": "This review maps official UAE source layers relevant to corporate, tax and finance teams.",
        "sample_title": "UAE Ministry of Finance — Tax Update (SAMPLE)",
    },
    "data_protection": {
        "label": "Data Protection",
        "keys": {"data_protection", "privacy", "dpo"},
        "summary": "This review maps official UAE source layers relevant to privacy, data protection and DPO teams.",
        "sample_title": "DIFC Data Protection — Guidance Update (SAMPLE)",
    },
}

STATUS_DETAILS = {
    "active": (
        "Confirmed for monitoring",
        "Change detection is available for this source after readiness review. Item-level indexing may still be under refinement.",
        "active",
    ),
    "remediation": (
        "Under extraction remediation",
        "Source is enabled but not confirmed for monitoring until extraction quality is fixed and rerun.",
        "validation",
    ),
    "under_validation": (
        "Under technical validation",
        "Official source located and reachable. Extraction quality, item-level structure and repeated-run stability are being validated.",
        "validation",
    ),
    "disabled_external_access": (
        "Access limited — monitoring deferred",
        "Current infrastructure cannot reliably access this source. Geo-IP, external access or server-side restrictions may apply.",
        "limited",
    ),
    "disabled_navigation_only": (
        "Navigation-only — monitoring deferred",
        "Source is reachable but returns navigation or shell content rather than publication-level content.",
        "limited",
    ),
    "limited": (
        "Monitoring limited",
        "Partial extractability exists, but source is not production-ready for full monitoring.",
        "validation",
    ),
    "needs_adapter": (
        "Needs extraction adapter",
        "A source-specific adapter is required before monitoring can be enabled.",
        "validation",
    ),
    "blocked": (
        "Blocked — not in current monitoring scope",
        "Access has failed across tested methods.",
        "limited",
    ),
    "mapped": (
        "Mapped — outside current scope",
        "Source is identified but not validated for this pilot.",
        "mapped",
    ),
    "under_review": (
        "Under review",
        "Technical readiness is still being reviewed by the operator.",
        "mapped",
    ),
}

ACTIVE_LABELS = {"Confirmed for monitoring"}
VALIDATION_LABELS = {
    "Under technical validation",
    "Needs extraction adapter",
    "Monitoring limited",
    "Under extraction remediation",
}
LIMITED_LABELS = {
    "Access limited — monitoring deferred",
    "Navigation-only — monitoring deferred",
    "Blocked — not in current monitoring scope",
    "Mapped — outside current scope",
    "Under review",
}


def _load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _text(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).strip() or fallback


def _html(value) -> str:
    return escape(_text(value), quote=True)


def _url_key(value: str | None) -> str:
    text = _text(value).lower().strip()
    if not text:
        return ""
    parsed = urlparse(text)
    netloc = parsed.netloc.removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{netloc}{path}" if netloc else text.rstrip("/")


def _name_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _text(value).lower()).strip()


def _profile_values(candidate: dict) -> set[str]:
    profiles = candidate.get("client_profiles")
    if isinstance(profiles, list):
        return {_text(item).lower() for item in profiles if _text(item)}
    if isinstance(profiles, str):
        return {_text(item).lower() for item in profiles.split(",") if _text(item)}
    return set()


def _broadly_relevant(candidate: dict) -> bool:
    haystack = " ".join(
        _text(candidate.get(key)).lower()
        for key in ("source_layer_name", "official_name", "source_name", "category", "why_it_matters")
    )
    return any(term in haystack for term in ("uae", "fiu", "aml", "tax", "vara", "dfsa", "difc", "adgm", "fsra", "cbuae"))


def _matches_profile(candidate: dict, buyer_profile: str) -> tuple[bool, str | None]:
    profile_keys = BUYER_PROFILES[buyer_profile]["keys"]
    candidate_profiles = _profile_values(candidate)
    if candidate_profiles:
        return bool(candidate_profiles.intersection(profile_keys)), None
    if _broadly_relevant(candidate):
        return True, "Profile mapping missing; included for operator review."
    return False, None


def _source_indexes(sources: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    by_url: dict[str, dict] = {}
    for source in sources:
        key = _url_key(source.get("url"))
        if key:
            by_url[key] = source
    return by_url, sources


def _find_source(candidate: dict, by_url: dict[str, dict], sources: list[dict]) -> dict | None:
    for key_name in ("official_url", "url"):
        key = _url_key(candidate.get(key_name))
        if key and key in by_url:
            return by_url[key]

    candidate_name = _name_key(
        candidate.get("source_layer_name")
        or candidate.get("official_name")
        or candidate.get("source_name")
        or candidate.get("name")
    )
    if not candidate_name:
        return None
    for source in sources:
        source_name = _name_key(source.get("name"))
        if source_name and (candidate_name in source_name or source_name in candidate_name):
            return source
    return None


def _under_validation_index(items: list[dict]) -> dict[str, dict]:
    index = {}
    for item in items:
        cid = _text(item.get("candidate_id"))
        if cid:
            index[cid] = item
    return index


def _derive_internal_status(candidate: dict, source: dict | None, under_validation: dict | None) -> str:
    proposed = _text(candidate.get("proposed_status") or candidate.get("status"), "mapped").lower()
    if proposed == "active_candidate":
        if source and bool(source.get("enabled")) and _text(source.get("status")).lower() == "active":
            return "active"
        return "under_validation"
    if proposed in STATUS_DETAILS:
        return proposed
    if under_validation and _text(under_validation.get("status")):
        return _text(under_validation.get("status")).lower()
    if source and _text(source.get("status")).lower() in STATUS_DETAILS:
        return _text(source.get("status")).lower()
    return "under_review"


def _status_details(internal_status: str) -> tuple[str, str, str]:
    return STATUS_DETAILS.get(internal_status, STATUS_DETAILS["under_review"])


def _extraction_method(candidate: dict, under_validation: dict | None) -> str:
    return (
        _text(candidate.get("extraction_method"))
        or _text(candidate.get("expected_extraction"))
        or _text(under_validation.get("extraction_expectation") if under_validation else "")
        or _text(candidate.get("likely_adapter_need"))
        or "Operator review required"
    )


def _limitation(candidate: dict, source: dict | None, under_validation: dict | None, extra_note: str | None) -> str:
    notes = [
        _text(candidate.get("limitation_notes")),
        _text(candidate.get("risk_notes")),
        _text(under_validation.get("limitation_notes") if under_validation else ""),
        _text(source.get("notes") if source else ""),
        _text(extra_note),
    ]
    joined = " ".join(note for note in notes if note)
    if not joined:
        return "Limitation not yet documented; operator review required."
    return joined


def _what_to_activate(item: dict) -> str:
    status = item["client_status"]
    if status == "Under technical validation":
        return "Required work: item-level mapping, repeated-run stability, PDF/document parsing where applicable, and proof/diff validation."
    if status == "Needs extraction adapter":
        return "Required work: source-specific adapter design, publication-level extraction, repeated-run stability, and proof/diff validation."
    if status == "Monitoring limited":
        return "Required work: expand partial extraction into reliable publication-level monitoring before pilot activation."
    if status in {"Access limited — monitoring deferred", "Blocked — not in current monitoring scope"}:
        return "Activation requires reliable access, an approved fallback source or mirror, and successful extraction validation."
    if status == "Navigation-only — monitoring deferred":
        return "Activation requires an adapter or endpoint that extracts publication-level content rather than navigation shell text."
    return "Activation requires operator review and written scope confirmation."


def _normalize_candidate(candidate: dict, source: dict | None, under_validation: dict | None, extra_note: str | None) -> dict:
    internal_status = _derive_internal_status(candidate, source, under_validation)
    label, explanation, tone = _status_details(internal_status)
    authority = (
        _text(candidate.get("authority"))
        or _text(candidate.get("official_name"))
        or _text(source.get("name") if source else "")
        or "Official source"
    )
    source_layer = (
        _text(candidate.get("source_layer_name"))
        or _text(candidate.get("source_name"))
        or _text(candidate.get("official_name"))
        or _text(candidate.get("name"))
        or "UAE source layer"
    )
    url = _text(candidate.get("official_url")) or _text(candidate.get("url")) or _text(source.get("url") if source else "")
    item = {
        "source_layer": source_layer,
        "authority": authority,
        "url": url,
        "client_status": label,
        "status_explanation": explanation,
        "tone": tone,
        "extraction_method": _extraction_method(candidate, under_validation),
        "why_it_matters": _text(candidate.get("why_it_matters"), "Client relevance requires operator review."),
        "limitation": _limitation(candidate, source, under_validation, extra_note),
        "next_action": _text(candidate.get("next_validation_action"))
        or _text(under_validation.get("next_validation_action") if under_validation else "")
        or "Operator review required before activation.",
        "internal_status": internal_status,
    }
    item["activation_note"] = _what_to_activate(item)
    return item


def _badge(item: dict) -> str:
    return f'<span class="badge status-{_html(item["tone"])}">{_html(item["client_status"])}</span>'


def _render_rows(items: list[dict]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td><strong>{_html(item['source_layer'])}</strong><br><a href=\"{_html(item['url'])}\">{_html(item['url'])}</a></td>"
            f"<td>{_html(item['authority'])}</td>"
            f"<td>{_badge(item)}<br><span class=\"muted\">{_html(item['status_explanation'])}</span></td>"
            f"<td>{_html(item['extraction_method'])}</td>"
            f"<td>{_html(item['why_it_matters'])}</td>"
            f"<td>{_html(item['limitation'])}</td>"
            "</tr>"
        )
    return "\n".join(rows) or '<tr><td colspan="6">No relevant source layers found for this profile.</td></tr>'


def _detail_card(item: dict, active: bool = False) -> str:
    caveat = (
        "Confirmed monitoring does not determine item-level detection of every publication."
        if active
        else item["activation_note"]
    )
    return (
        '<article class="detail">'
        f"<h3>{_html(item['source_layer'])}</h3>"
        f"<p>{_badge(item)}</p>"
        f"<p><strong>URL:</strong> <a href=\"{_html(item['url'])}\">{_html(item['url'])}</a></p>"
        f"<p><strong>{'What is monitored' if active else 'What remains'}:</strong> {_html(item['why_it_matters'])}</p>"
        f"<p><strong>Limitation:</strong> {_html(item['limitation'])}</p>"
        f"<p class=\"muted\">{_html(caveat)}</p>"
        "</article>"
    )


def _render_details(items: list[dict], empty: str, active: bool = False) -> str:
    if not items:
        return f'<p class="muted">{_html(empty)}</p>'
    return "\n".join(_detail_card(item, active=active) for item in items)


def _sample_brief(profile: dict) -> str:
    title = profile["sample_title"]
    official_source = "Official source URL selected during pilot setup"
    return "\n".join([
        f"<h3>{_html(title)}</h3>",
        "<h3>What Changed</h3>",
        "<p>This illustrative sample shows how a reviewed StatuteProof brief would describe a regulatory update format. It is not real data and does not represent a real regulatory change.</p>",
        "<h3>Who Is Affected</h3>",
        "<p>Illustrative affected teams may include compliance, legal, MLRO, licensing and operations stakeholders for this buyer profile. This is sample text only.</p>",
        "<h3>Why It Matters</h3>",
        "<p>This illustrative section explains the business relevance a human reviewer would validate before any client delivery. It is not a live assessment.</p>",
        "<h3>Suggested Action</h3>",
        "<p>Illustrative action: review the official source, assess internal policy impact, and consult qualified counsel before taking compliance action.</p>",
        "<h3>Source Proof</h3>",
        f"<p>{_html(official_source)}. A real brief includes official source proof and reviewed limitations.</p>",
        "<h3>Limitation Note</h3>",
        "<p>This sample is illustrative only. Real briefs include only human-reviewed changes from confirmed source layers.</p>",
        "<h3>Not Legal Advice</h3>",
        "<p>This sample brief does not constitute legal advice and should not be relied upon for compliance decisions.</p>",
    ])


def _render_recommended(active_items: list[dict]) -> str:
    if not active_items:
        return '<p class="muted">No confirmed source recommendation is made for this profile until readiness improves.</p>'
    return "\n".join(_detail_card(item, active=True) for item in active_items)


def _render_template(context: dict[str, str]) -> str:
    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, value in context.items():
        html = html.replace(f"{{{{ {key} }}}}", value)
    return html


def _build_report(args) -> tuple[str, dict]:
    candidates = _load_json(CANDIDATES_PATH, [])
    under_validation = _load_json(UNDER_VALIDATION_PATH, [])
    sources = _load_json(SOURCES_PATH, [])
    by_url, source_list = _source_indexes(sources if isinstance(sources, list) else [])
    under_by_id = _under_validation_index(under_validation if isinstance(under_validation, list) else [])

    selected = []
    for candidate in candidates if isinstance(candidates, list) else []:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("should_show_publicly_now") is not True:
            continue
        matches, extra_note = _matches_profile(candidate, args.buyer_profile)
        if not matches:
            continue
        source = _find_source(candidate, by_url, source_list)
        under = under_by_id.get(_text(candidate.get("candidate_id")))
        selected.append(_normalize_candidate(candidate, source, under, extra_note))

    selected.sort(key=lambda item: (item["tone"] != "active", item["source_layer"].lower()))
    active = [item for item in selected if item["client_status"] in ACTIVE_LABELS]
    validation = [item for item in selected if item["client_status"] in VALIDATION_LABELS]
    limited = [item for item in selected if item["client_status"] in LIMITED_LABELS]
    profile = BUYER_PROFILES[args.buyer_profile]
    total = len(selected)
    executive_summary = (
        f"For this profile, StatuteProof identified {total} relevant UAE source layers. "
        f"{len(active)} are confirmed for monitoring, {len(validation)} are under validation, need adapters, or are under extraction remediation, "
        f"and {len(limited)} have access limitations or are deferred. This is not a coverage guarantee."
    )
    context = {
        "company_name": _html(args.company_name),
        "contact_name": _html(args.contact_name),
        "buyer_profile_label": _html(profile["label"]),
        "report_date": _html(args.date),
        "profile_summary": _html(profile["summary"]),
        "active_count": str(len(active)),
        "validation_count": str(len(validation)),
        "limited_count": str(len(limited)),
        "total_count": str(total),
        "executive_summary": _html(executive_summary),
        "readiness_rows": _render_rows(selected),
        "active_details": _render_details(active, "No active sources are recommended for this profile yet.", active=True),
        "validation_details": _render_details(validation, "No under-validation source layers are included for this profile."),
        "limited_details": _render_details(limited, "No access-limited or deferred source layers are included for this profile."),
        "recommended_scope": _render_recommended(active),
        "sample_brief": _sample_brief(profile),
    }
    stats = {
        "total": total,
        "active": len(active),
        "validation": len(validation),
        "limited": len(limited),
    }
    return _render_template(context), stats


def _valid_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD format.") from exc
    return value


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a manual Source Readiness Review report.")
    parser.add_argument("--buyer-profile", required=True, choices=sorted(BUYER_PROFILES))
    parser.add_argument("--company-name", required=True)
    parser.add_argument("--contact-name", required=True)
    parser.add_argument("--date", required=True, type=_valid_date)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output) if args.output else Path("reports") / f"source_readiness_{args.buyer_profile}_{args.date}.html"
    if not output.is_absolute():
        output = ROOT / output
    html, stats = _build_report(args)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    print(f"Output: {output}")
    print(f"Sources reviewed: {stats['total']}")
    print(f"Confirmed for monitoring: {stats['active']}")
    print(f"Under validation / needs adapter: {stats['validation']}")
    print(f"Access-limited / deferred: {stats['limited']}")
    if stats["active"] == 0:
        print("Warning: no active sources recommended for this profile.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
