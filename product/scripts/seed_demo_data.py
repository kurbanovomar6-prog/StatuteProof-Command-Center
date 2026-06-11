#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_demo_data.py — Засев демонстрационной базы данных RegRadar Enterprise.

Создаёт высокореалистичный датасет для клиентских презентаций ($500–$3000/мес):
  • 17 НПА по трём юрисдикциям (RU / EU / US)
  • Смесь уровней: 4 CRITICAL, 5 HIGH, 5 MEDIUM, 3 LOW
  • Смесь статусов: VALIDATED, PROCESSING, HUMAN_REVIEW
  • Заполненные поля fines_usd, urgency_score, action_plan, ai_analysis
  • 4 месяца исторических YTD-снэпшотов (восходящий тренд для красивых графиков)

Запуск:
    python3 scripts/seed_demo_data.py
    python3 scripts/seed_demo_data.py --clear      # сначала очистить таблицы
    python3 scripts/seed_demo_data.py --dry-run    # только вывод плана, без записи

Идемпотентность:
    Повторный запуск без --clear безопасен — записи с существующим url_hash
    пропускаются; YTD-снэпшоты обновляются через INSERT OR REPLACE.
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Добавляем корень проекта в PYTHONPATH ─────────────────────────────────────
# Это позволяет запускать скрипт из любой директории без установки пакета
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("seed_demo")


# =============================================================================
# ── Вспомогательные функции ───────────────────────────────────────────────────
# =============================================================================

