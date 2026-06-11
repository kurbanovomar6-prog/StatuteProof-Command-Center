"""
analyzer.py — Многоагентный AI-анализ регуляторных документов.

Стадии:
  Stage 1 — Legal Analyst:  правовая суть, обязательства, ссылки на статьи.
  Stage 2 — Risk Assessor:  финансовый риск, штраф, urgency_score (1–10).
  Stage 3 — Action Planner: 4–5 конкретных шагов для комплаенс-команды.

urgency_score рассчитывается в Stage 2 LLM:
  1–3  — низкий  (срок > 90 дней, штраф < $10K)
  4–6  — средний (срок 30–90 дней, штраф $10K–$1M)
  7–9  — высокий (срок < 30 дней, штраф > $1M)
  10   — критический (срок < 7 дней, штраф > $10M)

Если urgency_score отсутствует в ответе LLM — он вычисляется детерминированно
в generate_compliance_action_plan() (action_plan.py) без доп. API-вызова.
"""

import json
import logging
import os
import re

log = logging.getLogger(__name__)


def run_multi_agent(raw_text: str, jurisdiction: str) -> dict:
    """
    Запускает трёхстадийный AI-анализ документа.

    Параметры:
      raw_text    — извлечённый текст документа (первые 3000 символов)
      jurisdiction — код юрисдикции ("RU", "KZ", "AZ", "BY", "UZ")

    Возвращает dict:
      {
        "legal":          str,   правовая суть (3–4 предложения)
        "risk":           str,   описание риска
        "fines":          str,   размер штрафа "$25,000" или "N/A"
        "max_fine_usd":   int,   числовой размер штрафа в USD
        "urgency_days":   int,   дней до вступления в силу
        "urgency_score":  int,   приоритет 1–10 (NEW)
        "action":         list,  4–5 конкретных шагов
        "internal_conflict": str
      }
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return {
            "legal": "", "risk": "", "fines": "N/A",
            "max_fine_usd": 0, "urgency_days": 90,
            "urgency_score": 1, "action": [], "internal_conflict": "",
        }

    from openai import OpenAI
    cli     = OpenAI(api_key=api_key)
    snippet = raw_text[:3000]

    # ── Stage 1: Legal Analyst ────────────────────────────────────────────────
    legal = cli.chat.completions.create(
        model="gpt-4o-mini", max_tokens=350, temperature=0.1,
        messages=[
            {"role": "system", "content":
                "You are a senior regulatory lawyer specializing in CIS law. "
                "Analyze the legal essence: which articles are cited, "
                "core obligations, compliance deadline. "
                "3–4 sentences, precise and formal. Respond in Russian."},
            {"role": "user", "content": f"Jurisdiction: {jurisdiction}\n\n{snippet}"},
        ],
    ).choices[0].message.content or ""

    # ── Stage 2: Risk Assessor → JSON с urgency_score ────────────────────────
    risk_raw = cli.chat.completions.create(
        model="gpt-4o-mini", max_tokens=300, temperature=0.0,
        messages=[
            {"role": "system", "content": (
                'Output ONLY valid JSON with these exact keys: '
                '{"risk_desc":"str","max_fine_usd":int,"urgency_days":int,"urgency_score":int}. '
                'urgency_score rules (1–10 integer): '
                '  10 = срок < 7 дней И штраф > $10M; '
                '  7–9 = срок < 30 дней ИЛИ штраф > $1M; '
                '  4–6 = срок 30–90 дней ИЛИ штраф $10K–$1M; '
                '  1–3 = срок > 90 дней И штраф < $10K. '
                'max_fine_usd = 0 if not specified. urgency_days = 90 if unknown.'
            )},
            {"role": "user", "content":
                f"Legal analysis: {legal}\n\nDocument excerpt: {raw_text[:1200]}"},
        ],
    ).choices[0].message.content or "{}"

    try:
        m = re.search(r"\{.*\}", risk_raw, re.DOTALL)
        rd = json.loads(m.group()) if m else {}  # type: ignore[union-attr]
    except Exception:
        rd = {"risk_desc": risk_raw[:200], "max_fine_usd": 0, "urgency_days": 90, "urgency_score": 1}

    max_fine_usd  = int(rd.get("max_fine_usd", 0) or 0)
    urgency_days  = int(rd.get("urgency_days", 90) or 90)
    urgency_score = int(rd.get("urgency_score", 1) or 1)
    # Зажимаем в допустимый диапазон
    urgency_score = max(1, min(10, urgency_score))

    fines_str = f"${max_fine_usd:,}" if max_fine_usd else "N/A"

    # ── Stage 3: Action Planner → JSON array ─────────────────────────────────
    action_raw = cli.chat.completions.create(
        model="gpt-4o-mini", max_tokens=400, temperature=0.1,
        messages=[
            {"role": "system", "content": (
                "Output ONLY a JSON array of 4–5 concrete action steps for "
                "the compliance team. Each step is a string starting with a verb "
                "in Russian (imperative mood). "
                'Example: ["Уведомить юридический департамент...", "Сформировать резерв..."]'
            )},
            {"role": "user", "content":
                f"Legal: {legal}\n"
                f"Risk: {rd.get('risk_desc','')}\n"
                f"Urgency score: {urgency_score}/10\n"
                f"Jurisdiction: {jurisdiction}"},
        ],
    ).choices[0].message.content or "[]"

    try:
        m2 = re.search(r"\[.*\]", action_raw, re.DOTALL)
        actions = json.loads(m2.group()) if m2 else []  # type: ignore[union-attr]
        if not isinstance(actions, list):
            actions = [action_raw[:300]]
    except Exception:
        actions = [action_raw[:300]]

    return {
        "legal":             legal,
        "risk":              rd.get("risk_desc", ""),
        "fines":             fines_str,
        "max_fine_usd":      max_fine_usd,
        "urgency_days":      urgency_days,
        "urgency_score":     urgency_score,
        "action":            actions[:5],
        "internal_conflict": "",
    }
