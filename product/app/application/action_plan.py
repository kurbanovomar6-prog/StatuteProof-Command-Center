"""
action_plan.py — Генератор структурированных планов комплаенс-мероприятий.

Назначение:
  Для каждого документа с уровнем CRITICAL или HIGH автоматически формирует
  трёхшаговый план действий, привязанный к конкретным обязательствам документа.

  Urgency Score (1–10):
    Рассчитывается LLM на основе:
      • max_fine_usd  — размер штрафа (до 5 баллов)
      • urgency_days  — срок до вступления в силу (до 3 баллов)
      • critical_level — уровень критичности (1–2 балла)
    Оцифровывается в числовое значение 1-10.

  Compliance Action Plan:
    3 конкретных шага:
      Step 1: Уведомление (Legal/Compliance)
      Step 2: Финансовые/операционные меры
      Step 3: Обновление внутренней документации

  Сохранение:
    action_plan (JSON) → regulations.action_plan
    urgency_score (int) → regulations.urgency_score

Вызов из pipeline.py после run_multi_agent().
"""

import json
import logging
import re
from datetime import datetime

log = logging.getLogger(__name__)

# ── Пороги для urgency_score ──────────────────────────────────────────────────
_FINE_SCORE_MAP = [
    (10_000_000, 5),  # > $10M  → 5 баллов
    (1_000_000,  4),  # > $1M   → 4 балла
    (100_000,    3),  # > $100K → 3 балла
    (10_000,     2),  # > $10K  → 2 балла
    (0,          1),  # любой  → 1 балл
]
_DAYS_SCORE_MAP = [
    (7,   3),  # < 7 дней   → 3 балла
    (30,  2),  # < 30 дней  → 2 балла
    (90,  1),  # < 90 дней  → 1 балл
    (999, 0),  # далеко     → 0 баллов
]
_LEVEL_SCORE = {"CRITICAL": 2, "HIGH": 1, "MEDIUM": 0, "LOW": 0}


def _compute_urgency_score(
    max_fine_usd: int,
    urgency_days: int,
    critical_level: str,
) -> int:
    """
    Детерминированная формула urgency_score (1–10).
    Не требует LLM-вызова — работает полностью локально.

    Формула: fine_score + days_score + level_score, нормализованная к [1, 10].
    """
    fine_score  = next((s for threshold, s in _FINE_SCORE_MAP if max_fine_usd > threshold), 1)
    days_score  = next((s for threshold, s in _DAYS_SCORE_MAP if urgency_days < threshold), 0)
    level_score = _LEVEL_SCORE.get(critical_level.upper(), 0)

    raw = fine_score + days_score + level_score
    # Нормализация: min=1, max=10
    return min(10, max(1, raw))


def _parse_fine_int(fines_str: str | None) -> int:
    """Конвертирует '$25,000' → 25000. Возвращает 0 при ошибке."""
    if not fines_str:
        return 0
    try:
        digits = re.sub(r"[^\d]", "", str(fines_str))
        return int(digits) if digits else 0
    except (ValueError, TypeError):
        return 0


