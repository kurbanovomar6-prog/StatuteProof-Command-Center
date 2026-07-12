"""Change-significance (review-priority) scoring — a MONITORING heuristic.

WHAT THIS IS (read the framing carefully — it is legally load-bearing).
----------------------------------------------------------------------
This module ranks *detected source changes* by how likely a human reviewer is
to want to look at them **first**. It exists to fight alert fatigue: when a
sweep surfaces many CHANGED runs, a compliance reviewer needs a way to triage
which excerpts to open before the others.

It is a transparent, rule-based **prioritization heuristic** and nothing more:

* It is NOT "materiality" in any legal or accounting sense.
* It does NOT decide whether a change matters *to your firm*, creates an
  obligation, or has any compliance/regulatory consequence.
* It is NOT advice, a legal opinion, or a determination of importance.
* It NEVER changes, gates, or discards the tamper-evident evidence record. A
  change banded "noise" is still fully recorded — the band only affects the
  ORDER a human reviews things in.

Every customer-facing string this module produces carries that framing plus the
short disclaimer, and is passed through ``app.legal_safety`` so a wording drift
can never ship a forbidden claim.

HOW IT SCORES (all signals are transparent, auditable surface cues).
--------------------------------------------------------------------
``score_change`` reads the SAME real diff artifact the rest of the pipeline
uses (``added_chunks`` / ``removed_chunks`` / ``changed_chunks`` from
``app.chunk_diff``) plus the run's ``change_status``. It computes a small set of
weighted signals, sums them, and clamps to 0..100. Each signal explains itself:
the magnitude of the normalized-text change, and the presence of high-signal
regulatory wording in the changed span (binding-obligation verbs, deadlines /
dates, monetary thresholds, penalties / enforcement, licensing / registration,
reporting duties). A genuinely new source (``FIRST_SEEN``) and an optional
source-tier hint also contribute.

Pure and deterministic: same input dict → same output. No I/O, no network, no
model — so it is fully unit-testable and its output is reproducible for audit.
"""

from __future__ import annotations

import re
from typing import Any

# Shared, tested primitives from the offline risk lane. Reusing them keeps ONE
# implementation of word-bounded matching (the fix that stopped 'ban' matching
# inside 'bank') and ONE character-level edit-magnitude counter, so the
# review-priority heuristic can never silently disagree with the risk lane on
# "what counts as a match" or "how big is this change".
from app.legal_safety import assert_no_forbidden_claims
from app.risk import _edited_char_count, _match_terms

# ── Customer-facing framing (legally load-bearing — see module docstring) ──────
SHORT_DISCLAIMER = (
    "For monitoring information only. Not legal advice and not a guarantee of "
    "compliance."
)
HEURISTIC_FRAMING = (
    "This is a monitoring prioritization heuristic to help a reviewer decide "
    "what to look at first. It is not a legal, compliance, or regulatory "
    "determination and not advice."
)
# The customer-visible name for the signal. We deliberately avoid presenting a
# bare "materiality score", which could read as a legal-sense claim.
SIGNAL_LABEL = "Review-priority signal (monitoring heuristic)"

# ── Bands ──────────────────────────────────────────────────────────────────────
BAND_HIGH = "high"
BAND_MEDIUM = "medium"
BAND_LOW = "low"
BAND_NOISE = "noise"

_BAND_HIGH_MIN = 65
_BAND_MEDIUM_MIN = 38
# There is no low threshold: any NON-noise score floors to ``low`` (see
# _band_for_score). ``noise`` is reachable only via explicit noise detection.

# When a change is detected as formatting / boilerplate / below the minimal
# magnitude threshold, we force the "noise" band and cap the score so it always
# sinks to the bottom of a review queue — while the evidence record is untouched.
_NOISE_SCORE_CAP = 8
_TINY_MAGNITUDE_CHARS = 24

