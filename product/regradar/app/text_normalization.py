"""
Stable text normalization for source change detection.

The goal is not to create a perfect legal parser.  It is to remove common
website noise while preserving the regulatory text that a human would verify:
headings, publication titles, dates, circular wording, tables already rendered
as text, and document links.
"""

from __future__ import annotations

import hashlib
import html
import re

# Bump whenever normalize_for_change_hash output can differ for the same
# input. Recorded into run records so a version change explains a planned
# baseline reset instead of masquerading as a regulatory CHANGED event.
# v2: signal-max F1 — page-chrome stripping (nav runs, rating counters,
#     theme widgets, carousel positions, all-caps title taglines).
# v3: reliability audit — nav-label runs are stripped only at page EDGES now.
#     An INTERIOR run of short label-like lines is regulatory content (a
#     predicate-offence list, a roster of licensed/sanctioned entities, a
#     glossary), which the old any-position strip erased — making an add/remove
#     invisible to the change hash (a missed regulatory change). This re-shapes
#     the normalized hash for affected pages, so the version bump makes
#     classify_change rebaseline each source once on the first sweep, no alert.
NORMALIZATION_VERSION = 3

_SPACE_RE = re.compile(r"[ \t\r\f\v]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

_BOILERPLATE_EXACT = {
    "accept",
    "accept all",
    "accept cookies",
    "all rights reserved",
    "back to top",
    "close",
    "cookie settings",
    "copyright",
    "english",
    "home",
    "menu",
    "privacy policy",
    "read more",
    "search",
    "skip to content",
    "submit",
    "terms and conditions",
    "عربي",
}

_BOILERPLATE_PHRASES = (
    "enable javascript",
    "follow us on",
    "powered by curator.io",
    "share this page",
    "subscribe to our newsletter",
    "this site uses cookies",
    "we use cookies",
    "your browser does not support",
)

_VOLATILE_LINE_RE = re.compile(
    r"""
    ^\s*(
        generated\s+(at|on)|
        page\s+generated|
        print(ed)?\s+(at|on)|
        retrieved\s+(at|on)|
        session\s+id|
        current\s+(date|time)|
        local\s+time|
        server\s+time|
        last\s+run
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_VOLATILE_FRAGMENT_RE = re.compile(
    r"""
    (
        عدد\s+الزوار\s*:\s*[\d\s,]+|
        آخر\s+تحديث\s+للمحتوى\s+بتاريخ\s*:\s*
            \d{1,2}\s+[^\n]{1,30}?\s+\d{4}\s+
            \d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?|
        آخر\s+تحديث\s+للموقع\s*:?\s*
            (?:ال[ء-ي]+\s+)?\d{1,2}\s+[ء-ي]+\s+\d{4}
            (?:\s+\d{1,2}:\d{2}(?::\d{2})?\s*[صم]?)?|
        last\s+content\s+update\s*:\s*
            \d{1,2}\s+[A-Za-z]+\s+\d{4}\s+
            \d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ── signal-max F1: page-chrome fragments measured from the real trail ─────────
# Every pattern was observed causing a false CHANGED/HIGH in the 63-run
# judgment pass (docs/signal/judgment_table.md).

# Rating widgets: "Rate this page Rated by 1008 People Thanks for rating" and
# the CBUAE Arabic equivalent with a live user counter.
_CHROME_FRAGMENT_RE = re.compile(
    r"""
    (
        rate\s+this\s+page(\s+rated\s+by\s+[\d,]+\s+people)?(\s+thanks\s+for\s+rating)?|
        rated\s+by\s+[\d,]+\s+people(\s+thanks\s+for\s+rating)?|
        total\s+visitors\s*:?\s*[\d,]+|
        قيّ?م\s+هذه\s+الصفحة|
        قُ?يّ?مت\s+الصفحة\s+من\s+قبلِ?\s*[\d,]+\s*مستخدما?ً?|
        شكراً\s+على\s+التقيّ?م|
        theme\s+color(\s+\#[0-9A-Fa-f]{3,6})+|
        تغيير\s+اللون(\s+\#[0-9A-Fa-f]{3,6})+|
        (color\s+blind\s+mode|night\s+reading\s+mode)\s*(default\s+switch\s+checkbox\s+input)?|
        (إعدادات\s+عمى\s+الألوان|القراءة\s+الليلية)\s*(default\s+switch\s+checkbox\s+input)?|
        default\s+switch\s+checkbox\s+input
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Carousel/pagination position indicators rendered as bare "1/6" lines.
_CAROUSEL_LINE_RE = re.compile(r"^\s*\d{1,2}\s*/\s*\d{1,2}\s*$")

# Bare theme-color lines ("#1E8800") — found by the F6 activation probe on
# UAEFIU pages where hex codes render without the "Theme color" label.
_HEX_COLOR_LINE_RE = re.compile(r"^\s*(#[0-9A-Fa-f]{3,8}\s*)+$")

# Site taglines appended to <title>-derived lines as pipe-separated ALL-CAPS
# segments, e.g. "… | DFSA | THE INDEPENDENT REGULATOR OF FINANCIAL SERVICES".
_TAGLINE_SEGMENT_RE = re.compile(r"^[A-Z][A-Z&'’\-\s]{10,}$")

# Nav-menu label runs: >= _NAV_RUN_MIN consecutive short label lines with no
# sentence punctuation and no digits (e.g. "About us / Go Back / Who we are").
_NAV_RUN_MIN = 4
_NAV_PUNCT_RE = re.compile(r"[.:;!?،؟|/\\]|\d")
_NAV_MAX_LEN = 40

_TIME_ONLY_RE = re.compile(r"^\s*\d{1,2}:\d{2}(:\d{2})?\s*(am|pm)?\s*$", re.IGNORECASE)
_DATE_WORD_RE = re.compile(
    r"\b(published|publication|issued|effective|dated|date|circular|law|decree|resolution)\b",
    re.IGNORECASE,
)

_ARABIC_RE = re.compile(r"[؀-ۿ]")


def _is_arabic_line(line: str) -> bool:
    """Return True if more than 20% of the line's characters are Arabic-script."""
    if not line:
        return False
    arabic_chars = len(_ARABIC_RE.findall(line))
    return arabic_chars > 0.2 * len(line)


def _strip_tagline_segments(line: str) -> str:
    """Drop pipe-separated ALL-CAPS site-tagline segments from title lines.

    "\u2026 | DFSA | THE INDEPENDENT REGULATOR OF FINANCIAL SERVICES" toggling its
    suffix produced the 2026-07-05 false-HIGH pair; short acronym segments
    ("DFSA") are kept, long all-caps taglines are chrome.
    """
    if "|" not in line:
        return line
    kept = [
        seg.strip()
        for seg in line.split("|")
        if seg.strip() and not _TAGLINE_SEGMENT_RE.match(seg.strip())
    ]
    return " | ".join(kept)


def _clean_line(line: str) -> str:
    line = line.replace("\u00a0", " ")
    line = _VOLATILE_FRAGMENT_RE.sub("", line)
    line = _CHROME_FRAGMENT_RE.sub(" ", line)
    line = _strip_tagline_segments(line)
    line = _SPACE_RE.sub(" ", line).strip()
    return line


def _is_volatile_line(line: str) -> bool:
    """Remove timestamps that describe the page/render run, not publication dates."""
    if not line:
        return True
    if _CAROUSEL_LINE_RE.match(line):
        return True
    if _HEX_COLOR_LINE_RE.match(line):
        return True
    # Strip render-run stamps FIRST. _VOLATILE_LINE_RE is prefix-anchored to
    # render phrases ("generated at / current date / printed / retrieved /
    # session id / …") that do NOT overlap real publication lines like
    # "Published <date>". Checking it before the publication-date keep-guard
    # means a render stamp that happens to contain the word "date" is dropped
    # instead of kept — otherwise a page that prints its own render date flips
    # CHANGED every single cycle (fabricated daily noise).
    if _VOLATILE_LINE_RE.search(line):
        return True
    if _DATE_WORD_RE.search(line):
        return False
    if _TIME_ONLY_RE.match(line):
        return True
    return False


def _is_nav_label(line: str) -> bool:
    """Short menu-label line: no sentence punctuation, no digits, no doc words."""
    return (
        0 < len(line) <= _NAV_MAX_LEN
        and not _NAV_PUNCT_RE.search(line)
        and not _DATE_WORD_RE.search(line)
    )


def _strip_nav_label_runs(lines: list[str]) -> list[str]:
    """Drop only the LEADING and TRAILING runs of >= _NAV_RUN_MIN nav-label lines.

    Menu chrome sits at the page EDGES (header nav, footer links). An INTERIOR
    run of short label-like lines is far more likely to be regulatory content \u2014
    a predicate-offence list, a table of defined terms, a roster of licensed or
    sanctioned entities. The previous version dropped nav-label runs ANYWHERE on
    the page, which erased exactly that content and made adding/removing a list
    item invisible to the change hash: a MISSED regulatory change (the worst
    failure mode for an evidence product). Restricting the strip to the edges
    keeps interior lists while still removing edge nav (DFSA header+footer, the
    ~106-label case in docs/signal/SIGNAL_QUALITY.md \u00a7C). A leading/trailing run
    shorter than the threshold is kept (too short to be a menu).
    """
    n = len(lines)
    if n == 0:
        return lines

    start = 0
    while start < n and _is_nav_label(lines[start]):
        start += 1
    if start < _NAV_RUN_MIN:
        start = 0

    end = n
    while end > start and _is_nav_label(lines[end - 1]):
        end -= 1
    if n - end < _NAV_RUN_MIN:
        end = n

    return lines[start:end]


def _is_boilerplate_line(line: str) -> bool:
    lower = line.lower().strip(" .:-|")
    if line.startswith("حساب حكومة الإمارات"):
        return True
    if "الجريدة الرسمية المحلية حكومة أبوظبي حكومة دبي" in line:
        return True
    if lower in _BOILERPLATE_EXACT:
        return True
    # Drop very short chrome tokens (bullets, arrows, "•", ">") — but NEVER a
    # short token that carries regulatory signal: anything with a digit or a
    # currency/percent symbol (e.g. "5%", "8%", "1a", "AED"). Erasing those
    # collapsed a real change like "5%"->"8%" to the same normalized hash — a
    # missed regulatory change (false negative).
    if len(lower) <= 3 and not any(c.isdigit() for c in lower) and not re.search(r"[%$€£﷼]", lower):
        return True
    if len(lower) <= 24 and any(phrase in lower for phrase in _BOILERPLATE_PHRASES):
        return True
    return False


def normalize_for_change_hash(text: str) -> str:
    """
    Return a stable text representation for regulatory change hashing.

    Conservative cleanup only:
    - normalize whitespace
    - remove empty lines
    - remove obvious UI/cookie/navigation fragments
    - remove duplicate repeated lines
    - remove render-time timestamp lines when clearly not publication dates
    """
    if not text:
        return ""

    text = html.unescape(text)
    raw_lines = str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: list[str] = []
    seen: dict[str, int] = {}

    for raw in raw_lines:
        line = _clean_line(raw)
        if not line:
            continue
        if _is_volatile_line(line):
            continue

        key = line.casefold()
        seen_count = seen.get(key, 0)
        if _is_boilerplate_line(line):
            seen[key] = seen_count + 1
            continue
        if seen_count > 0:
            seen[key] = seen_count + 1
            continue
        if len(line) > 40 and any(line in previous for previous in lines[-5:]):
            seen[key] = 1
            continue

        seen[key] = 1
        lines.append(line)

    lines = _strip_nav_label_runs(lines)
    normalized = "\n".join(_merge_wrapped_lines(lines))
    normalized = _MULTI_NEWLINE_RE.sub("\n\n", normalized)
    return normalized.strip()


def _merge_wrapped_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        if not merged or not merged[-1]:
            merged.append(line)
            continue
        prev = merged[-1]
        if _is_arabic_line(prev) or _is_arabic_line(line):
            # For Arabic lines, only merge if the previous line ends with a
            # comma (Arabic or ASCII) — never rely on the lowercase-initial
            # check because Arabic script has no case distinction.
            if prev.endswith("،") or prev.endswith(","):
                merged[-1] = f"{prev} {line}"
            else:
                merged.append(line)
        else:
            # English / Latin merge heuristic: previous line does not end in
            # sentence-closing punctuation and current line starts lowercase.
            if (
                not prev.endswith((".", ":", ";", "!", "?", ")", "]"))
                and line[:1].islower()
            ):
                merged[-1] = f"{prev} {line}"
            else:
                merged.append(line)
    return merged


def stable_content_hash(text: str) -> str | None:
    """
    Return SHA-256 of whitespace-normalised text for change detection.

    Uses minimal normalisation (collapse whitespace only) so the hash is
    stable across minor formatting changes while remaining sensitive to any
    actual text change.  Returns None for empty/blank input.

    This is the canonical hash used by both pipeline.py (comparison) and
    db.save_document() (storage) — they must always call the same function.
    """
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


_ERROR_PAGE_MARKERS = re.compile(
    r"""
    (
        bad\s+gateway|
        gateway\s+time.?out|
        service\s+(temporarily\s+)?unavailable|
        page\s+not\s+found|
        couldn.t\s+find\s+what\s+you\s+were\s+looking\s+for|
        cloudflare\s+ray\s+id|
        attention\s+required.{0,40}cloudflare|
        access\s+denied|
        error\s+(403|404|500|502|503)|
        ^\s*404\s*$|
        الصفحة\s+غير\s+موجودة|
        عذراً?[^\n]{0,60}لم\s+نتمكن
    )
    """,
    re.IGNORECASE | re.MULTILINE | re.VERBOSE,
)

# Real error pages in the trail were tiny (VARA 404: 62 chars; Cloudflare
# 502: 178 chars normalized). A long document that merely *mentions* an
# error code is not an error page.
_ERROR_PAGE_MAX_CHARS = 1500


def looks_like_error_page(text: str) -> bool:
    """True when fetched content is an HTTP error / challenge page.

    Error pages must never be hashed as baselines: on 2026-06-11 a
    Cloudflare 502 and a VARA 404 became baselines and their recoveries
    alerted as CHANGED (docs/signal/judgment_table.md, ERROR_PAGE class).
    """
    if not text:
        return False
    stripped = text.strip()
    if len(stripped) > _ERROR_PAGE_MAX_CHARS:
        return False
    return bool(_ERROR_PAGE_MARKERS.search(stripped.replace("’", "'")))


def stable_normalized_hash(text: str) -> str:
    """Return SHA-256 of normalized text, or an empty string for empty input."""
    normalized = normalize_for_change_hash(text)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
