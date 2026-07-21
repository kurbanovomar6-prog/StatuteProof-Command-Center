"""Every customer-facing forbidden-claims guard must be the ONE canonical guard.

Historically ``evidence_pack``, ``coverage_certificate`` and ``weekly_brief``
each carried their own ``lower()`` + substring scan, so the whitespace-collapse,
homoglyph-folding and inflection matching in ``app.legal_safety`` protected
every OTHER delivery path but not the evidence pack, the Evidence Room (which
re-exports the pack guard), the coverage certificate or the brief legal gate.

This module pins parity: the same bypass corpus that ``legal_safety`` blocks
must be blocked by each of those guards, and the canonical guard must stay
linear-time (it sits in front of every customer-facing byte, so a quadratic
guard is an availability defect on the delivery it protects).
"""

import time

import pytest

from app import coverage_certificate, evidence_pack, weekly_brief
from app.legal_safety import find_forbidden_claims

# Wordings that a marketer or an adversarial source produces naturally and that
# the old literal-substring scans all let through.
BYPASS_CORPUS = {
    "inflected": "StatuteProof guarantees compliance for your firm.",
    "line-wrapped": "We guarantee\ncompliance.",
    "homoglyph": "We guarantεe compliance.",
    "inflected-prevent": "StatuteProof prevents fines.",
    # Markup between the phrase words — ordinary emphasis in AI-drafted prose.
    # Both rendered representations (markdown body_text AND the HTML body) are
    # what the fail-closed final-bytes gates actually scan.
    "markdown-bold": "StatuteProof will **guarantee** compliance for your firm.",
    "html-strong": "<p>StatuteProof will <strong>guarantee</strong> compliance.</p>",
    "html-inline": "We are an <b>AI</b> lawyer.",
    # One intervening determiner / adjective — the MORE natural phrasing.
    "gap-adjective": "StatuteProof guarantees full compliance with VARA rules.",
    "gap-possessive": "We guarantee your compliance.",
    "gap-of": "This is our guarantee of compliance.",
    "gap-percent": "We guarantee 100% compliance.",
    # Non-whitespace separators: hyphens, dashes, zero-width, acronym dots.
    "hyphen-compound": "StatuteProof is the AI-lawyer for UAE compliance teams.",
    "hyphen-never-miss": "You will never-miss a rulebook change.",
    "dash-unicode": "We guarantee‑compliance for every client.",
    "pdf-hyphenation": "StatuteProof will guarantee com-\npliance.",
    "zero-width": "We are an AI​lawyer.",
    "acronym-dots": "We are the A.I. lawyer for compliance teams.",
    "percent-spaced": "Our monitoring is 100 % accurate.",
    # Base forms the forward-only inflection engine could not reach.
    "singular-decision": "Every automated compliance decision is logged.",
    "singular-lawyer": "StatuteProof will replace your lawyer.",
    "certify-verb": "StatuteProof certifies your compliance.",
    # A first-party claim does not become quotable by wearing a modal or by
    # naming a regulated entity — the attribution exemption below must not open
    # a door for the copy StatuteProof itself writes.
    "modal-first-party": "StatuteProof must guarantee compliance for your firm.",
    "third-party-noun-first-party-subject": (
        "Our firm guarantees compliance for every licensee we monitor."
    ),
    "bullet-single-item": "- We guarantee compliance for your firm\n- Filed 30 June",
}