# Bound the text used for ALL scoring (magnitude, keyword matching, and noise
# detection) so a pathological pair of very large chunks cannot make scoring
# slow — score_change runs once per candidate inside the synchronous preview
# request. Beyond this size a change is already "very large" for triage.
_SCORING_TEXT_CAP = 8000

# ── Signal weights (max contribution of each signal to the 0..100 score) ───────
# WHY these groups: a compliance reviewer typically triages a change faster when
# the changed text touches a binding duty, a concrete deadline, a monetary
# threshold, a penalty, a licensing/registration condition, or a reporting duty.
# These are SURFACE CUES in the changed text — never a conclusion about the
# reader's obligations. Weights are ordered by how strongly, in monitoring
# practice, each cue predicts "a human will want to open this first".
# (legal review 2026-07-12: these comments are review-triage cues — why a reviewer
# opens the change first — never an effect on the reader. Do not lift into any
# customer-facing string.)
_W_OBLIGATION = 16          # binding-duty verbs: the strongest open-this-first cue
_W_DEADLINE = 16            # a dated/time-boxed change is time-sensitive to review
_W_PENALTY = 14             # penalty/enforcement wording: a high-attention review cue
_W_MONETARY = 12            # thresholds/fees/amounts: a strong review cue
_W_LICENSING = 10           # licensing/registration wording: a strong review cue
_W_REPORTING = 8            # reporting/filing wording: a common review cue
_W_FIRST_SEEN = 8           # a newly-monitored source has no prior baseline to compare
_W_SOURCE_TIER = {1: 10, 2: 6, 3: 3}  # optional: higher-tier official source hint

# ── Curated keyword groups (auditable — each term is a deliberate choice) ──────
# English terms are matched WORD-BOUNDED (via app.risk._match_terms) on lowered
# changed text. Arabic terms are matched on arabic-normalized changed text. The
# Arabic sets mirror the measured terms in app.risk (SIGNAL_QUALITY.md) so the
# two lanes stay consistent.

# Binding-obligation verbs: the presence of "must / shall / required / prohibited"
# in a CHANGE is the single strongest cue that a duty was introduced or altered.
_OBLIGATION_EN = (
    "must", "shall", "required", "require", "mandatory", "obliged", "obligation",
    "prohibited", "prohibition", "must not", "shall not", "may not",
)
_OBLIGATION_AR = ("يجب", "يتعين", "يلتزم", "ملزم", "الزامي", "محظور")

# Deadlines / dated effectivity: a change that carries a date or a deadline word
# is time-sensitive — a reviewer wants it before undated prose.
_DEADLINE_EN = (
    "deadline", "effective date", "effective from", "no later than",
    "reporting date", "submission date", "come into force", "comes into force",
    "in force", "transition period", "grace period", "with effect from",
)
_DEADLINE_AR = ("نافذ", "الموعد النهائي", "تاريخ السريان", "حيز التنفيذ")
# Concrete calendar-date forms (kept compact; the risk lane owns the exhaustive
# radar regex — this only needs presence detection, not extraction).
_MONTHS = (
    "january|february|march|april|may|june|july|august|"
    "september|october|november|december"
)
_DATE_RE = re.compile(
    r"(?ix)\b("
    r"\d{1,2}\s+(?:" + _MONTHS + r")\s+\d{4}"      # 1 September 2026
    r"|(?:end\s+of\s+)?(?:" + _MONTHS + r")\s+\d{4}"  # (end of) September 2026
    r"|\d{4}-\d{2}-\d{2}"                            # 2026-09-01
    r"|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"               # 01/09/2026
    r"|within\s+\d+\s+days"                          # within 30 days
    r")\b"
)

# Penalty / enforcement wording: direct downside signals a reviewer prioritizes.
_PENALTY_EN = (
    "penalty", "penalties", "fine", "fines", "sanction", "sanctions",
    "enforcement", "revoke", "revoked", "revocation", "suspend", "suspended",
    "suspension", "cease", "administrative fine",
)
_PENALTY_AR = ("عقوبة", "عقوبات", "غرامة", "جزاء", "جزاءات")