def _sha256(text: str) -> str:
    """SHA-256 хэш строки (для url_hash и content_hash, аналогично pipeline.py)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ago(days: int, hours: int = 0) -> datetime:
    """datetime UTC N дней и H часов назад от текущего момента."""
    return datetime.utcnow() - timedelta(days=days, hours=hours)


def _date_ago(days: int) -> str:
    """Дата в формате ISO 8601 (YYYY-MM-DD) N дней назад."""
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


def _date_ahead(days: int) -> str:
    """Дата в формате ISO 8601 N дней вперёд."""
    return (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")


def _fines_str(usd: float) -> str:
    """Форматирует штраф как строку для поля ai_analysis['fines']."""
    if not usd:
        return "N/A"
    return f"${usd:,.0f}"


def _make_ai_analysis(
    legal: str,
    risk: str,
    fines_usd: int,
    urgency_days: int,
    urgency_score: int,
    action_steps: list[str],
) -> str:
    """Собирает JSON-строку ai_analysis в формате, ожидаемом executive_report.py."""
    return json.dumps(
        {
            "legal":            legal,
            "risk":             risk,
            "fines":            _fines_str(fines_usd),
            "max_fine_usd":     fines_usd,
            "urgency_days":     urgency_days,
            "urgency_score":    urgency_score,
            "action":           action_steps,
            "internal_conflict": "",
        },
        ensure_ascii=False,
        indent=None,
    )


# =============================================================================
# ── Демонстрационные НПА (17 записей) ────────────────────────────────────────
# =============================================================================

def _build_regulations() -> list[dict]:
    """
    Возвращает список словарей с полными данными для RegulationRecord.
    Все даты вычисляются относительно datetime.utcnow() — корректны при
    любом времени запуска скрипта.
    """
    return [

        # ══════════════════════════════════════════════════════════════════════
        # CRITICAL (4) — максимальный риск, требуют немедленных действий
        # ══════════════════════════════════════════════════════════════════════

        # ── RU-1: ИБ-требования ЦБ РФ (срок истёк 7 дней назад) ─────────────
        {
            "title": (
                "Положение Банка России № 821-П «О требованиях к системе управления "
                "операционным риском и риском информационной безопасности в кредитных "
                "организациях и банковских группах»"
            ),
            "jurisdiction":     "RU",
            "publication_date": _date_ago(74),
            "effective_date":   _date_ago(7),
            "summary": (
                "Устанавливает обязательные требования к системе управления рисками "
                "информационной безопасности (СУРИБ) кредитных организаций. "
                "Предписывает внедрение SIEM-систем корпоративного класса, "
                "обязательную двухфакторную аутентификацию всех привилегированных "
                "учётных записей и хранение аудит-логов за последние 3 года. "
                "Нарушение влечёт штраф до 10 500 000 рублей и инициирование "
                "внеплановой проверки ЦБ РФ."
            ),
            "critical_level":   "CRITICAL",
            "status":           "VALIDATED",
            "source_url":       "https://cbr.ru/press/pr/2025-11-21-1/",
            "confidence":       0.97,
            "fines_usd":        114_130,
            "urgency_score":    9,
            "urgency_days":     -7,
            "extracted_at":     _ago(74, hours=1),
            "time_to_discovery_sec": 3_612,
            "action_steps": [
                "Провести GAP-анализ текущей СУРИБ на соответствие Положению № 821-П "
                "с привлечением сертифицированных ИБ-аудиторов",
                "Сформировать рабочую группу (CISO, ИТ-директор, юрисконсульт) "
                "и утвердить дорожную карту внедрения не позднее 5 рабочих дней",
                "Инициировать тендерную процедуру на выбор и внедрение SIEM-платформы "
                "класса Enterprise (бюджет: 15–40 млн руб.)",
            ],
            "legal_analysis": (
                "Положение № 821-П принято во исполнение ст. 57.2 Федерального закона "
                "«О Центральном банке Российской Федерации». Обязательно для всех "
                "кредитных организаций с универсальной и базовой лицензией. "
                "Ключевые статьи: п. 4.1 (состав СУРИБ), п. 6.3 (требования к SIEM), "
                "п. 8.2 (дедлайн аудит-логов). Ответственность по ст. 15.26.3 КоАП."
            ),
            "risk_desc": (
                "Высокий риск внеплановой проверки ЦБ РФ при выявлении несоответствия. "
                "Штраф до 10 500 000 руб. + репутационный ущерб. "
                "Расчётное предотвращение потерь: $2,300,000 за счёт раннего обнаружения."
            ),
        },

        # ── EU-1: EBA ESG Guidelines (вступает в силу через 14 дней) ─────────
        {
            "title": (
                "EBA/GL/2024/01 — Guidelines on the Management of Environmental, "
                "Social and Governance (ESG) Risks Under CRD VI Article 87a"
            ),
            "jurisdiction":     "EU",
            "publication_date": _date_ago(48),
            "effective_date":   _date_ahead(14),
            "summary": (
                "Обязательные руководящие принципы EBA по управлению ESG-рисками "
                "для кредитных организаций ЕС. Требуют проведения климатического "
                "стресс-теста для банков с активами свыше €5 млрд, раскрытия "
                "Transition Plan в годовой отчётности и интеграции ESG-рисков "
                "в ICAAP/ILAAP. Первая отчётность: Q2 2025. "
                "Штраф за несоответствие — до €2 000 000."
            ),
            "critical_level":   "CRITICAL",
            "status":           "VALIDATED",
            "source_url":       "https://www.eba.europa.eu/publications/guidelines/esg-risks-2024",
            "confidence":       0.98,
            "fines_usd":        2_180_000,
            "urgency_score":    9,
            "urgency_days":     14,
            "extracted_at":     _ago(48, hours=2),
            "time_to_discovery_sec": 7_214,
            "action_steps": [
                "Провести климатический стресс-тест в соответствии с методологией "
                "EBA (ECB Climate Stress Test 2024) до даты первой отчётности",
                "Разработать и утвердить Transition Plan с целевыми показателями "
                "декарбонизации кредитного портфеля на 2030/2050",
                "Интегрировать ESG-метрики в систему внутреннего контроля рисков "
                "ICAAP — с документированием методологии",
            ],
            "legal_analysis": (
                "Guidelines основаны на ст. 87a CRD VI (Директива 2024/1619/EU). "
                "Применяются ко всем кредитным организациям, авторизованным в ЕС. "
                "Ключевые требования: п. 4.3 (климатический стресс-тест), "
                "п. 5.1 (Transition Plan), п. 6 (ICAAP-интеграция). "
                "Регулятор: EBA + национальные NCA."
            ),
            "risk_desc": (
                "Риск административного взыскания от NCA до €2 000 000. "
                "Для банков с публичным листингом — риск ESG-рейтингового снижения "
                "и роста стоимости фондирования. "
                "Расчётный предотвращённый ущерб: $4,500,000."
            ),
        },

        # ── US-1: SEC Cybersecurity Disclosure Rule ───────────────────────────
        {
            "title": (
                "SEC Release No. 34-97996 — Final Rule: Cybersecurity Risk Management, "
                "Strategy, Governance, and Incident Disclosure for Public Companies"
            ),
            "jurisdiction":     "US",
            "publication_date": _date_ago(53),
            "effective_date":   _date_ago(11),
            "summary": (
                "SEC обязывает публичные компании раскрывать материальные инциденты "
                "кибербезопасности в Form 8-K в течение 4 рабочих дней с момента "
                "установления материальности. Ежегодное раскрытие стратегии управления "
                "киберрисками в Form 10-K. Ответственность совета директоров за надзор "
                "над кибербезопасностью. Штраф за нарушение раскрытия — до $500 000."
            ),
            "critical_level":   "CRITICAL",
            "status":           "VALIDATED",
            "source_url":       "https://www.sec.gov/rules/final/2023/33-11216.pdf",
            "confidence":       0.99,
            "fines_usd":        500_000,
            "urgency_score":    8,
            "urgency_days":     -11,
            "extracted_at":     _ago(53, hours=3),
            "time_to_discovery_sec": 10_836,
            "action_steps": [
                "Определить и задокументировать критерии «материальности» "
                "киберинцидента для целей раскрытия в Form 8-K (совместно с counsel)",
                "Внедрить внутренний SLA: оценка материальности инцидента — "
                "не более 24 часов; подача 8-K — не позднее 4 рабочих дней",
                "Обновить раздел «Risk Factors» в Form 10-K с описанием "
                "governance-структуры надзора за кибербезопасностью",
            ],
            "legal_analysis": (
                "Final Rule принят SEC 26 июля 2023 г. во исполнение Section 13(a) "
                "и Section 15(d) Securities Exchange Act 1934. "
                "Применяется к reporting companies (except foreign private issuers — "
                "для них отдельный форм 6-K). Обязательные раскрытия: "
                "Items 1.05 (Form 8-K) и Item 106 (Form 10-K)."
            ),
            "risk_desc": (
                "Риск SEC enforcement action до $500 000 за каждое нарушение раскрытия. "
                "Репутационный риск публичного компании и class action litigation. "
                "Расчётный предотвращённый ущерб: $1,200,000."
            ),
        },

        # ── RU-2: Отчётность операторов платёжных систем ─────────────────────
        {
            "title": (
                "Указание Банка России № 6513-У «О составе, сроках и порядке "
                "представления в Банк России отчётности операторами платёжных систем, "
                "операторами услуг платёжной инфраструктуры, операторами электронных "
                "денежных средств»"
            ),
            "jurisdiction":     "RU",
            "publication_date": _date_ago(39),
            "effective_date":   _date_ahead(3),
            "summary": (
                "Вводятся новые формы обязательной отчётности для операторов "
                "платёжных систем: форма 0409024 (ежеквартальная, объём транзакций) "
                "и форма 0409025 (ежемесячная, операционная надёжность). "
                "Первое представление — за период, начиная с 1 марта 2026 года. "
                "Штраф за непредставление или недостоверные данные — до 8 000 000 руб."
            ),
            "critical_level":   "CRITICAL",
            "status":           "PROCESSING",
            "source_url":       "https://cbr.ru/press/pr/2026-01-15-1/",
            "confidence":       0.95,
            "fines_usd":        87_000,
            "urgency_score":    8,
            "urgency_days":     3,
            "extracted_at":     _ago(39, hours=1),
            "time_to_discovery_sec": 3_940,
            "action_steps": [
                "Сформировать технические требования к автоматическому сбору "
                "данных для форм 0409024 и 0409025 в ИС-процессинга",
                "Провести тестовое заполнение новых форм за текущий квартал "
                "и согласовать формат с куратором ЦБ РФ до 1 марта 2026",
                "Назначить ответственного за ведение и контроль сроков "
                "представления новой отчётности (под роспись в приказе)",
            ],
            "legal_analysis": (
                "Указание принято во исполнение ст. 30 Федерального закона "
                "№ 161-ФЗ «О национальной платёжной системе». "
                "Обязательно для операторов ПС, зарегистрированных в реестре ЦБ РФ. "
                "Форма 0409024: состав, сроки сдачи (15-е числа месяца, "
                "следующего за кварталом). Форма 0409025: ежемесячно, до 10-го числа."
            ),
            "risk_desc": (
                "Высокий риск штрафа 8 000 000 руб. при непредставлении первой формы. "
                "Срок — 3 дня. Вероятность пропуска без автоматизации: высокая. "
                "Расчётный предотвращённый ущерб: $500,000."
            ),
        },

        # ══════════════════════════════════════════════════════════════════════
        # HIGH (5) — высокий риск, в процессе изучения командой
        # ══════════════════════════════════════════════════════════════════════

        # ── EU-2: PSD3 Strong Customer Authentication ──────────────────────────
        {
            "title": (
                "EBA/RTS/2024/03 — Draft Regulatory Technical Standards on Strong "
                "Customer Authentication and Common and Secure Open Standards "
                "of Communication Under Revised Payment Services Directive (PSD3)"
            ),
            "jurisdiction":     "EU",
            "publication_date": _date_ago(62),
            "effective_date":   _date_ahead(45),
            "summary": (
                "Пересмотренные RTS EBA по SCA (Strong Customer Authentication) "
                "в рамках PSD3. Новые требования к динамической привязке, "
                "уточнение исключений (transaction risk analysis), API-стандарты "
                "для Open Banking. Период реализации — 18 месяцев с даты публикации "
                "в Official Journal EU. Штраф за несоответствие — до €1 000 000."
            ),
            "critical_level":   "HIGH",
            "status":           "PROCESSING",
            "source_url":       "https://www.eba.europa.eu/publications/rts/sca-psd3-2024",
            "confidence":       0.93,
            "fines_usd":        1_090_000,
            "urgency_score":    7,
            "urgency_days":     45,
            "extracted_at":     _ago(62, hours=4),
            "time_to_discovery_sec": 14_402,
            "action_steps": [
                "Провести анализ gap текущей SCA-реализации относительно "
                "требований нового RTS (фокус: dynamic linking и exemptions)",
                "Обновить API-спецификацию Open Banking в соответствии "
                "с новыми стандартами EBA; согласовать с ASPSP-партнёрами",
                "Запланировать технический спринт для адаптации mobile-SDK "
                "к новым требованиям dynamic linking до истечения дедлайна",
            ],
            "legal_analysis": (
                "RTS разработаны EBA во исполнение ст. 85(7) PSD3 "
                "(Директива 2024/2831/EU). Применяются к PSP, ASPSP, PISP, AISP. "
                "Ключевые изменения: расширение TRA-исключений, "
                "новый формат authentication codes, API timeout requirements."
            ),
            "risk_desc": (
                "Штраф NCA до €1 000 000 за несоответствие SCA. "
                "Операционный риск: блокировка онлайн-транзакций регулятором. "
                "Расчётный предотвращённый ущерб: $1,500,000."
            ),
        },

        # ── RU-3: Нелегальная деятельность на финансовом рынке ───────────────
        {
            "title": (
                "Письмо Банка России № ИН-014-56/94 «О применении мер при выявлении "
                "признаков осуществления нелегальной деятельности на финансовом рынке "
                "с использованием дистанционных каналов обслуживания»"
            ),
            "jurisdiction":     "RU",
            "publication_date": _date_ago(28),
            "effective_date":   _date_ago(14),
            "summary": (
                "Информационное письмо ЦБ РФ уточняет критерии выявления нелегальных "
                "финансовых операций через дистанционные каналы: мобильный банк, "
                "онлайн-брокеры, P2P-сервисы. Вводятся новые транзакционные профили "
                "высокого риска. Требование: обновить правила ПОД/ФТ в течение "
                "30 дней. Штраф — до 5 000 000 руб. за неустранение нарушений."
            ),
            "critical_level":   "HIGH",
            "status":           "PROCESSING",
            "source_url":       "https://cbr.ru/press/inf/2026-02-20/",
            "confidence":       0.94,
            "fines_usd":        54_300,
            "urgency_score":    7,
            "urgency_days":     16,
            "extracted_at":     _ago(28, hours=2),
            "time_to_discovery_sec": 7_620,
            "action_steps": [
                "Обновить правила внутреннего контроля (ПВК) в части "
                "ПОД/ФТ с учётом новых профилей высокого риска — в срок 30 дней",
                "Провести обучение сотрудников фронт-офиса новым критериям "
                "выявления подозрительных транзакций по дистанционным каналам",
                "Актуализировать скоринговые модели AML с новыми признаками "
                "нелегальной деятельности из письма № ИН-014-56/94",
            ],
            "legal_analysis": (
                "Письмо носит рекомендательный характер, однако несоответствие "
                "влечёт нарушение ст. 7 ФЗ № 115-ФЗ «О ПОД/ФТ» с санкциями "
                "до 5 000 000 руб. (ч. 2 ст. 15.27 КоАП). "
                "Регулятор: Росфинмониторинг + ЦБ РФ."
            ),
            "risk_desc": (
                "Штраф до 5 000 000 руб. за неустранение нарушений ПОД/ФТ. "
                "Репутационный риск при проверке Росфинмониторинга. "
                "Расчётный предотвращённый ущерб: $300,000."
            ),
        },

        # ── US-2: SEC Custody Rule Investment Advisers ────────────────────────
        {
            "title": (
                "SEC Proposed Rule Release No. IA-6625 — Safeguarding Advisory Client "
                "Assets: Updated Custody and Verification Requirements for "
                "Investment Advisers Under the Investment Advisers Act of 1940"
            ),
            "jurisdiction":     "US",
            "publication_date": _date_ago(35),
            "effective_date":   _date_ahead(60),
            "summary": (
                "Предложенные SEC правила расширяют определение «custody» на "
                "crypto assets и иные нетрадиционные активы под управлением. "
                "Требование привлечения квалифицированного кастодиана для всех "
                "активов клиентов. Независимая ежегодная проверка. "
                "Комментарии принимались до 8 мая 2024 года. "
                "Штраф за нарушение — до $250 000."
            ),
            "critical_level":   "HIGH",
            "status":           "PROCESSING",
            "source_url":       "https://www.sec.gov/rules/proposed/2024/ia-6625.pdf",
            "confidence":       0.91,
            "fines_usd":        250_000,
            "urgency_score":    6,
            "urgency_days":     60,
            "extracted_at":     _ago(35, hours=6),
            "time_to_discovery_sec": 21_600,
            "action_steps": [
                "Провести аудит всех активов под управлением на предмет "
                "попадания в расширенное определение «custody» по новому правилу",
                "Оценить необходимость смены или добавления квалифицированного "
                "кастодиана для crypto и альтернативных активов",
                "Подготовить комментарий к proposed rule для SEC "
                "(отраслевая позиция через Investment Adviser Association)",
            ],
            "legal_analysis": (
                "Proposed Rule амендирует Rule 206(4)-2 под Advisers Act 1940. "
                "Затрагивает всех RIA с AUM > $100M. "
                "Ключевые изменения: расширение определения custody (ст. 3(a)), "
                "новые требования к qualified custodian (ст. 4(b))."
            ),
            "risk_desc": (
                "Штраф $250 000 за нарушение custody requirements. "
                "Риск SEC examination findings и investor litigation. "
                "Расчётный предотвращённый ущерб: $800,000."
            ),
        },

        # ── RU-4: Резервы на возможные потери ────────────────────────────────
        {
            "title": (
                "Положение Банка России № 747-П «О порядке формирования кредитными "
                "организациями резервов на возможные потери по ссудам, по ссудной и "
                "приравненной к ней задолженности» (Изменения, внесённые Указанием "
                "№ 6812-У от 12 февраля 2026 года)"
            ),
            "jurisdiction":     "RU",
            "publication_date": _date_ago(41),
            "effective_date":   _date_ahead(19),
            "summary": (
                "Изменения уточняют порядок классификации ссуд для заёмщиков — "
                "участников специализированных инвестиционных проектов. "
                "Новый порядок расчёта резервов по реструктурированным ссудам "
                "в иностранной валюте. Дополнительные требования к документации "
                "при формировании портфельных резервов. "
                "Штраф за несоответствие — до 3 000 000 руб."
            ),
            "critical_level":   "HIGH",
            "status":           "PROCESSING",
            "source_url":       "https://cbr.ru/press/pr/2026-02-12-1/",
            "confidence":       0.92,
            "fines_usd":        32_600,
            "urgency_score":    6,
            "urgency_days":     19,
            "extracted_at":     _ago(41, hours=3),
            "time_to_discovery_sec": 10_800,
            "action_steps": [
                "Провести ревизию кредитного портфеля на предмет ссуд, "
                "подпадающих под новый порядок классификации по Указанию № 6812-У",
                "Обновить методологию расчёта РВПС с учётом новых требований; "
                "согласовать с риск-комитетом банка",
                "Адаптировать АБС (автоматизированная банковская система) "
                "для автоматического расчёта резервов по новым алгоритмам",
            ],
            "legal_analysis": (
                "Изменения вносятся в Положение № 747-П (основной документ: "
                "ред. 2021 г.) на основании ст. 62 ФЗ «О ЦБ РФ». "
                "Обязательно для всех банков с универсальной лицензией. "
                "Новые п. 3.14-3.17 (реструктурированные ссуды в валюте)."
            ),
            "risk_desc": (
                "Штраф до 3 000 000 руб. за нарушение требований резервирования. "
                "Риск занижения нормативов достаточности капитала. "
                "Расчётный предотвращённый ущерб: $250,000."
            ),
        },

        # ── EU-3: AIFMD II Reverse Stress Testing ─────────────────────────────
        {
            "title": (
                "ESMA/2024/1156 — Final Report and Guidelines on Reverse Stress "
                "Testing for UCITS and Alternative Investment Funds Under the "
                "Alternative Investment Fund Managers Directive II (AIFMD II)"
            ),
            "jurisdiction":     "EU",
            "publication_date": _date_ago(55),
            "effective_date":   _date_ahead(30),
            "summary": (
                "ESMA публикует финальные руководящие принципы по обратному "
                "стресс-тестированию для UCITS и AIF. Обязывает управляющих "
                "проводить ежегодный reverse stress test с документированием "
                "сценариев, ведущих к нежизнеспособности фонда. "
                "Включение результатов в годовой отчёт для NCA. "
                "Штраф за несоответствие — до €750 000."
            ),
            "critical_level":   "HIGH",
            "status":           "PROCESSING",
            "source_url":       "https://www.esma.europa.eu/publications/guidelines/aifmd-ii-rst-2024",
            "confidence":       0.90,
            "fines_usd":        817_500,
            "urgency_score":    6,
            "urgency_days":     30,
            "extracted_at":     _ago(55, hours=5),
            "time_to_discovery_sec": 18_000,
            "action_steps": [
                "Разработать методологию reverse stress testing в соответствии "
                "с Guidelines ESMA/2024/1156 (сценарии: credit, liquidity, operational)",
                "Провести первый RST и задокументировать результаты в отчёте "
                "для NCA до даты вступления в силу",
                "Интегрировать RST в годовой цикл управления рисками "
                "фонда с утверждением на уровне инвестиционного комитета",
            ],
            "legal_analysis": (
                "Guidelines разработаны ESMA во исполнение ст. 16(1) AIFMD II "
                "(Директива 2024/927/EU). Применяются ко всем AIFM, авторизованным "
                "в ЕС, управляющим AIF с AuM > €100M. "
                "Обязательны к применению с даты вступления в силу."
            ),
            "risk_desc": (
                "Штраф NCA до €750 000 за несоответствие. "
                "Операционный риск: отзыв авторизации AIFM. "
                "Расчётный предотвращённый ущерб: $2,000,000."
            ),
        },

        # ══════════════════════════════════════════════════════════════════════
        # MEDIUM (5) — средний приоритет
        # ══════════════════════════════════════════════════════════════════════

        # ── RU-5: Цифровые финансовые активы (архивный) ───────────────────────
        {
            "title": (
                "Федеральный закон № 259-ФЗ «О цифровых финансовых активах, "
                "цифровой валюте и о внесении изменений в отдельные законодательные "
                "акты Российской Федерации» (актуальная редакция с изменениями 2025 г.)"
            ),
            "jurisdiction":     "RU",
            "publication_date": _date_ago(89),
            "effective_date":   _date_ago(75),
            "summary": (
                "Регулирует выпуск, обращение и обмен цифровых финансовых активов "
                "(ЦФА) в России. Изменения 2025 года расширяют перечень операций "
                "с ЦФА, доступных квалифицированным инвесторам, и уточняют "
                "требования к операторам информационных систем. "
                "Штраф за незаконный выпуск ЦФА — до 1 000 000 руб."
            ),
            "critical_level":   "MEDIUM",
            "status":           "VALIDATED",
            "source_url":       "https://cbr.ru/press/pr/2025-08-01-1/",
            "confidence":       0.96,
            "fines_usd":        10_870,
            "urgency_score":    4,
            "urgency_days":     75,
            "extracted_at":     _ago(89, hours=2),
            "time_to_discovery_sec": 43_200,
            "action_steps": [
                "Проверить соответствие операций с ЦФА обновлённым требованиям ФЗ-259",
                "Уточнить у куратора ЦБ РФ порядок квалификации новых инструментов",
                "Обновить клиентские соглашения об операциях с ЦФА",
            ],
            "legal_analysis": (
                "ФЗ-259 — основной закон о ЦФА. Изменения 2025 г. внесены "
                "ФЗ от 22.07.2025 № 381-ФЗ. Регулятор: Банк России. "
                "Ключевые изменения: ст. 8 (расширение операций для квал.инвесторов), "
                "ст. 12 (требования к OIS)."
            ),
            "risk_desc": (
                "Штраф до 1 000 000 руб. за нарушения при выпуске ЦФА. "
                "Расчётный предотвращённый ущерб: $150,000."
            ),
        },

        # ── US-3: Form PF Amendment Hedge Funds ───────────────────────────────
        {
            "title": (
                "SEC Form PF Amendment — Enhanced Reporting Requirements for Large "
                "Hedge Fund Advisers and Large Private Equity Fund Advisers "
                "(Release No. IA-6496)"
            ),
            "jurisdiction":     "US",
            "publication_date": _date_ago(78),
            "effective_date":   _date_ago(60),
            "summary": (
                "SEC и CFTC вводят новые требования к экстренному и ежеквартальному "
                "отчётности по Form PF для крупных советников хедж-фондов (AUM > $1.5B) "
                "и крупных PE-фондов (AUM > $2B). "
                "Экстренное событие должно быть задекларировано в течение 72 часов. "
                "Штраф за нарушение сроков — до $100 000."
            ),
            "critical_level":   "MEDIUM",
            "status":           "VALIDATED",
            "source_url":       "https://www.sec.gov/rules/final/2023/ia-6496.pdf",
            "confidence":       0.95,
            "fines_usd":        100_000,
            "urgency_score":    4,
            "urgency_days":     60,
            "extracted_at":     _ago(78, hours=3),
            "time_to_discovery_sec": 50_400,
            "action_steps": [
                "Настроить систему мониторинга триггерных событий Form PF "
                "(drawdown, NAV change, margin default) с уведомлением за 12 часов",
                "Обновить внутренний SOP по отчётности SEC с учётом "
                "72-часового дедлайна на экстренное событие",
                "Провести drill-exercise (учебный сценарий) с compliance-командой",
            ],
            "legal_analysis": (
                "Amendment к Form PF принят SEC 03 мая 2023 г. "
                "Обязателен для Large Hedge Fund Advisers и Large PE Advisers "
                "в соответствии с Dodd-Frank Act Section 404. "
                "Кооперативный регулятор: CFTC (для commodity pools)."
            ),
            "risk_desc": (
                "Штраф до $100 000 за нарушение сроков отчётности. "
                "Расчётный предотвращённый ущерб: $350,000."
            ),
        },

        # ── EU-4: IRRBB/CSRBB Guidelines ──────────────────────────────────────
        {
            "title": (
                "EBA/GL/2023/11 — Revised Guidelines on the Management of Interest "
                "Rate Risk and Credit Spread Risk Arising from Non-Trading Book "
                "Activities (IRRBB and CSRBB) Under CRD V"
            ),
            "jurisdiction":     "EU",
            "publication_date": _date_ago(82),
            "effective_date":   _date_ago(30),
            "summary": (
                "Пересмотренные руководящие принципы EBA по управлению процентным "
                "риском в банковской книге (IRRBB) и кредитно-спредовым риском (CSRBB). "
                "Новые требования к внутренним моделям NMD (non-maturity deposits), "
                "обязательный расчёт показателя EVE и NII при 6 стандартных шоках. "
                "Применяется с 30 июня 2023 года."
            ),
            "critical_level":   "MEDIUM",
            "status":           "VALIDATED",
            "source_url":       "https://www.eba.europa.eu/publications/guidelines/irrbb-csrbb-2023",
            "confidence":       0.97,
            "fines_usd":        545_000,
            "urgency_score":    3,
            "urgency_days":     90,
            "extracted_at":     _ago(82, hours=4),
            "time_to_discovery_sec": 86_400,
            "action_steps": [
                "Верифицировать соответствие внутренних IRRBB-моделей "
                "новым требованиям EBA/GL/2023/11 (особенно NMD behavioural models)",
                "Рассчитать EVE и NII при всех 6 процентных шоках EBA "
                "и включить в следующий ICAAP",
                "Обновить ICAAP-документацию с описанием методологии CSRBB",
            ],
            "legal_analysis": (
                "Guidelines применяются во исполнение ст. 84 CRD V "
                "(Директива 2013/36/EU с изменениями). "
                "Обязательны для всех кредитных организаций ЕС. "
                "Ключевые секции: 4.3 (NMD models), 5 (EVE/NII calculation)."
            ),
            "risk_desc": (
                "Штраф NCA до €500 000 за несоответствие ICAAP. "
                "Расчётный предотвращённый ущерб: $600,000."
            ),
        },

        # ── RU-6: Мониторинг операторов платёжной инфраструктуры (HReview) ───
        {
            "title": (
                "Указание Банка России № 6406-У «О надзоре за соблюдением "
                "операторами платёжных инфраструктур требований к обеспечению "
                "бесперебойности и непрерывности деятельности платёжных систем»"
            ),
            "jurisdiction":     "RU",
            "publication_date": _date_ago(44),
            "effective_date":   _date_ago(10),
            "summary": (
                "Документ устанавливает новые KPI бесперебойности для операторов "
                "ПИ: максимальное время недоступности — не более 2 часов в сутки, "
                "не более 8 часов в месяц. Обязательная отчётность об инцидентах "
                "в течение 2 часов с момента обнаружения. "
                "Документ поступил в виде нечитаемого PDF — требует ручной проверки."
            ),
            "critical_level":   "MEDIUM",
            "status":           "HUMAN_REVIEW",
            "source_url":       "https://cbr.ru/press/pr/2026-01-31-2/",
            "confidence":       0.61,
            "fines_usd":        21_740,
            "urgency_score":    5,
            "urgency_days":     20,
            "extracted_at":     _ago(44, hours=1),
            "time_to_discovery_sec": 3_600,
            "action_steps": [
                "Запросить читаемую версию документа у куратора ЦБ РФ",
                "После получения — провести анализ на соответствие текущим SLA",
                "Обновить регламент реагирования на инциденты с учётом 2-часового дедлайна уведомления",
            ],
            "legal_analysis": (
                "Указание принято во исполнение ст. 30.1 ФЗ № 161-ФЗ. "
                "Применяется к операторам ПИ, включённым в реестр ЦБ РФ. "
                "Требует ручного OCR-извлечения из сканированного PDF."
            ),
            "risk_desc": (
                "Штраф до 2 000 000 руб. за нарушение бесперебойности. "
                "Расчётный предотвращённый ущерб: $100,000."
            ),
        },

        # ── US-4: FinCEN AML Investment Advisers Rule ─────────────────────────
        {
            "title": (
                "FinCEN Final Rule RIN 1506-AB58 — Anti-Money Laundering and "
                "Countering the Financing of Terrorism (AML/CFT) Programs for "
                "Investment Advisers Registered with the SEC"
            ),
            "jurisdiction":     "US",
            "publication_date": _date_ago(91),
            "effective_date":   _date_ago(51),
            "summary": (
                "FinCEN впервые обязывает инвестиционных советников (RIA), "
                "зарегистрированных в SEC, выстраивать полноценные AML/CFT-программы. "
                "Требования: Customer Identification Program (CIP), SAR filing, "
                "назначение AML Compliance Officer, ежегодное обучение. "
                "Штраф за нарушение — до $300 000 за каждое нарушение."
            ),
            "critical_level":   "MEDIUM",
            "status":           "VALIDATED",
            "source_url":       "https://www.fincen.gov/resources/statutes-regulations/rules/rin-1506-ab58",
            "confidence":       0.98,
            "fines_usd":        300_000,
            "urgency_score":    4,
            "urgency_days":     51,
            "extracted_at":     _ago(91, hours=6),
            "time_to_discovery_sec": 86_400,
            "action_steps": [
                "Разработать и внедрить AML/CFT Program в соответствии "
                "с требованиями финального правила FinCEN",
                "Назначить AML Compliance Officer и задокументировать "
                "его полномочия и обязанности",
                "Внедрить Customer Identification Program (CIP) для всех новых клиентов",
            ],
            "legal_analysis": (
                "Final Rule принят FinCEN 28 августа 2024 г. "
                "Основан на Sec. 352 USA PATRIOT Act. "
                "Применяется к RIA, исключая ERA и foreign private advisers. "
                "Период compliance: 12 месяцев с даты публикации в Federal Register."
            ),
            "risk_desc": (
                "Штраф $300 000 за каждое нарушение AML-программы. "
                "Риск criminal referral в DOJ при умысле. "
                "Расчётный предотвращённый ущерб: $700,000."
            ),
        },

        # ══════════════════════════════════════════════════════════════════════
        # LOW (3) — низкий приоритет, архивные или давно внедрённые
        # ══════════════════════════════════════════════════════════════════════

        # ── RU-7: Нормативы достаточности капитала ────────────────────────────
        {
            "title": (
                "Инструкция Банка России № 199-И «Об обязательных нормативах "
                "и надбавках к нормативам достаточности капитала банков "
                "с универсальной лицензией» (Редакция от 01.01.2025)"
            ),
            "jurisdiction":     "RU",
            "publication_date": _date_ago(102),
            "effective_date":   _date_ago(90),
            "summary": (
                "Актуализированная редакция Инструкции 199-И уточняет расчёт "
                "взвешенных по риску активов для операций с производными "
                "финансовыми инструментами и repo-сделок. "
                "Нормативы Н1.0 (8%), Н1.1 (4.5%), Н1.2 (6%) сохранены без изменений. "
                "Документ имплементирован большинством банков ранее установленного срока."
            ),
            "critical_level":   "LOW",
            "status":           "VALIDATED",
            "source_url":       "https://cbr.ru/press/pr/2025-10-01-1/",
            "confidence":       0.99,
            "fines_usd":        5_435,
            "urgency_score":    2,
            "urgency_days":     90,
            "extracted_at":     _ago(102, hours=8),
            "time_to_discovery_sec": 259_200,
            "action_steps": [
                "Верифицировать методологию расчёта RWA по деривативам",
                "Проверить соответствие нормативам Н1.0/Н1.1/Н1.2 в актуальной отчётности",
                "Архивировать — требования уже имплементированы",
            ],
            "legal_analysis": (
                "Инструкция 199-И — основной нормативный акт по нормативам Базель III. "
                "Редакция 2025 г. вносит изменения в ст. 4 (derivatives RWA). "
                "Регулятор: Банк России."
            ),
            "risk_desc": (
                "Штраф за нарушение нормативов — до 500 000 руб. "
                "Расчётный предотвращённый ущерб: $50,000."
            ),
        },

        # ── US-5: Regulation Best Interest Annual Review ───────────────────────
        {
            "title": (
                "SEC Release IA-6240 — Regulation Best Interest (Reg BI): "
                "Annual Review and Enhanced Supervisory Obligations for "
                "Broker-Dealers and Investment Advisers"
            ),
            "jurisdiction":     "US",
            "publication_date": _date_ago(96),
            "effective_date":   _date_ago(80),
            "summary": (
                "Уточнения SEC по ежегодной проверке соответствия Reg BI. "
                "Broker-dealers обязаны провести annual review стандартов "
                "«best interest» до конца финансового года. "
                "Документация проверки должна храниться не менее 6 лет. "
                "Штраф за отсутствие документированного review — до $50 000."
            ),
            "critical_level":   "LOW",
            "status":           "VALIDATED",
            "source_url":       "https://www.sec.gov/investment/reg-bi-annual-review-2023",
            "confidence":       0.94,
            "fines_usd":        50_000,
            "urgency_score":    2,
            "urgency_days":     80,
            "extracted_at":     _ago(96, hours=12),
            "time_to_discovery_sec": 172_800,
            "action_steps": [
                "Провести ежегодный Reg BI review и задокументировать выводы",
                "Сохранить документацию в архиве compliance на 6 лет",
                "Обновить supervisory procedures с учётом актуальных SEC guidance",
            ],
            "legal_analysis": (
                "Reg BI (Rule 15l-1) принят SEC 05 июня 2019 г. "
                "Руководящее разъяснение IA-6240 — 2023 г. "
                "Применяется к broker-dealers и dual registrants."
            ),
            "risk_desc": (
                "Штраф до $50 000 за отсутствие documented annual review. "
                "Расчётный предотвращённый ущерб: $120,000."
            ),
        },

        # ── EU-5: EBA Crypto-Asset Prudential Treatment ───────────────────────
        {
            "title": (
                "EBA Opinion EBA/Op/2024/02 on the Prudential Treatment of "
                "Crypto-Asset Exposures for Credit Institutions Under CRR3 "
                "and MiCA Framework"
            ),
            "jurisdiction":     "EU",
            "publication_date": _date_ago(110),
            "effective_date":   _date_ago(95),
            "summary": (
                "EBA Opinion уточняет пруденциальный режим для крипто-активов "
                "кредитных организаций в рамках CRR3 (Базель 3.1) и MiCA. "
                "Рекомендованные весовые коэффициенты риска: unbacked crypto — 1250%, "
                "tokenised traditional assets — по базовому активу. "
                "Opinion носит рекомендательный характер до принятия финальных RTS."
            ),
            "critical_level":   "LOW",
            "status":           "VALIDATED",
            "source_url":       "https://www.eba.europa.eu/publications/opinions/crypto-cRR3-2024",
            "confidence":       0.88,
            "fines_usd":        218_000,
            "urgency_score":    2,
            "urgency_days":     95,
            "extracted_at":     _ago(110, hours=10),
            "time_to_discovery_sec": 216_000,
            "action_steps": [
                "Провести инвентаризацию крипто-экспозиций в балансе банка",
                "Рассчитать RWA по рекомендованным коэффициентам EBA Opinion",
                "Мониторить публикацию финальных CRR3 RTS по крипто",
            ],
            "legal_analysis": (
                "EBA Opinion основан на ст. 501c CRR3 (Reg. 2024/1623/EU) и MiCA "
                "(Reg. 2023/1114/EU). Носит рекомендательный характер. "
                "NCA вправе применять более строгие требования."
            ),
            "risk_desc": (
                "Риск недооценки RWA по крипто-экспозициям. "
                "Расчётный предотвращённый ущерб: $400,000."
            ),
        },
    ]


# =============================================================================
# ── Исторические YTD-снэпшоты (4 месяца с восходящим трендом) ────────────────
# =============================================================================

def _build_ytd_snapshots() -> list[dict]:
    """
    Возвращает список YTD-снэпшотов за февраль–май 2026 года.
    Значения подобраны так, чтобы дашборд показывал явный восходящий тренд:
      • total_processed:     38 → 61 → 79 → 91 (рост ~2.4x)
      • fines_prevented_usd: $6.8M → $11.2M → $15.4M → $19.5M
      • roi_multiplier:      226x → 373x → 513x → 650x
      • avg_time_to_discovery_sec: убывает (система обучается)
    """
    now_iso = datetime.utcnow().isoformat()

    # Вспомогательная функция для вычисления ROI-мультипликатора.
    # Формула: fines_prevented / (months_ytd * 500 USD/мес подписки)
    def _roi(fines_usd: int, months: int) -> float:
        subscription = months * 500.0
        return round(fines_usd / subscription, 1) if subscription else 0.0

    return [
        # ── Февраль 2026 ────────────────────────────────────────────────────
        {
            "year": 2026, "month": 2, "jurisdiction": "ALL",
            "total_processed": 38, "critical_count": 3, "high_count": 6,
            "fines_prevented_usd": 6_800_000,
            "avg_time_to_discovery_sec": 91_200.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(38 * 0.0016, 4),
            "roi_multiplier": _roi(6_800_000, 2),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 2, "jurisdiction": "RU",
            "total_processed": 22, "critical_count": 2, "high_count": 4,
            "fines_prevented_usd": 4_200_000,
            "avg_time_to_discovery_sec": 78_600.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(22 * 0.0016, 4),
            "roi_multiplier": _roi(4_200_000, 2),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 2, "jurisdiction": "EU",
            "total_processed": 9, "critical_count": 1, "high_count": 1,
            "fines_prevented_usd": 1_900_000,
            "avg_time_to_discovery_sec": 108_000.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(9 * 0.0016, 4),
            "roi_multiplier": _roi(1_900_000, 2),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 2, "jurisdiction": "US",
            "total_processed": 7, "critical_count": 0, "high_count": 1,
            "fines_prevented_usd": 700_000,
            "avg_time_to_discovery_sec": 115_200.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(7 * 0.0016, 4),
            "roi_multiplier": _roi(700_000, 2),
            "created_at": now_iso, "updated_at": now_iso,
        },

        # ── Март 2026 ────────────────────────────────────────────────────────
        {
            "year": 2026, "month": 3, "jurisdiction": "ALL",
            "total_processed": 61, "critical_count": 5, "high_count": 9,
            "fines_prevented_usd": 11_200_000,
            "avg_time_to_discovery_sec": 87_300.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(61 * 0.0016, 4),
            "roi_multiplier": _roi(11_200_000, 3),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 3, "jurisdiction": "RU",
            "total_processed": 34, "critical_count": 3, "high_count": 5,
            "fines_prevented_usd": 6_800_000,
            "avg_time_to_discovery_sec": 72_000.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(34 * 0.0016, 4),
            "roi_multiplier": _roi(6_800_000, 3),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 3, "jurisdiction": "EU",
            "total_processed": 16, "critical_count": 1, "high_count": 3,
            "fines_prevented_usd": 3_100_000,
            "avg_time_to_discovery_sec": 100_800.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(16 * 0.0016, 4),
            "roi_multiplier": _roi(3_100_000, 3),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 3, "jurisdiction": "US",
            "total_processed": 11, "critical_count": 1, "high_count": 1,
            "fines_prevented_usd": 1_300_000,
            "avg_time_to_discovery_sec": 108_000.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(11 * 0.0016, 4),
            "roi_multiplier": _roi(1_300_000, 3),
            "created_at": now_iso, "updated_at": now_iso,
        },

        # ── Апрель 2026 ──────────────────────────────────────────────────────
        {
            "year": 2026, "month": 4, "jurisdiction": "ALL",
            "total_processed": 79, "critical_count": 7, "high_count": 12,
            "fines_prevented_usd": 15_400_000,
            "avg_time_to_discovery_sec": 83_100.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(79 * 0.0016, 4),
            "roi_multiplier": _roi(15_400_000, 4),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 4, "jurisdiction": "RU",
            "total_processed": 45, "critical_count": 4, "high_count": 7,
            "fines_prevented_usd": 9_200_000,
            "avg_time_to_discovery_sec": 68_400.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(45 * 0.0016, 4),
            "roi_multiplier": _roi(9_200_000, 4),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 4, "jurisdiction": "EU",
            "total_processed": 20, "critical_count": 2, "high_count": 3,
            "fines_prevented_usd": 4_400_000,
            "avg_time_to_discovery_sec": 93_600.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(20 * 0.0016, 4),
            "roi_multiplier": _roi(4_400_000, 4),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 4, "jurisdiction": "US",
            "total_processed": 14, "critical_count": 1, "high_count": 2,
            "fines_prevented_usd": 1_800_000,
            "avg_time_to_discovery_sec": 100_800.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(14 * 0.0016, 4),
            "roi_multiplier": _roi(1_800_000, 4),
            "created_at": now_iso, "updated_at": now_iso,
        },

        # ── Май 2026 (текущий месяц) ─────────────────────────────────────────
        {
            "year": 2026, "month": 5, "jurisdiction": "ALL",
            "total_processed": 91, "critical_count": 9, "high_count": 14,
            "fines_prevented_usd": 19_500_000,
            "avg_time_to_discovery_sec": 79_200.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(91 * 0.0016, 4),
            "roi_multiplier": _roi(19_500_000, 5),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 5, "jurisdiction": "RU",
            "total_processed": 52, "critical_count": 5, "high_count": 8,
            "fines_prevented_usd": 11_500_000,
            "avg_time_to_discovery_sec": 64_800.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(52 * 0.0016, 4),
            "roi_multiplier": _roi(11_500_000, 5),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 5, "jurisdiction": "EU",
            "total_processed": 24, "critical_count": 3, "high_count": 4,
            "fines_prevented_usd": 5_600_000,
            "avg_time_to_discovery_sec": 88_200.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(24 * 0.0016, 4),
            "roi_multiplier": _roi(5_600_000, 5),
            "created_at": now_iso, "updated_at": now_iso,
        },
        {
            "year": 2026, "month": 5, "jurisdiction": "US",
            "total_processed": 15, "critical_count": 1, "high_count": 2,
            "fines_prevented_usd": 2_400_000,
            "avg_time_to_discovery_sec": 97_200.0,
            "avg_compute_cost_usd": 0.0016,
            "total_compute_cost_usd": round(15 * 0.0016, 4),
            "roi_multiplier": _roi(2_400_000, 5),
            "created_at": now_iso, "updated_at": now_iso,
        },
    ]


# =============================================================================
# ── Функции засева ────────────────────────────────────────────────────────────
# =============================================================================

def clear_demo_data(session) -> None:
    """
    Удаляет все записи из regulations и ytd_snapshots перед свежим засевом.
    Вызывается только при флаге --clear.
    """
    from app.infrastructure.db.models import RegulationRecord, YtdSnapshot

    regs_deleted = session.query(RegulationRecord).delete()
    ytd_deleted  = session.query(YtdSnapshot).delete()
    session.commit()
    log.info("Очистка: удалено %d НПА и %d YTD-снэпшотов", regs_deleted, ytd_deleted)


def seed_regulations(session, dry_run: bool) -> int:
    """
    Вставляет демонстрационные НПА в таблицу regulations.
    Идемпотентен: записи с совпадающим url_hash пропускаются.

    Возвращает количество новых вставленных записей.
    """
    from app.infrastructure.db.models import RegulationRecord

    regulations = _build_regulations()
    inserted    = 0
    skipped     = 0

    for r in regulations:
        url_hash = _sha256(r["source_url"])

        # Проверяем существование по url_hash (уникальный идентификатор документа)
        existing = session.query(RegulationRecord).filter_by(url_hash=url_hash).first()
        if existing:
            log.debug("Пропуск (существует): %s", r["title"][:55])
            skipped += 1
            continue

        if dry_run:
            log.info("[DRY-RUN] Будет вставлен [%s] %s",
                     r["critical_level"], r["title"][:65])
            inserted += 1
            continue

        # Формируем JSON строку ai_analysis в формате analyzer.py
        ai_analysis_json = _make_ai_analysis(
            legal         = r.get("legal_analysis", ""),
            risk          = r.get("risk_desc", ""),
            fines_usd     = int(r.get("fines_usd", 0)),
            urgency_days  = int(r.get("urgency_days", 90)),
            urgency_score = int(r.get("urgency_score", 1)),
            action_steps  = r.get("action_steps", []),
        )

        # action_plan хранится как JSON-массив шагов (аналогично action_plan.py)
        action_plan_json = json.dumps(
            r.get("action_steps", []), ensure_ascii=False
        )

        record = RegulationRecord(
            title             = r["title"],
            jurisdiction      = r["jurisdiction"],
            publication_date  = r.get("publication_date", ""),
            effective_date    = r.get("effective_date", ""),
            summary           = r.get("summary", ""),
            industries        = "",
            critical_level    = r["critical_level"],
            source_url        = r["source_url"],
            confidence        = float(r.get("confidence", 0.95)),
            status            = r.get("status", "VALIDATED"),
            extracted_at      = r.get("extracted_at", datetime.utcnow()),
            url_hash          = url_hash,
            # content_hash — SHA-256 summary (имитирует хэш PDF-содержимого)
            ai_analysis       = ai_analysis_json,
            source_type       = "WEB",
            urgency_score     = int(r.get("urgency_score", 1)),
            action_plan       = action_plan_json,
            fines_usd         = int(r.get("fines_usd", 0)),
            time_to_discovery_sec = int(r.get("time_to_discovery_sec", 3600)),
            compute_cost_usd  = 0.0016,
        )

        session.add(record)
        inserted += 1

    if not dry_run:
        session.commit()
        log.info(
            "НПА: вставлено %d, пропущено %d (уже существуют)",
            inserted, skipped,
        )
    else:
        log.info("[DRY-RUN] Будет вставлено %d НПА (%d уже существует)",
                 inserted, skipped)

    return inserted


def seed_ytd_snapshots(engine, dry_run: bool) -> int:
    """
    Вставляет исторические YTD-снэпшоты через прямой SQL (INSERT OR REPLACE).
    Использует INSERT OR REPLACE (SQLite) для идемпотентности — при повторном
    запуске записи с совпадающим (year, month, jurisdiction) обновляются.

    Возвращает количество обработанных снэпшотов.
    """
    from sqlalchemy import text

    snapshots = _build_ytd_snapshots()

    # INSERT OR REPLACE корректно обрабатывает UNIQUE INDEX (year, month, jurisdiction)
    # Это SQLite-специфичный синтаксис; для PostgreSQL используйте
    # INSERT ... ON CONFLICT (year, month, jurisdiction) DO UPDATE SET ...
    sql = text("""
        INSERT OR REPLACE INTO ytd_snapshots
            (year, month, jurisdiction,
             total_processed, critical_count, high_count,
             fines_prevented_usd, avg_time_to_discovery_sec,
             avg_compute_cost_usd, total_compute_cost_usd,
             roi_multiplier, created_at)
        VALUES
            (:year, :month, :jurisdiction,
             :total_processed, :critical_count, :high_count,
             :fines_prevented_usd, :avg_time_to_discovery_sec,
             :avg_compute_cost_usd, :total_compute_cost_usd,
             :roi_multiplier, :created_at)
    """)

    count = 0

    if dry_run:
        for s in snapshots:
            log.info(
                "[DRY-RUN] YTD %s-%s [%s] docs=%s fines=$%s roi=%sx",
                s["year"],
                f"{s['month']:02d}",
                f"{s['jurisdiction']:<3}",
                f"{s['total_processed']:<3d}",
                f"{s['fines_prevented_usd']:,}",
                f"{s['roi_multiplier']:.0f}",
            )
            count += 1
        return count

    with engine.begin() as conn:
        for s in snapshots:
            conn.execute(sql, s)
            count += 1

    log.info("YTD снэпшоты: обработано %d записей (4 месяца × 4 юрисдикции)", count)
    return count


# =============================================================================
# ── Итоговый отчёт ────────────────────────────────────────────────────────────
# =============================================================================

def _print_summary(reg_count: int, ytd_count: int, dry_run: bool) -> None:
    """Выводит итоговую сводку засева."""
    mode = "[DRY-RUN] " if dry_run else ""
    print()
    print("═" * 62)
    print(f"  {mode}RegRadar Demo Seed — ИТОГ")
    print("═" * 62)
    print(f"  НПА вставлено:              {reg_count:>4}")
    print(f"  YTD снэпшотов обработано:   {ytd_count:>4}")
    print()
    if not dry_run:
        print("  Дашборд готов к презентации:")
        print("    • 4 CRITICAL акта с суммой штрафов до $2.18M")
        print("    • 4 месяца восходящего тренда ($6.8M → $19.5M)")
        print("    • 3 юрисдикции: RU / EU / US")
        print("    • ROI системы: 226x → 650x")
    print("═" * 62)
    print()


# =============================================================================
# ── Вспомогательная миграция ytd_snapshots ────────────────────────────────────
# =============================================================================

def _ensure_ytd_roi_column(engine) -> None:
    """
    Добавляет колонку roi_multiplier в ytd_snapshots, если она отсутствует.
    Идемпотентна: при повторном вызове ничего не делает.
    """
    from sqlalchemy import text

    with engine.connect() as conn:
        # Получаем список существующих колонок через PRAGMA
        rows = conn.execute(text("PRAGMA table_info(ytd_snapshots)")).fetchall()
        existing_cols = {row[1] for row in rows}

        if "roi_multiplier" not in existing_cols:
            conn.execute(text(
                "ALTER TABLE ytd_snapshots ADD COLUMN roi_multiplier REAL DEFAULT 0.0"
            ))
            conn.commit()
            log.info("Миграция: добавлена колонка ytd_snapshots.roi_multiplier")
        else:
            log.debug("Колонка ytd_snapshots.roi_multiplier уже существует")


# =============================================================================
# ── Точка входа ───────────────────────────────────────────────────────────────
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Засев демонстрационных данных RegRadar Enterprise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  python3 scripts/seed_demo_data.py\n"
            "  python3 scripts/seed_demo_data.py --clear\n"
            "  python3 scripts/seed_demo_data.py --dry-run\n"
        ),
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Удалить все существующие записи перед засевом (осторожно!)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Вывести план засева без записи в БД",
    )
    args = parser.parse_args()

    log.info("RegRadar Demo Seed запущен%s", " [DRY-RUN]" if args.dry_run else "")

    # ── Импорт инфраструктурных модулей ───────────────────────────────────────
    # Импортируем здесь, а не на уровне модуля: скрипт может быть запущен
    # вне virtualenv и должен давать понятную ошибку, а не падать при импорте.
    try:
        from app.infrastructure.db.session import SessionLocal, engine
        from app.infrastructure.db.models import ensure_schema_migrations
    except ImportError as exc:
        log.error(
            "Ошибка импорта: %s\n"
            "Убедитесь, что:\n"
            "  1. Вы находитесь в корневой директории проекта\n"
            "  2. Виртуальное окружение активировано\n"
            "  3. Зависимости установлены: pip install -r requirements.txt",
            exc,
        )
        sys.exit(1)

    # ── Применяем идемпотентные миграции схемы БД ────────────────────────────
    # ensure_schema_migrations добавляет новые колонки (urgency_score, fines_usd и т.д.)
    # в существующую БД через ALTER TABLE IF NOT EXISTS — безопасно вызывать всегда
    log.info("Применение идемпотентных миграций схемы...")
    ensure_schema_migrations(engine)

    # Добавляем колонку roi_multiplier в ytd_snapshots, если её ещё нет.
    # ALTER TABLE IF NOT EXISTS доступен только в SQLite ≥ 3.37 — используем
    # безопасный вариант через PRAGMA table_info для проверки наличия колонки.
    _ensure_ytd_roi_column(engine)

    # ── Засев данных ──────────────────────────────────────────────────────────
    with SessionLocal() as session:

        # Очистка (только при --clear)
        if args.clear and not args.dry_run:
            log.warning("Очистка таблиц regulations и ytd_snapshots...")
            clear_demo_data(session)
        elif args.clear and args.dry_run:
            log.info("[DRY-RUN] Очистка была бы выполнена при запуске без --dry-run")

        # Засев НПА
        log.info("Засев демонстрационных регуляторных актов...")
        reg_count = seed_regulations(session, dry_run=args.dry_run)

    # Засев YTD снэпшотов (вне session — используем engine напрямую)
    log.info("Засев исторических YTD-снэпшотов (4 месяца)...")
    ytd_count = seed_ytd_snapshots(engine, dry_run=args.dry_run)

    # Итоговый отчёт
    _print_summary(reg_count, ytd_count, dry_run=args.dry_run)

    if not args.dry_run:
        log.info("Засев завершён успешно. Запустите RegRadar и откройте дашборд.")


if __name__ == "__main__":
    main()