# ── MUST_ALLOW: text the guard withholding is WORSE than the bypass ───────────
# A blocked delivery is a WITHHELD delivery. StatuteProof's product is the
# regulator's own sentence, so a guard that holds a genuine DFSA/CBUAE line
# fails the customer silently and in exactly the place they are paying for.
# Sourced where possible from real strings: the product's own disclaimers
# (app.evidence_assessment.LEGAL_DISCLAIMER, CLAUDE.md short outreach line) and
# rulebook wording quoted verbatim in the 2026-07-21 guard review. The evidence
# store (evidence/**) was checked for rulebook prose to draw from — its
# snapshots are regulator LISTING pages (HTML/Arabic index text), so they carry
# no obligation sentences to quote here.
QUOTED_CORPUS = {
    # Third-party regulatory obligations — the core deliverable.
    "obligation-authorised-firm": (
        "An Authorised Firm must certify compliance with GEN 5.3.7 within 30 "
        "days of its financial year end."
    ),
    "obligation-senior-management": (
        "The DFSA requires senior management to certify compliance annually."
    ),
    "obligation-ensure": (
        "The firm shall ensure compliance with the AML rules by 30 June."
    ),
    "obligation-officer": "An officer must certify the compliance report.",
    "obligation-panel": "The panel may replace any lawyer acting for the licensee.",
    # Denials — the negation is not always the word before the phrase.
    "denial-there-is-no": (
        "StatuteProof provides monitoring; there is no guarantee of compliance."
    ),
    "denial-makes-no": "StatuteProof makes no guarantee of compliance.",
    "denial-not-any": "StatuteProof does not offer any guarantee of compliance.",
    "denial-do-not-provide": "We do not provide a guarantee of compliance.",
    "denial-nothing-is": "Nothing here is a guarantee of compliance.",
    "denial-nothing-verb": "Nothing in this brief guarantees compliance.",
    "denial-cannot-rely": "Firms cannot rely on this to guarantee compliance.",
    "denial-coordinated": "We cannot prevent fines or guarantee compliance.",
    "denial-coordinated-list": (
        "StatuteProof does not determine legal obligations, certify compliance, "
        "or replace counsel."
    ),
    # Bullet / spaced-dash artefacts: the live alert + digest format. Folding
    # must not weld two list items or two clauses into a claim.
    "bullet-across-items": "- guarantee\n- compliance",
    "bullet-alert-format": (
        "- The circular does not change the guarantee\n"
        "- Compliance filings move to 30 June"
    ),
    "spaced-em-dash": (
        "Nothing in this report is a guarantee — compliance remains your obligation."
    ),
    "spaced-em-dash-prevent": "Risk: prevent — fines may still apply.",
    "spaced-hyphen-lawyer": "We replace - lawyers stay in control.",
    # The product's own fixed wording.
    "product-short-disclaimer": (
        "For monitoring information only. Not legal advice and not a guarantee "
        "of compliance."
    ),
}

# Honest wording that must stay clean on every guard — the stricter folding and
# the widened phrase gap must not start holding legitimate denials.
HONEST_CORPUS = {
    "denial": "StatuteProof does not guarantee compliance.",
    "denial-gap": "StatuteProof does not guarantee full compliance.",
    "denial-of": "This is not a guarantee of compliance.",
    "denial-prevent": "We cannot prevent fines.",
    "denial-replace": "StatuteProof does not replace lawyers.",
    "source-excerpt": "Firms should seek independent legal advice.",
    "denial-certify": (
        "StatuteProof does not guarantee compliance, prevent fines, or certify "
        "that all regulatory updates have been captured."
    ),
}


@pytest.mark.parametrize("label", sorted(HONEST_CORPUS))
def test_canonical_guard_keeps_honest_wording_clean(label):
    assert find_forbidden_claims(HONEST_CORPUS[label]) == [], label


@pytest.mark.parametrize("label", sorted(QUOTED_CORPUS))
def test_canonical_guard_delivers_quoted_and_denied_wording(label):
    """Regulator obligations, denials and list formatting must not be withheld."""
    assert find_forbidden_claims(QUOTED_CORPUS[label]) == [], label


@pytest.mark.parametrize("label", sorted(QUOTED_CORPUS))
def test_change_register_guard_delivers_quoted_and_denied_wording(label):
    """The digest / deadline / register paths gate on the same corpus."""
    from app.change_register import assert_no_forbidden_claims as cr_guard

    cr_guard(QUOTED_CORPUS[label])


@pytest.mark.parametrize("label", sorted(QUOTED_CORPUS))
def test_evidence_pack_guard_delivers_quoted_and_denied_wording(label):
    evidence_pack.assert_no_forbidden_claims(QUOTED_CORPUS[label])


def test_full_legal_disclaimer_is_never_withheld():
    from app.evidence_assessment import LEGAL_DISCLAIMER

    assert find_forbidden_claims(LEGAL_DISCLAIMER) == []


@pytest.mark.parametrize("label", sorted(HONEST_CORPUS))
def test_evidence_pack_guard_keeps_honest_wording_clean(label):
    evidence_pack.assert_no_forbidden_claims(HONEST_CORPUS[label])


@pytest.mark.parametrize("label", sorted(BYPASS_CORPUS))
def test_canonical_guard_blocks_corpus(label):
    assert find_forbidden_claims(BYPASS_CORPUS[label]), label


@pytest.mark.parametrize("label", sorted(BYPASS_CORPUS))
def test_evidence_pack_guard_blocks_corpus(label):
    with pytest.raises(evidence_pack.EvidencePackError):
        evidence_pack.assert_no_forbidden_claims(BYPASS_CORPUS[label])


@pytest.mark.parametrize("label", sorted(BYPASS_CORPUS))
def test_coverage_certificate_guard_blocks_corpus(label):
    assert coverage_certificate.contains_forbidden_claim(BYPASS_CORPUS[label])