# Monetary thresholds / amounts: a change touching a number/fee/threshold often
# has an operational trigger. Detected by both curated terms and an amount regex.
_MONETARY_EN = (
    "threshold", "minimum capital", "capital requirement", "capital adequacy",
    "fee", "fees", "levy", "charge",
)
_MONETARY_AR = ("الحد الادنى", "متطلبات رأس المال", "رسوم", "رسم")
_MONEY_RE = re.compile(
    r"(?ix)("
    r"(?:aed|usd|eur|gbp|dhs?|dirhams?|\$|£|€)\s?[\d][\d,\.]*"  # AED 50,000 / $10k
    r"|[\d][\d,\.]*\s?(?:aed|usd|eur|gbp|dirhams?|per\s?cent|percent)\b"
    r"|\b\d+(?:\.\d+)?\s?%"                                       # 5% / 12.5 %
    r"|\b\d{1,3}(?:,\d{3})+\b"                                    # 50,000
    r")"
)

# Licensing / registration: conditions that gate the ability to operate.
_LICENSING_EN = (
    "license", "licence", "licensing", "licensed", "authorization",
    "authorisation", "authorised", "authorized", "registration", "registered",
    "permit", "approval",
)
_LICENSING_AR = ("ترخيص", "رخصة", "تسجيل", "اعتماد")

# Reporting / filing duties: change compliance workflows and calendars.
_REPORTING_EN = (
    "reporting", "report", "filing", "file a", "return", "returns", "disclosure",
    "disclose", "submit", "submission", "notification", "notify",
)
_REPORTING_AR = ("الابلاغ", "تقرير", "افصاح", "اخطار")


