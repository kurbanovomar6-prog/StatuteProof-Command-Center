"""
text_extractor.py — Промышленный воркер извлечения текста и OCR для RegRadar.

Конвейер обработки PDF:
  0. SHA-256 дедупликация по бинарному содержимому файла.
     Если хэш уже в БД — мгновенный abort, экономия GPT-токенов.
  1. pdfplumber  — быстрое извлечение текстового слоя (~50-200мс).
  2. PyMuPDF     — если pdfplumber дал < MIN_CHARS (нестандартный шрифт, CID).
  3. pytesseract — если PyMuPDF также < MIN_CHARS (скан, image-only PDF).
     Страницы рендерятся через fitz.Pixmap в 300 DPI, OCR на rus+eng.
  4. Ошибки защиты / повреждения → MANUAL_REVIEW_FLAG, статус обновляется в БД.

Латентность:
  Текстовый PDF  — pdfplumber only     ~50-200мс
  Гибридный PDF  — pdfplumber + PyMuPDF ~300-800мс
  Скан-PDF       — + pytesseract OCR    ~3-12с/страница
"""

import hashlib
import io
import logging
import time

log = logging.getLogger(__name__)

# ── Константы статусов ─────────────────────────────────────────────────────────

# Документ не поддаётся автоматической обработке — требуется ручной OCR
MANUAL_REVIEW_FLAG = "__ТРЕБУЕТ_РУЧНОЙ_ПРОВЕРКИ_OCR__"

# Содержимое уже обработано (дубликат по content-hash) — abort, не тратим GPT
CONTENT_DUPLICATE_FLAG = "__ДУБЛИКАТ_ПО_СОДЕРЖИМОМУ__"

# ── Параметры конвейера ────────────────────────────────────────────────────────
_MIN_CHARS   = 150   # минимум символов для признания извлечения успешным
_MAX_PAGES   = 15    # максимум страниц для обработки (цена vs. ценность)
_OCR_DPI     = 300   # разрешение рендера страниц для OCR (оптимум качество/скорость)
_OCR_LANGS   = "rus+eng"  # языковые паки tesseract для юридических текстов СНГ
_OCR_CONFIG  = "--psm 3 --oem 3"  # psm 3 = полностью автоматическое определение сегментов


def compute_content_hash(pdf_bytes: bytes) -> str:
    """
    SHA-256 хэш бинарного содержимого PDF.
    Одинаковый контент = одинаковый хэш, даже если URL изменился.
    """
    return hashlib.sha256(pdf_bytes).hexdigest()


# ── Этап 1: pdfplumber ────────────────────────────────────────────────────────

def _extract_pdfplumber(pdf_bytes: bytes) -> str:
    """
    Быстрое извлечение через pdfplumber.
    Надёжно работает с текстовыми PDF — сохраняет форматирование.
    Обнаруживает зашифрованные файлы через is_encrypted.
    """
    import pdfplumber

    parts: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            # Зашифрованный PDF — сразу возвращаем флаг ручной проверки
            if pdf.doc.is_encrypted:
                log.warning("pdfplumber: PDF зашифрован — помечаем для ручной проверки")
                return MANUAL_REVIEW_FLAG

            for page in pdf.pages[:_MAX_PAGES]:
                try:
                    t = page.extract_text()
                    if t:
                        parts.append(t.strip())
                except Exception as page_err:
                    log.debug("pdfplumber: ошибка страницы — %s", page_err)
                    continue

    except Exception as exc:
        log.debug("pdfplumber: сбой — %s", str(exc)[:120])

    return "\n\n".join(parts).strip()


# ── Этап 2: PyMuPDF (нативный, без OCR) ──────────────────────────────────────

def _extract_pymupdf_native(pdf_bytes: bytes) -> str:
    """
    Извлечение через PyMuPDF без OCR.
    Лучше работает с CID-шрифтами и нестандартными кодировками Кириллицы.
    """
    try:
        import fitz
    except ImportError:
        log.warning("PyMuPDF не установлен — этап 2 пропускается")
        return ""

    parts: list[str] = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        if doc.is_encrypted:
            log.warning("pymupdf: PDF зашифрован — помечаем для ручной проверки")
            doc.close()
            return MANUAL_REVIEW_FLAG

        for page in doc[:_MAX_PAGES]:
            try:
                t = page.get_text("text").strip()
                if t:
                    parts.append(t)
            except Exception as page_err:
                log.debug("pymupdf: ошибка страницы %d — %s", page.number, page_err)
                continue

        doc.close()

    except fitz.FileDataError as fde:
        # Повреждённый файл — фиксируем и возвращаем флаг ручной проверки
        log.error("pymupdf: повреждённый файл (FileDataError) — %s", str(fde)[:100])
        return MANUAL_REVIEW_FLAG
    except Exception as exc:
        log.debug("pymupdf native: сбой — %s", str(exc)[:120])

    return "\n\n".join(parts).strip()


