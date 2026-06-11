import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.core.domain.models import RegulationModel
from .models import AlertSubscription, RegulationRecord, RegulationVersion, Regulator
from .session import SessionLocal

log = logging.getLogger(__name__)


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


class VersionedUpsertResult(NamedTuple):
    saved:       bool
    is_update:   bool
    old_summary: str | None
    version_id:  int | None
    record_id:   int


class RegulationRepository:
    def upsert(self, reg: RegulationModel) -> bool:
        h = _url_hash(reg.source_url)
        with SessionLocal() as db:
            existing = db.query(RegulationRecord).filter_by(url_hash=h).first()
            if existing:
                return False
            record = RegulationRecord(
                title=reg.title,
                jurisdiction=reg.jurisdiction.value,
                publication_date=str(reg.publication_date),
                effective_date=str(reg.effective_date),
                summary=reg.summary,
                industries=",".join(reg.industries),
                critical_level=reg.critical_level.value,
                source_url=reg.source_url,
                confidence=reg.confidence,
                status=reg.status.value,
                extracted_at=reg.extracted_at,
                url_hash=h,
            )
            db.add(record)
            db.commit()
            log.info("Saved: %s", reg.title[:60])
            return True

    def list_recent(self, days: int = 30, jurisdiction: str = None, level: str = None) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with SessionLocal() as db:
            q = db.query(RegulationRecord).filter(RegulationRecord.extracted_at >= cutoff)
            if jurisdiction:
                q = q.filter(RegulationRecord.jurisdiction == jurisdiction)
            if level:
                q = q.filter(RegulationRecord.critical_level == level)
            rows = q.order_by(RegulationRecord.extracted_at.desc()).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "jurisdiction": r.jurisdiction,
                "effective_date": r.effective_date,
                "critical_level": r.critical_level,
                "summary": r.summary,
                "confidence": r.confidence,
                "status": r.status,
                "source_url": r.source_url,
            }
            for r in rows
        ]

    def upsert_raw(self, data: dict) -> bool:
        """Insert a raw dict (e.g. from Telegram monitor) without Pydantic validation."""
        h = _url_hash(data["source_url"])
        with SessionLocal() as db:
            if db.query(RegulationRecord).filter_by(url_hash=h).first():
                return False
            record = RegulationRecord(
                title=data.get("title", "")[:500],
                jurisdiction=data.get("jurisdiction", ""),
                publication_date=data.get("publication_date", ""),
                effective_date=data.get("effective_date", ""),
                summary=data.get("summary", ""),
                industries=data.get("industries", ""),
                critical_level=data.get("critical_level", "MEDIUM"),
                source_url=data["source_url"],
                confidence=float(data.get("confidence", 0.5)),
                status=data.get("status", "HUMAN_REVIEW"),
                source_type=data.get("source_type", "WEB"),
                extracted_at=datetime.utcnow(),
                url_hash=h,
            )
            db.add(record)
            db.commit()
            log.info("Saved raw: %s", data.get("title", "")[:60])
            return True

    def upsert_raw_versioned(self, data: dict) -> VersionedUpsertResult:
        """
        Insert or version-update a regulation.
        Creates a RegulationVersion record on every content change (detected via SHA-256 of summary).
        Returns VersionedUpsertResult with is_update=True when an existing record changed.
        Caller should dispatch analyze_delta_task when is_update=True and version_id is set.
        """
        h       = _url_hash(data["source_url"])
        summary = data.get("summary", "") or ""
        s_hash  = hashlib.sha256(summary.encode()).hexdigest()

        with SessionLocal() as db:
            existing = db.query(RegulationRecord).filter_by(url_hash=h).first()

            if not existing:
                record = RegulationRecord(
                    title=data.get("title", "")[:500],
                    jurisdiction=data.get("jurisdiction", ""),
                    publication_date=data.get("publication_date", ""),
                    effective_date=data.get("effective_date", ""),
                    summary=summary,
                    industries=data.get("industries", ""),
                    critical_level=data.get("critical_level", "MEDIUM"),
                    source_url=data["source_url"],
                    confidence=float(data.get("confidence", 0.5)),
                    status=data.get("status", "HUMAN_REVIEW"),
                    source_type=data.get("source_type", "WEB"),
                    extracted_at=datetime.utcnow(),
                    url_hash=h,
                )
                db.add(record)
                db.flush()
                version = RegulationVersion(
                    regulation_id=record.id,
                    version_number=1,
                    summary_hash=s_hash,
                    summary=summary,
                )
                db.add(version)
                db.commit()
                log.info("upsert_raw_versioned: new %s", data.get("title", "")[:60])
                return VersionedUpsertResult(
                    saved=True, is_update=False, old_summary=None,
                    version_id=version.id, record_id=record.id,
                )

            latest = (
                db.query(RegulationVersion)
                .filter_by(regulation_id=existing.id)
                .order_by(RegulationVersion.version_number.desc())
                .first()
            )
            if latest and latest.summary_hash == s_hash:
                return VersionedUpsertResult(
                    saved=False, is_update=False, old_summary=existing.summary,
                    version_id=None, record_id=existing.id,
                )

            old_summary  = existing.summary
            next_ver_num = (latest.version_number + 1) if latest else 1
            existing.summary = summary
            version = RegulationVersion(
                regulation_id=existing.id,
                version_number=next_ver_num,
                summary_hash=s_hash,
                summary=summary,
            )
            db.add(version)
            db.commit()
            log.info(
                "upsert_raw_versioned: updated v%d %s",
                next_ver_num, data.get("title", "")[:60],
            )
            return VersionedUpsertResult(
                saved=True, is_update=True, old_summary=old_summary,
                version_id=version.id, record_id=existing.id,
            )

    def update_version_delta(self, version_id: int, delta) -> None:
        """Store serialised DeltaAnalysis and impact_level on a RegulationVersion row."""
        with SessionLocal() as db:
            version = db.query(RegulationVersion).filter_by(id=version_id).first()
            if version:
                version.delta_json   = delta.model_dump_json()
                version.impact_level = delta.impact_level
                db.commit()

    def get_version_by_id(self, version_id: int) -> dict | None:
        with SessionLocal() as db:
            v = db.query(RegulationVersion).filter_by(id=version_id).first()
            if not v:
                return None
            return {"id": v.id, "summary": v.summary, "regulation_id": v.regulation_id}

    def get_versions(self, regulation_id: int) -> list[dict]:
        with SessionLocal() as db:
            rows = (
                db.query(RegulationVersion)
                .filter_by(regulation_id=regulation_id)
                .order_by(RegulationVersion.version_number.asc())
                .all()
            )
            return [
                {
                    "id":             r.id,
                    "version_number": r.version_number,
                    "summary_hash":   r.summary_hash[:12],
                    "summary":        r.summary,
                    "delta_json":     r.delta_json,
                    "impact_level":   r.impact_level,
                    "created_at":     r.created_at,
                }
                for r in rows
            ]

    def get_recent_with_versions(self, since: datetime) -> list[dict]:
        """Return regulations that got a new analyzed version since cutoff."""
        from sqlalchemy import text
        with SessionLocal() as db:
            rows = db.execute(text("""
                SELECT r.id, r.title, r.jurisdiction, r.critical_level, r.summary,
                       r.source_url, v.delta_json, v.impact_level
                FROM regulation_versions v
                JOIN regulations r ON r.id = v.regulation_id
                WHERE v.created_at >= :since AND v.delta_json IS NOT NULL
                ORDER BY v.created_at DESC
            """), {"since": since.isoformat()}).fetchall()
        return [
            {
                "id":             row[0],
                "title":          row[1],
                "jurisdiction":   row[2],
                "critical_level": row[3],
                "summary":        row[4],
                "source_url":     row[5],
                "delta_json":     row[6],
                "impact_level":   row[7] or row[3],
            }
            for row in rows
        ]

    def get_regulators(self) -> list[Regulator]:
        with SessionLocal() as db:
            return db.query(Regulator).filter_by(active=True).all()