@pytest.mark.parametrize("label", sorted(BYPASS_CORPUS))
def test_brief_legal_gate_blocks_corpus(label):
    flags = weekly_brief.legal_scan_brief({"executive_summary": BYPASS_CORPUS[label]})
    assert flags, label


def test_brief_legal_gate_blocks_inflected_brief_extra_phrase():
    """BRIEF_EXTRA_PHRASES only exist to be matched here — inflections included."""
    flags = weekly_brief.legal_scan_brief(
        {"executive_summary": "This ensures you are compliant."}
    )
    assert flags


def test_evidence_pack_disclaimer_still_passes():
    evidence_pack.assert_no_forbidden_claims(evidence_pack.FULL_LEGAL_DISCLAIMER)


def test_coverage_certificate_disclaimer_still_clean():
    assert (
        coverage_certificate.contains_forbidden_claim(
            coverage_certificate._FULL_CERTIFICATE_DISCLAIMER
        )
        is None
    )


def test_rendered_email_html_cannot_hide_a_claim_behind_emphasis():
    """The email gate scans the RENDERED bytes — markup must not neutralize it."""
    from app.email_delivery import _brief_markdown_to_html

    markdown = "StatuteProof will **guarantee** compliance for your firm."
    rendered = _brief_markdown_to_html(markdown)
    assert "<strong>guarantee</strong>" in rendered
    assert find_forbidden_claims(markdown), "markdown source must be blocked"
    assert find_forbidden_claims(rendered), "rendered HTML must be blocked"


def test_canonical_guard_stays_linear_on_large_documents():
    """A denial-heavy 126KB delivery must not cost seconds of CPU.

    ``_is_denied`` used to re-scan the whole prefix for every denied match,
    making the guard O(n^2): the document below measured ~3.2s (and ~31s at
    350KB) — long enough to stall or time out the delivery the guard protects.
    """
    row = "StatuteProof does not guarantee compliance for this change. "
    document = row * 2200  # ~126KB
    assert len(document) > 120_000
    started = time.perf_counter()
    hits = find_forbidden_claims(document)
    elapsed = time.perf_counter() - started
    assert hits == []
    assert elapsed < 1.0, f"guard took {elapsed:.3f}s on {len(document)} chars"


def test_canonical_guard_stays_linear_on_markup_heavy_documents():
    """Unbalanced '<' must not make the markup fold quadratic.

    ``_HTML_TAG``'s ``[^>]*`` could cross other '<' characters, so a document
    with '<letter' and no later '>' — comparison notation in a diff excerpt,
    mojibake, truncated HTML — rescanned to end-of-document from every '<':
    100KB measured 2.2s and 400KB 86s inside the fail-closed guard, on the
    synchronous path of an audit-pack / register export.
    """
    document = "if x<y then the value is fine. " * 6400  # ~198KB
    assert len(document) > 190_000
    started = time.perf_counter()
    hits = find_forbidden_claims(document)
    elapsed = time.perf_counter() - started
    assert hits == []
    assert elapsed < 1.0, f"guard took {elapsed:.3f}s on {len(document)} chars"


def test_honest_denial_with_trailing_banned_conjunct_is_allowed():
    """A safe-disclaimer fragment carries the clause's negation; neutralising it
    must NOT strip that negation from a FURTHER banned phrase in a trailing
    conjunct of the SAME honest denial.

    Regression: _neutralize_disclaimers replaced the matched fragment with a
    bare space, so "...does not guarantee compliance, prevent fines, or replace
    lawyers." lost its "does not" and the trailing "replace lawyers" was wrongly
    blocked. The product's core job is delivering the regulator's words and its
    own honest denials; over-blocking one is worse than the bypass it closes.
    """
    honest_denials = [
        "This report does not guarantee compliance, prevent fines, or replace lawyers.",
        "StatuteProof does not guarantee compliance, prevent fines, or provide legal advice.",
        "It does not determine legal obligations, certify compliance, or replace counsel.",
        # The actual shipped standard disclaimer must keep passing.
        "StatuteProof does not guarantee compliance, prevent fines, or certify "
        "that all regulatory updates have been captured.",
    ]
    for sentence in honest_denials:
        assert find_forbidden_claims(sentence) == [], (
            f"honest denial wrongly blocked: {sentence!r}"
        )

    # The neutralisation token must not become a bypass: a first-party
    # affirmative claim adjacent to a safe fragment must STILL be blocked.
    assert find_forbidden_claims("StatuteProof guarantees compliance.")
    assert find_forbidden_claims("We replace your lawyers.")
    assert find_forbidden_claims("StatuteProof certifies your compliance.")