# ── Этап 3: pytesseract OCR через fitz.Pixmap ─────────────────────────────────

def _extract_pytesseract_ocr(pdf_bytes: bytes) -> str:
    """
    OCR через pytesseract с рендером страниц через fitz.Pixmap.
    Применяется только для image-only PDF (скан, отсутствует текстовый слой).

    Конвейер на страницу:
      fitz.Page → Pixmap(300 DPI, RGB) → PIL Image (L, grayscale) → pytesseract
    Языки: rus+eng для покрытия кириллических и латинских юридических терминов.
    """
    try:
        import fitz
    except ImportError:
        log.warning("PyMuPDF не установлен — OCR недоступен")
        return ""

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        log.warning("pytesseract или Pillow не установлены — OCR недоступен")
        return ""

    parts: list[str] = []
    t0 = time.monotonic()

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        if doc.is_encrypted:
            doc.close()
            return MANUAL_REVIEW_FLAG

        pages_to_ocr = doc[:_MAX_PAGES]
        log.info("OCR: начинаем обработку %d страниц при %d DPI (rus+eng)",
                 len(list(pages_to_ocr)), _OCR_DPI)

        for page in doc[:_MAX_PAGES]:
            try:
                # Рендеринг страницы в растр с заданным DPI через матрицу масштабирования
                scale = _OCR_DPI / 72.0  # 72 dpi — стандартное разрешение PDF
                mat   = fitz.Matrix(scale, scale)
                pix   = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)

                # Конвертируем Pixmap в PIL Image через raw-байты
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Граyscale улучшает точность OCR для чёрно-белых юридических документов
                img_gray = img.convert("L")

                # Запуск tesseract: psm 3 = авто-сегментация, oem 3 = LSTM-движок
                text = pytesseract.image_to_string(
                    img_gray,
                    lang=_OCR_LANGS,
                    config=_OCR_CONFIG,
                )
                if text.strip():
                    parts.append(text.strip())

                log.debug(
                    "OCR: страница %d — %d символов (%.1f с)",
                    page.number, len(text), time.monotonic() - t0,
                )

            except pytesseract.TesseractNotFoundError:
                log.error(
                    "tesseract не найден. Установите: brew install tesseract tesseract-lang "
                    "(macOS) или apt install tesseract-ocr tesseract-ocr-rus (Ubuntu)."
                )
                doc.close()
                return ""
            except Exception as page_err:
                log.warning("OCR: ошибка страницы %d — %s", page.number, str(page_err)[:100])
                continue

        doc.close()

    except fitz.FileDataError as fde:
        log.error("OCR: повреждённый PDF — %s", str(fde)[:100])
        return MANUAL_REVIEW_FLAG
    except Exception as exc:
        log.warning("OCR: критическая ошибка — %s", str(exc)[:120])

    elapsed = time.monotonic() - t0
    result  = "\n\n".join(parts).strip()
    log.info("OCR: завершён за %.1f с, извлечено %d символов", elapsed, len(result))
    return result


# ── Публичный API ──────────────────────────────────────────────────────────────