# ── Subscription repository ───────────────────────────────────────────────────

class SubscriptionRepository:
    def subscribe(
        self,
        chat_id:        str,
        jurisdictions:  str = "",
        frequency:      str = "daily",
        min_risk_level: str = "LOW",
    ) -> bool:
        """Create or update a Telegram subscription. Returns True if new."""
        with SessionLocal() as db:
            existing = db.query(AlertSubscription).filter_by(chat_id=chat_id).first()
            if existing:
                existing.jurisdictions  = jurisdictions
                existing.frequency      = frequency
                existing.min_risk_level = min_risk_level
                existing.is_active      = True
                db.commit()
                return False
            sub = AlertSubscription(
                chat_id=chat_id,
                jurisdictions=jurisdictions,
                frequency=frequency,
                min_risk_level=min_risk_level,
            )
            db.add(sub)
            db.commit()
            return True

    def list_active(self) -> list[AlertSubscription]:
        with SessionLocal() as db:
            return db.query(AlertSubscription).filter_by(is_active=True).all()

    def update_last_notified(self, chat_ids: list[str]) -> None:
        if not chat_ids:
            return
        with SessionLocal() as db:
            db.query(AlertSubscription).filter(
                AlertSubscription.chat_id.in_(chat_ids)
            ).update({"last_notified_at": datetime.utcnow()}, synchronize_session=False)
            db.commit()