def generate_compliance_action_plan(
    ai_analysis: dict,
    regulation_title: str,
    jurisdiction: str,
    critical_level: str,
    effective_date: str | None = None,
    use_llm: bool = True,
) -> dict:
    """
    Формирует структурированный план комплаенс-мероприятий.

    Параметры:
      ai_analysis      — результат run_multi_agent() (dict)
      regulation_title — заголовок нормативного акта
      jurisdiction     — код юрисдикции ("RU", "KZ", ...)
      critical_level   — уровень критичности
      effective_date   — дата вступления в силу (ISO string)
      use_llm          — использовать LLM для улучшенного плана (True по умолчанию)

    Возвращает dict:
      {
        "urgency_score":    int (1–10),
        "urgency_label":    str ("КРИТИЧЕСКИЙ" / "ВЫСОКИЙ" / "СРЕДНИЙ"),
        "max_fine_usd":     int,
        "days_to_deadline": int,
        "steps": [
          {
            "step_num":     int,
            "action":       str,
            "responsible":  str,
            "deadline_days":int,
            "priority":     str ("НЕМЕДЛЕННО" / "В ТЕЧЕНИЕ НЕДЕЛИ" / "30 ДНЕЙ"),
          },
          ...
        ],
        "generated_at": str (ISO),
      }
    """
    # ── Данные из AI-анализа ──────────────────────────────────────────────────
    max_fine_usd  = _parse_fine_int(ai_analysis.get("fines"))
    urgency_days  = int(ai_analysis.get("urgency_days") or 90)
    legal_text    = str(ai_analysis.get("legal") or "")
    risk_text     = str(ai_analysis.get("risk")  or "")
    existing_acts = list(ai_analysis.get("action") or [])

    # ── Urgency Score ─────────────────────────────────────────────────────────
    urgency_score = _compute_urgency_score(max_fine_usd, urgency_days, critical_level)
    if urgency_score >= 8:
        urgency_label = "КРИТИЧЕСКИЙ"
    elif urgency_score >= 5:
        urgency_label = "ВЫСОКИЙ"
    elif urgency_score >= 3:
        urgency_label = "СРЕДНИЙ"
    else:
        urgency_label = "НИЗКИЙ"

    # ── Дней до дедлайна ─────────────────────────────────────────────────────
    days_to_deadline = urgency_days
    if effective_date:
        try:
            eff_dt = datetime.fromisoformat(effective_date[:10])
            days_to_deadline = max(0, (eff_dt - datetime.utcnow()).days)
        except ValueError:
            pass

    # ── Генерация плана: LLM или детерминированный fallback ──────────────────
    if use_llm and legal_text:
        steps = _llm_generate_steps(
            regulation_title=regulation_title,
            jurisdiction=jurisdiction,
            legal_text=legal_text,
            risk_text=risk_text,
            max_fine_usd=max_fine_usd,
            urgency_days=days_to_deadline,
            critical_level=critical_level,
        )
    else:
        steps = _deterministic_steps(
            existing_acts=existing_acts,
            jurisdiction=jurisdiction,
            max_fine_usd=max_fine_usd,
            days_to_deadline=days_to_deadline,
        )

    return {
        "urgency_score":    urgency_score,
        "urgency_label":    urgency_label,
        "max_fine_usd":     max_fine_usd,
        "days_to_deadline": days_to_deadline,
        "steps":            steps[:3],  # строго 3 шага
        "generated_at":     datetime.utcnow().isoformat(),
    }


def _llm_generate_steps(
    regulation_title: str,
    jurisdiction: str,
    legal_text: str,
    risk_text: str,
    max_fine_usd: int,
    urgency_days: int,
    critical_level: str,
) -> list[dict]:
    """
    LLM-генерация трёхшагового плана через GPT-4o-mini.
    Возвращает список из ровно 3 шагов в структурированном JSON.
    Fallback → _deterministic_steps() при недоступности API.
    """
    import os
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return _deterministic_steps([], jurisdiction, max_fine_usd, urgency_days)

    try:
        from openai import OpenAI
        cli = OpenAI(api_key=api_key)

        fine_str = f"${max_fine_usd:,}" if max_fine_usd else "не определён"
        prompt_system = (
            "Ты — старший комплаенс-директор банка. "
            "Сформируй ровно 3 конкретных действия для команды комплаенс "
            "в ответ на новый нормативный акт. "
            "Верни ТОЛЬКО JSON-массив из 3 объектов: "
            '{"step_num":int, "action":str, "responsible":str, '
            '"deadline_days":int, "priority":str}. '
            "Шаги должны быть: 1-уведомление, 2-операционные меры, "
            "3-документация/политики. "
            "priority: НЕМЕДЛЕННО / В ТЕЧЕНИЕ НЕДЕЛИ / 30 ДНЕЙ. "
            "Ответ строго на русском языке."
        )
        prompt_user = (
            f"Регуляторный акт: {regulation_title[:200]}\n"
            f"Юрисдикция: {jurisdiction}\n"
            f"Уровень риска: {critical_level}\n"
            f"Размер штрафа: {fine_str}\n"
            f"Дней до вступления в силу: {urgency_days}\n\n"
            f"Правовая суть:\n{legal_text[:600]}\n\n"
            f"Оценка риска:\n{risk_text[:300]}"
        )

        resp = cli.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=500,
            temperature=0.05,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user",   "content": prompt_user},
            ],
        )
        raw = resp.choices[0].message.content or "[]"
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            steps = json.loads(match.group())
            if isinstance(steps, list) and len(steps) >= 1:
                return _normalize_steps(steps)

    except Exception as e:
        log.warning("[ACTION_PLAN] LLM недоступен, fallback к детерминированному плану — %s", e)

    return _deterministic_steps([], jurisdiction, max_fine_usd, urgency_days)