def extract_text_from_pdf(
    pdf_bytes: bytes,
    known_content_hashes: set[str] | None = None,
) -> str:
    """
    Извлекает текст из PDF с трёхэтапным fallback-конвейером.

    Параметры:
      pdf_bytes              — сырые байты PDF-файла
      known_content_hashes   — множество SHA-256 хэшей уже обработанных PDF.
                               Если хэш совпадает — мгновенный возврат
                               CONTENT_DUPLICATE_FLAG без дальнейшей обработки.

    Возвращает:
      str  — извлечённый текст
      CONTENT_DUPLICATE_FLAG  — файл уже обработан (дубликат по содержимому)
      MANUAL_REVIEW_FLAG      — все методы провалились, требуется ручная проверка
    """
    t_start = time.monotonic()

    # ── Этап 0: SHA-256 дедупликация по бинарному содержимому ────────────────
    content_hash = compute_content_hash(pdf_bytes)
    if known_content_hashes and content_hash in known_content_hashes:
        log.debug(
            "[DEDUP] Пропуск — content_hash %s уже обработан", content_hash[:16]
        )
        return CONTENT_DUPLICATE_FLAG

    # ── Этап 1: pdfplumber (быстрый, ~50-200мс) ───────────────────────────────
    text = _extract_pdfplumber(pdf_bytes)

    if text == MANUAL_REVIEW_FLAG:
        # Зашифрован на этапе pdfplumber — сразу завершаем
        log.warning(
            "extract_text: зашифрованный PDF (pdfplumber) — %.2f с",
            time.monotonic() - t_start,
        )
        return MANUAL_REVIEW_FLAG

    if len(text) >= _MIN_CHARS:
        log.debug(
            "extract_text: extractor=pdfplumber chars=%d латентность=%.2f с",
            len(text), time.monotonic() - t_start,
        )
        return text

    log.info("pdfplumber: недостаточно символов (%d), переход на PyMuPDF", len(text))

    # ── Этап 2: PyMuPDF нативный (CID-шрифты, нестандартные кодировки) ────────
    text = _extract_pymupdf_native(pdf_bytes)

    if text == MANUAL_REVIEW_FLAG:
        log.error(
            "extract_text: повреждённый/зашифрованный PDF (PyMuPDF) — %.2f с",
            time.monotonic() - t_start,
        )
        return MANUAL_REVIEW_FLAG

    if len(text) >= _MIN_CHARS:
        log.debug(
            "extract_text: extractor=pymupdf chars=%d латентность=%.2f с",
            len(text), time.monotonic() - t_start,
        )
        return text

    log.info("PyMuPDF: недостаточно символов (%d) — PDF скорее всего image-only, запуск OCR", len(text))

    # ── Этап 3: pytesseract OCR (медленный, ~3-12с/стр., только для скан-PDF) ─
    text = _extract_pytesseract_ocr(pdf_bytes)

    if text == MANUAL_REVIEW_FLAG:
        log.error(
            "extract_text: повреждённый PDF (OCR-этап) — помечаем для ручной проверки"
        )
        return MANUAL_REVIEW_FLAG

    elapsed = time.monotonic() - t_start

    if len(text) >= _MIN_CHARS:
        log.info(
            "extract_text: extractor=pytesseract_ocr chars=%d латентность=%.2f с",
            len(text), elapsed,
        )
        return text

    # ── Этап 4: все методы провалились ────────────────────────────────────────
    # Запаролен, битый encoding, нестандартный формат — требуется ручная проверка
    log.error(
        "extract_text: все три экстрактора не смогли извлечь текст за %.2f с. "
        "Документ помечен как '%s'. "
        "Причины: шифрование, повреждённый файл, нераспознанная кодировка.",
        elapsed, MANUAL_REVIEW_FLAG,
    )
    return MANUAL_REVIEW_FLAG


def update_db_manual_review(url: str, reason: str = "OCR Error") -> None:
    """
    Обновляет запись в БД — устанавливает статус 'Требуется ручная проверка'.
    Вызывается из pipeline.py когда extract_text_from_pdf вернул MANUAL_REVIEW_FLAG.

    Параметры:
      url    — source_url документа для поиска записи по url_hash
      reason — текстовое пояснение для операторов (по умолчанию 'OCR Error')
    """
    import hashlib
    h = hashlib.sha256(url.encode()).hexdigest()

    try:
        from app.infrastructure.db.session import engine
        from sqlalchemy import text as _sql
        with engine.connect() as c:
            c.execute(
                _sql(
                    "UPDATE regulations "
                    "SET status='HUMAN_REVIEW', "
                    "    summary=:summary "
                    "WHERE url_hash=:h"
                ),
                {
                    "h":       h,
                    "summary": f"Требуется ручная проверка ({reason}). "
                               "Документ не поддаётся автоматической обработке.",
                },
            )
            c.commit()
        log.info("update_db_manual_review: статус HUMAN_REVIEW установлен для %s", url[-60:])
    except Exception as exc:
        log.warning("update_db_manual_review: ошибка БД — %s", exc)