def _as_list(value: Any) -> list[str]:
    """Coerce a chunk field into a clean list[str]."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _extract_diff_text(change: dict) -> tuple[str, str, int]:
    """Return (added_side_text, removed_side_text, block_count) from a change.

    Accepts the shape every diff-carrying object in the pipeline already uses:
    ``added_chunks`` (insertions), ``removed_chunks`` (deletions), and
    ``changed_chunks`` (list of ``{"before": [...], "after": [...]}``). A nested
    ``diff`` dict and a bare ``diff_excerpt`` string are accepted as fallbacks so
    the scorer is robust to the routing-normalized alert shape too. Purely reads
    the dict — never touches disk.
    """
    diff = change.get("diff")
    source = diff if isinstance(diff, dict) else change

    added = _as_list(source.get("added_chunks"))
    removed = _as_list(source.get("removed_chunks"))
    changed_chunks = source.get("changed_chunks")
    if isinstance(changed_chunks, list):
        for item in changed_chunks:
            if isinstance(item, dict):
                added.extend(_as_list(item.get("after")))
                removed.extend(_as_list(item.get("before")))

    added_text = "\n".join(added)
    removed_text = "\n".join(removed)
    block_count = len(added) + len(removed)

    # Fallback: an object that only carried a bounded excerpt (no raw chunks).
    if not added_text and not removed_text:
        excerpt = str(change.get("diff_excerpt") or "").strip()
        if excerpt:
            added_text = excerpt
            block_count = 1

    return added_text, removed_text, block_count


def _magnitude_signal(edited_chars: int, block_count: int) -> dict:
    """Weighted magnitude signal from the real edit size + breadth.

    ``edited_chars`` is the number of characters that actually differ between the
    two sides (character-level diff, shared with the risk lane), so a same-length
    material swap is not masked by a near-zero length delta. Tiers are stepped
    (not linear) for a stable, explainable weight.
    """
    if edited_chars >= 2000:
        weight = 34
    elif edited_chars >= 1000:
        weight = 28
    elif edited_chars >= 400:
        weight = 20
    elif edited_chars >= 120:
        weight = 12
    elif edited_chars >= _TINY_MAGNITUDE_CHARS:
        weight = 6
    else:
        weight = 2
    detail = (
        f"about {edited_chars} characters of normalized text across "
        f"{block_count} block(s)"
    )
    return {"name": "change_magnitude", "detail": detail, "weight": weight}


def _keyword_group_matches(lowered: str, arabic: str) -> list[dict]:
    """Run each curated group; return a signal dict per group that matched.

    Only curated terms (never raw source text) surface in ``detail``, so the
    rationale stays legal-safe by construction.
    """
    groups: list[tuple[str, str, int, tuple[str, ...], tuple[str, ...]]] = [
        ("binding_obligation", "binding-obligation wording", _W_OBLIGATION, _OBLIGATION_EN, _OBLIGATION_AR),
        ("deadline_or_date", "a deadline or dated reference", _W_DEADLINE, _DEADLINE_EN, _DEADLINE_AR),
        ("penalty_or_enforcement", "penalty or enforcement wording", _W_PENALTY, _PENALTY_EN, _PENALTY_AR),
        ("monetary_threshold", "a monetary amount or threshold", _W_MONETARY, _MONETARY_EN, _MONETARY_AR),
        ("licensing_registration", "licensing or registration wording", _W_LICENSING, _LICENSING_EN, _LICENSING_AR),
        ("reporting_obligation", "reporting or filing wording", _W_REPORTING, _REPORTING_EN, _REPORTING_AR),
    ]
    signals: list[dict] = []
    for name, label, weight, en_terms, ar_terms in groups:
        matched = _match_terms(en_terms, lowered)
        matched += [term for term in ar_terms if term in arabic]
        # Regex-backed presence for the two groups that also have non-word forms.
        if name == "deadline_or_date" and _DATE_RE.search(lowered):
            matched.append("<date>")
        if name == "monetary_threshold" and _MONEY_RE.search(lowered):
            matched.append("<amount>")
        if matched:
            terms = ", ".join(sorted(dict.fromkeys(matched)))
            signals.append({
                "name": name,
                "detail": f"{label} ({terms})",
                "weight": weight,
            })
    return signals


def _source_tier_signal(change: dict) -> dict | None:
    """Optional weight from a source-tier hint, only if the change carries one."""
    raw = change.get("source_tier")
    if raw is None:
        raw = change.get("tier")
    if raw is None and isinstance(change.get("source"), dict):
        raw = change["source"].get("tier")
    try:
        tier = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    weight = _W_SOURCE_TIER.get(tier)
    if not weight:
        return None
    return {
        "name": "source_importance",
        "detail": f"higher-priority official source (tier {tier})",
        "weight": weight,
    }


_BOILERPLATE_RE = re.compile(
    r"""(?ix)
    last\s+(content\s+)?updated?(\s+on)?
    | last\s+modified
    | page\s+generated | generated\s+(on|at) | printed?\s+(on|at)
    | copyright | all\s+rights\s+reserved | ©
    | rate\s+this\s+page | rated\s+by | thanks\s+for\s+rating
    | total\s+visitors? | number\s+of\s+visitors? | visitor\s+count
    | session\s+id
    | terms\s+and\s+conditions | privacy\s+policy | cookies?
    | back\s+to\s+top | skip\s+to\s+content
    """
)
_DATE_STRIP_RE = re.compile(
    r"(?ix)\d{1,2}[:/\-\.]\d{1,2}(?:[:/\-\.]\d{2,4})?|\d{4}|\b(am|pm)\b|"
    + r"\d{1,2}\s+(?:" + _MONTHS + r")\s+\d{4}"
)
# For the boilerplate-substance check, keep ONLY alphabetic content (Latin +
# Arabic). Bare numbers/dates/punctuation are not substantive regulatory text on
# their own, so a "Total visitors: 12,344" counter reduces to empty and is
# correctly treated as boilerplate churn. Real content (which carries words)
# always survives, so a genuine change is never misclassified as boilerplate.
_LETTERS_ONLY_RE = re.compile(r"[^A-Za-z؀-ۿ]+")


def _strip_ws(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _noise_reason(
    added: str,
    removed: str,
    edited_chars: int,
    keyword_signals: list[dict],
    meaningful_flag: Any,
) -> str | None:
    """Return a plain noise reason string, or None if the change is not noise.

    Noise only affects PRIORITIZATION. The three noise classes are: an explicit
    below-threshold verdict from the diff layer, a whitespace/formatting-only
    edit, a boilerplate-only edit (footer / "last updated" churn), and a change
    below the minimal magnitude with no high-signal wording.
    """
    # The diff layer already judged this change below its significance threshold.
    if meaningful_flag is False:
        return (
            "the diff layer classified this change as below its significance "
            "threshold"
        )

    stripped_a, stripped_r = _strip_ws(added), _strip_ws(removed)
    if stripped_a and stripped_a == stripped_r:
        return "the change appears to be whitespace or formatting only"

    # Boilerplate-only: after removing footer/date-stamp churn and bare
    # dates/numbers, nothing of substance remains.
    combined = f"{added} {removed}"
    had_boilerplate_term = bool(_BOILERPLATE_RE.search(combined))
    residual = _BOILERPLATE_RE.sub(" ", combined)
    residual = _DATE_STRIP_RE.sub(" ", residual)
    residual = _LETTERS_ONLY_RE.sub(" ", residual).strip()
    if combined.strip() and not residual:
        if had_boilerplate_term:
            return (
                "the change appears to be boilerplate churn (for example a "
                "\"last updated\" timestamp, footer, or visitor counter)"
            )
        return (
            "the change contains no substantive wording (only numbers, dates, "
            "or symbols changed)"
        )

    if edited_chars < _TINY_MAGNITUDE_CHARS and not keyword_signals:
        return (
            "the change is below the minimal-magnitude threshold and no "
            "high-signal regulatory wording was detected"
        )
    return None


def _band_for_score(score: int) -> str:
    """Map a NON-noise score to a band. The floor is ``low`` by design.

    ``noise`` is NOT reachable from here — it is reserved for the explicit
    noise-detection path (whitespace / boilerplate / below-tiny-magnitude), so a
    small-but-genuine content change is honestly labelled ``low``, never ``noise``.
    """
    if score >= _BAND_HIGH_MIN:
        return BAND_HIGH
    if score >= _BAND_MEDIUM_MIN:
        return BAND_MEDIUM
    return BAND_LOW


def _join_clause(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _reasons_phrase(signals: list[dict]) -> str:
    """Compose a readable, curated-only reasons clause for the rationale.

    Magnitude, keyword groups, new-source, and source-tier each read naturally in
    their own clause. Only curated labels/ints reach this string.
    """
    touched: list[str] = []
    magnitude_clause = ""
    extra: list[str] = []
    for sig in signals:
        name = sig["name"]
        detail = str(sig["detail"])
        if name == "change_magnitude":
            magnitude_clause = detail
        elif name == "new_source_baseline":
            extra.append("it is the first captured baseline for a newly monitored source")
        elif name == "source_importance":
            extra.append(f"it comes from a {detail}")
        else:
            touched.append(detail)

    clauses: list[str] = []
    if touched:
        clauses.append("the changed text touched " + _join_clause(touched))
    if magnitude_clause:
        clauses.append("the edit changed " + magnitude_clause)
    clauses.extend(extra)
    return "; ".join(clauses) if clauses else "only a small, low-signal change was detected"


def _build_rationale(band: str, signals: list[dict], noise_reason: str | None) -> str:
    """Compose the self-explaining, legal-safe rationale string.

    Interpolates only curated labels and integers — never raw source text — so
    the forbidden-claims guard below can never be tripped by source content. The
    guard is still applied fail-closed to protect against future wording drift.
    """
    if noise_reason is not None:
        rationale = (
            f"Ranked noise (lowest review-priority): {noise_reason}. "
            "The underlying change is still recorded as a tamper-evident "
            "evidence record and is not discarded — only its review order is "
            f"affected. {HEURISTIC_FRAMING} {SHORT_DISCLAIMER}"
        )
    else:
        rationale = (
            f"Ranked {band} review-priority because {_reasons_phrase(signals)}. "
            f"{HEURISTIC_FRAMING} {SHORT_DISCLAIMER}"
        )
    # Fail-closed: a customer-facing byte must never assert a forbidden claim.
    assert_no_forbidden_claims(rationale, label="Materiality rationale")
    return rationale


def score_change(change: dict) -> dict:
    """Score a detected change for review-priority (a monitoring heuristic).

    Parameters
    ----------
    change:
        A diff-carrying dict — a source-run record, a diff artifact, or an alert
        draft. Read keys: ``added_chunks`` / ``removed_chunks`` /
        ``changed_chunks`` (the real diff), optional ``change_status``
        (``FIRST_SEEN`` vs ``CHANGED``), optional ``meaningful_change_detected``,
        and an optional ``source_tier`` / ``tier`` hint. Unknown/absent keys are
        tolerated.

    Returns
    -------
    dict
        ``{"score": int 0..100, "band": "high"|"medium"|"low"|"noise",
        "signals": [{"name", "detail", "weight"}], "rationale": str,
        "label": str, "framing": str, "disclaimer": str, "heuristic_only": True}``

    Pure and deterministic. The tamper-evident evidence record is never read,
    written, or affected — this only influences the ORDER a human reviews things.
    """
    if not isinstance(change, dict):
        change = {}

    added, removed, block_count = _extract_diff_text(change)
    # Bound EVERY downstream analysis (magnitude, keyword matching, noise
    # detection) to the scoring cap — not just the char-level diff.
    added, removed = added[:_SCORING_TEXT_CAP], removed[:_SCORING_TEXT_CAP]
    edited_chars = _edited_char_count(removed, added)

    lowered = f"{added}\n{removed}".lower()
    arabic = _arabic_fold(f"{added}\n{removed}")
    keyword_signals = _keyword_group_matches(lowered, arabic)

    noise_reason = _noise_reason(
        added, removed, edited_chars, keyword_signals,
        change.get("meaningful_change_detected"),
    )

    if noise_reason is not None:
        # Noise: force the bottom band and cap the score. Keyword matches (which
        # came from boilerplate/formatting) are intentionally NOT surfaced — only
        # the honest magnitude signal is kept.
        magnitude = _magnitude_signal(edited_chars, block_count)
        score = min(magnitude["weight"], _NOISE_SCORE_CAP)
        return _result(BAND_NOISE, score, [magnitude], noise_reason)

    signals: list[dict] = [_magnitude_signal(edited_chars, block_count)]
    signals.extend(keyword_signals)

    if str(change.get("change_status") or "").upper() == "FIRST_SEEN":
        signals.append({
            "name": "new_source_baseline",
            "detail": "first captured baseline for a newly monitored source",
            "weight": _W_FIRST_SEEN,
        })

    tier_signal = _source_tier_signal(change)
    if tier_signal is not None:
        signals.append(tier_signal)

    score = min(sum(int(sig["weight"]) for sig in signals), 100)
    band = _band_for_score(score)
    return _result(band, score, signals, None)


def _arabic_fold(text: str) -> str:
    """Arabic-normalize for AR term matching; empty string when unavailable."""
    if not any("؀" <= ch <= "ۿ" for ch in text):
        return ""
    try:
        from app.arabic_text import normalize_arabic

        return normalize_arabic(text)
    except Exception:
        return text


def _result(band: str, score: int, signals: list[dict], noise_reason: str | None) -> dict:
    """Assemble the public result dict (with the legal-safe framing block)."""
    return {
        "score": int(score),
        "band": band,
        "signals": signals,
        "rationale": _build_rationale(band, signals, noise_reason),
        "label": SIGNAL_LABEL,
        "framing": HEURISTIC_FRAMING,
        "disclaimer": SHORT_DISCLAIMER,
        "heuristic_only": True,
    }