def _deterministic_steps(
    existing_acts: list,
    jurisdiction: str,
    max_fine_usd: int,
    days_to_deadline: int,
) -> list[dict]:
    """
    Детерминированный шаблонный план — не требует LLM.
    Используется как fallback при недоступности OpenAI.
    """
    fine_str = f"${max_fine_usd:,}" if max_fine_usd else "уточнить у юристов"
    reserve  = f"${int(max_fine_usd * 1.2):,}" if max_fine_usd else "резерв по решению CFO"

    # Срочность первого шага
    if days_to_deadline <= 7:
        step1_priority = "НЕМЕДЛЕННО"
        step1_deadline = 1
    elif days_to_deadline <= 30:
        step1_priority = "В ТЕЧЕНИЕ НЕДЕЛИ"
        step1_deadline = 5
    else:
        step1_priority = "30 ДНЕЙ"
        step1_deadline = 14

    # Шаг 1 берём из LLM-actions если они есть
    step1_action = (
        str(existing_acts[0]) if existing_acts
        else f"Уведомить юридический департамент о новом требовании [{jurisdiction}]"
    )
    step2_action = (
        str(existing_acts[1]) if len(existing_acts) > 1
        else f"Сформировать резерв на покрытие потенциального штрафа {reserve}"
    )
    step3_action = (
        str(existing_acts[2]) if len(existing_acts) > 2
        else "Обновить внутренние комплаенс-политики и провести инструктаж сотрудников"
    )

    return [
        {
            "step_num":     1,
            "action":       step1_action,
            "responsible":  "Директор по комплаенс / Юридический департамент",
            "deadline_days": step1_deadline,
            "priority":     step1_priority,
        },
        {
            "step_num":     2,
            "action":       step2_action,
            "responsible":  "CFO / Финансовый департамент",
            "deadline_days": min(days_to_deadline, 14) if days_to_deadline > 0 else 7,
            "priority":     "В ТЕЧЕНИЕ НЕДЕЛИ",
        },
        {
            "step_num":     3,
            "action":       step3_action,
            "responsible":  "HR / Комплаенс-офицер",
            "deadline_days": min(days_to_deadline, 30) if days_to_deadline > 0 else 21,
            "priority":     "30 ДНЕЙ",
        },
    ]


def _normalize_steps(raw_steps: list) -> list[dict]:
    """Нормализует LLM-ответ к стандартной схеме шагов."""
    normalized = []
    for i, s in enumerate(raw_steps[:3], 1):
        if isinstance(s, dict):
            normalized.append({
                "step_num":     int(s.get("step_num", i)),
                "action":       str(s.get("action", ""))[:400],
                "responsible":  str(s.get("responsible", ""))[:100],
                "deadline_days": int(s.get("deadline_days", 7)),
                "priority":     str(s.get("priority", "30 ДНЕЙ")),
            })
        elif isinstance(s, str):
            normalized.append({
                "step_num":     i,
                "action":       s[:400],
                "responsible":  "Комплаенс-офицер",
                "deadline_days": 7 * i,
                "priority":     "В ТЕЧЕНИЕ НЕДЕЛИ" if i == 1 else "30 ДНЕЙ",
            })
    return normalized


def save_action_plan(source_url: str, plan: dict, urgency_score: int) -> bool:
    """
    Сохраняет план действий и urgency_score в БД.

    Вызывается из pipeline.py сразу после generate_compliance_action_plan().
    Обновляет regulations по url_hash.
    """
    import hashlib
    from sqlalchemy import text as _sql
    from app.infrastructure.db.session import engine

    url_hash = hashlib.sha256(source_url.encode()).hexdigest()
    try:
        with engine.connect() as c:
            c.execute(_sql("""
                UPDATE regulations
                SET action_plan   = :plan,
                    urgency_score = :score
                WHERE url_hash = :h
            """), {
                "plan":  json.dumps(plan, ensure_ascii=False),
                "score": urgency_score,
                "h":     url_hash,
            })
            c.commit()
        return True
    except Exception as exc:
        log.error("[ACTION_PLAN] ошибка сохранения для %s — %s", source_url[:60], exc)
        return False
