"""
Telegram channel monitor via public t.me/s/<channel> web archive.
No API key required — uses public HTML endpoint.

Returns posts that pass regulatory pre-filter as dicts ready for DB insertion.
All records stored with source_type="TELEGRAM_INTEL", status="HUMAN_REVIEW".
"""
import logging
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Каналы для мониторинга (только публичные)
DEFAULT_CHANNELS: dict[str, str] = {
    "RU": "https://t.me/s/centralbank_russia",
    "RU_FIN": "https://t.me/s/minfin_ru",
    "KZ": "https://t.me/s/arrfr_official",
}

# Минимум совпадений сигнальных слов для сохранения поста
_SIGNAL_THRESHOLD = 2

_SIGNAL_WORDS: list[str] = [
    "постановление", "положение", "приказ", "указ", "федеральный закон",
    "штраф", "лицензия", "требования", "нормативный", "обязательный",
    "вступает в силу", "предписание", "ответственность", "санкции",
    "регулятор", "регулирование", "compliance", "требует",
    "qaydalar", "tələblər", "qərar", "lisenziya",           # AZ
    "қаулы", "ереже", "нұсқаулық",                          # KZ
]

_NOISE_WORDS: list[str] = [
    "курс доллара", "usd/rub", "eur/rub", "обменный курс",
    "инфляция составила", "ключевая ставка осталась",
    "поздравляем", "приглашаем", "конференция", "вебинар",
    "акция", "скидка", "предлагаем",
]

_MAX_POST_LEN = 3000   # обрезаем слишком длинные посты


def _extract_posts(html: str, channel_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []

    for msg in soup.select(".tgme_widget_message"):
        text_el = msg.select_one(".tgme_widget_message_text")
        date_el = msg.select_one(".tgme_widget_message_date time")
        link_el = msg.select_one(".tgme_widget_message_date a")

        if not text_el:
            continue

        body = text_el.get_text(" ", strip=True)
        body_lower = body.lower()

        # Noise rejection first (cheap)
        if any(n in body_lower for n in _NOISE_WORDS):
            continue

        # Count signal hits
        signal_hits = sum(1 for s in _SIGNAL_WORDS if s in body_lower)
        if signal_hits < _SIGNAL_THRESHOLD:
            continue

        # Parse date
        pub_date = ""
        if date_el and date_el.get("datetime"):
            try:
                dt = datetime.fromisoformat(date_el["datetime"].rstrip("Z"))
                pub_date = dt.strftime("%Y-%m-%d")
            except Exception:
                pub_date = ""

        msg_url = ""
        if link_el and link_el.get("href", "").startswith("https://t.me/"):
            msg_url = link_el["href"]
        else:
            msg_url = channel_url

        results.append({
            "text":       body[:_MAX_POST_LEN],
            "date":       pub_date,
            "source_url": msg_url,
            "signal_hits": signal_hits,
        })

    return results


def _post_to_reg_record(post: dict, jurisdiction: str) -> dict:
    """Convert raw post dict to a format pipeline can use."""
    # Вытаскиваем первую строку как заголовок
    lines = [l.strip() for l in post["text"].split("\n") if l.strip()]
    title = lines[0][:300] if lines else post["text"][:100]

    # Очищаем title от эмодзи-мусора в начале
    title = re.sub(r"^[\U0001F300-\U0001FFFF\s]+", "", title).strip()
    if not title:
        title = f"[TG] {jurisdiction} регуляторное обновление"
    else:
        title = f"[TG] {title}"

    summary = post["text"][:500]
    today = datetime.utcnow().strftime("%Y-%m-%d")

    return {
        "text":        post["text"],          # для AI-анализа
        "title":       title,
        "jurisdiction": jurisdiction,
        "publication_date": post["date"] or today,
        "effective_date":   post["date"] or today,
        "summary":     summary,
        "industries":  "fintech,banking",
        "critical_level": "MEDIUM",           # AI скорректирует
        "source_url":  post["source_url"],
        "confidence":  0.55,                  # ниже порога — не авто-валидировать
        "status":      "HUMAN_REVIEW",
        "source_type": "TELEGRAM_INTEL",
    }


def scrape_channel(
    channel_url: str,
    jurisdiction: str,
    known_urls: set[str] | None = None,
) -> list[dict]:
    """
    Scrape one public Telegram channel.
    Returns list of record dicts (not yet saved) for NEW posts only.
    """
    known_urls = known_urls or set()

    try:
        r = httpx.get(channel_url, headers=_HEADERS, timeout=15, follow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        log.warning("tg_monitor: fetch failed %s — %s", channel_url, e)
        return []

    posts = _extract_posts(r.text, channel_url)
    log.info("tg_monitor: %s → %d relevant posts", channel_url[-40:], len(posts))

    results: list[dict] = []
    for post in posts:
        if post["source_url"] in known_urls:
            continue
        rec = _post_to_reg_record(post, jurisdiction)
        results.append(rec)

    return results


def run_all_channels(
    channels: dict[str, str] | None = None,
    known_urls: set[str] | None = None,
) -> list[dict]:
    """
    Run all configured channels. Returns all new records.
    channel dict: {jurisdiction: channel_url}
    """
    channels = channels or DEFAULT_CHANNELS
    known_urls = known_urls or set()

    all_records: list[dict] = []
    for jur, url in channels.items():
        # Нормализуем jurisdiction (RU_FIN → RU)
        jur_code = jur.split("_")[0] if "_" in jur else jur
        recs = scrape_channel(url, jur_code, known_urls)
        all_records.extend(recs)

    log.info("tg_monitor: total %d new records from %d channels",
             len(all_records), len(channels))
    return all_records
