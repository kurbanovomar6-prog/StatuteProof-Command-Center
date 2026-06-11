"""
HTML → clean plain-text extractor — v2.

Improvements over v1:
  - Cookie / consent banner removal (detected by class/id keywords)
  - Whitespace normalisation (collapse multiple spaces, strip non-breaking spaces)
  - Exact-match paragraph deduplication (unchanged from v1, kept explicit)
  - Minimum 30-char filter (unchanged)
  - Fallback to raw body text when no semantic elements match
"""

import re

from bs4 import BeautifulSoup

# ── constants ─────────────────────────────────────────────────────────────────

_NOISE_TAGS = [
    "script", "style", "noscript", "head",
    "nav", "footer", "header", "aside",
    "form", "button", "input", "select",
    "textarea", "iframe", "img", "svg",
]

_CONTENT_TAGS = [
    "p", "li", "td", "th",
    "h1", "h2", "h3", "h4", "h5",
    "article", "section", "blockquote",
    "dd", "dt", "pre",
]

# Substrings in class/id attributes that signal cookie / consent banners
_COOKIE_SIGNALS = (
    "cookie", "consent", "gdpr", "banner",
    "cc-banner", "cookiebar", "privacy-notice",
    "cookie-notice", "cookie-popup", "cookie-wall",
)

_MIN_BLOCK_LEN = 30

# Regex for collapsing any run of whitespace (including \xa0) to a single space
_WHITESPACE_RE = re.compile(r"[\s\xa0]+")


# ── helpers ───────────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    """Collapse whitespace and strip leading/trailing spaces."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def _is_cookie_banner(tag) -> bool:
    """Return True when a tag looks like a cookie / consent banner."""
    if not tag.attrs:  # guard: decomposed siblings have attrs=None
        return False
    for attr in ("class", "id"):
        value = tag.get(attr, "")
        combined = " ".join(value) if isinstance(value, list) else value
        combined = combined.lower()
        if any(signal in combined for signal in _COOKIE_SIGNALS):
            return True
    return False


# ── public API ────────────────────────────────────────────────────────────────

def extract_text(html: str) -> str:
    """
    Parse `html` and return clean paragraph text separated by double newlines.

    Steps:
      1. Remove noise tags (scripts, styles, nav, footer, …)
      2. Remove cookie / consent banner containers
      3. Collect text from semantic content elements
      4. Normalise whitespace in every block
      5. Deduplicate and filter short fragments
      6. Fallback to line-by-line body text if nothing was found

    Returns
    -------
    str
        Paragraphs delimited by "\\n\\n".  Empty string when nothing extracted.
    """
    soup = BeautifulSoup(html, "html.parser")

    # ── 1. Strip structural noise ─────────────────────────────────────
    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # ── 2. Strip cookie banners ───────────────────────────────────────
    for tag in soup.find_all(True):
        if _is_cookie_banner(tag):
            tag.decompose()

    # ── 3. Collect semantic content blocks ────────────────────────────
    blocks: list[str] = []
    seen:   set[str]  = set()

    for el in soup.find_all(_CONTENT_TAGS):
        raw  = el.get_text(separator=" ", strip=True)
        text = _normalise(raw)
        if len(text) < _MIN_BLOCK_LEN or text in seen:
            continue
        seen.add(text)
        blocks.append(text)

    # ── 4. Fallback: raw body text ────────────────────────────────────
    if not blocks:
        for line in soup.get_text(separator="\n").splitlines():
            text = _normalise(line)
            if len(text) >= _MIN_BLOCK_LEN and text not in seen:
                seen.add(text)
                blocks.append(text)

    return "\n\n".join(blocks)
