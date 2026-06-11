"""Single-file database layer: models + session + repositories."""
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, Integer, String, Text,
    create_engine, event, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from config import settings


# ── Engine ────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=5,
    max_overflow=10,
)


@event.listens_for(engine, "connect")
def _on_connect(conn, _):
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ── Models ────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


class Regulator(Base):
    __tablename__ = "regulators"
    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    name: Mapped[str]        = mapped_column(String(200), nullable=False)
    jurisdiction: Mapped[str]= mapped_column(String(5),  nullable=False)
    base_url: Mapped[str]    = mapped_column(Text,       nullable=False)
    strategy: Mapped[str]    = mapped_column(String(20), default="STATIC")
    link_pattern: Mapped[str]= mapped_column(String(50), default=".pdf")
    active: Mapped[bool]     = mapped_column(Boolean,    default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RegulationRecord(Base):
    __tablename__ = "regulations"
    id: Mapped[int]              = mapped_column(Integer,   primary_key=True)
    title: Mapped[str]           = mapped_column(Text,      nullable=False)
    jurisdiction: Mapped[str]    = mapped_column(String(5), nullable=False, index=True)
    publication_date: Mapped[str]= mapped_column(String(10))
    effective_date: Mapped[str]  = mapped_column(String(10))
    summary: Mapped[str]         = mapped_column(Text,      default="")
    industries: Mapped[str]      = mapped_column(Text,      default="")
    critical_level: Mapped[str]  = mapped_column(String(20),default="LOW", index=True)
    source_url: Mapped[str]      = mapped_column(Text)
    confidence: Mapped[float]    = mapped_column(Float,     default=0.5)
    status: Mapped[str]          = mapped_column(String(20),default="PROCESSING")
    extracted_at: Mapped[datetime]= mapped_column(DateTime, default=datetime.utcnow, index=True)
    url_hash: Mapped[str]        = mapped_column(String(64),unique=True, index=True)


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"
    id: Mapped[int]             = mapped_column(Integer,    primary_key=True)
    regulator_name: Mapped[str] = mapped_column(String(200))
    jurisdiction: Mapped[str]   = mapped_column(String(5))
    status: Mapped[str]         = mapped_column(String(20), default="PENDING")
    docs_found: Mapped[int]     = mapped_column(Integer,    default=0)
    docs_saved: Mapped[int]     = mapped_column(Integer,    default=0)
    error_msg: Mapped[Optional[str]] = mapped_column(Text,  nullable=True)
    started_at: Mapped[datetime]= mapped_column(DateTime,   default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


# ── Helpers ───────────────────────────────────────────────────────
def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def get_session() -> Session:
    return SessionLocal()


# ── Repositories ──────────────────────────────────────────────────
class RegulationRepo:
    def upsert(self, data: dict) -> bool:
        h = _url_hash(data["source_url"])
        with get_session() as db:
            if db.query(RegulationRecord).filter_by(url_hash=h).first():
                return False
            db.add(RegulationRecord(**data, url_hash=h))
            db.commit()
            return True

    def list_recent(
        self,
        days: int = 30,
        jurisdiction: Optional[str] = None,
        level: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with get_session() as db:
            q = db.query(RegulationRecord).filter(RegulationRecord.extracted_at >= cutoff)
            if jurisdiction:
                q = q.filter(RegulationRecord.jurisdiction == jurisdiction)
            if level:
                q = q.filter(RegulationRecord.critical_level == level)
            if status:
                q = q.filter(RegulationRecord.status == status)
            rows = q.order_by(RegulationRecord.extracted_at.desc()).all()
        return [
            {
                "id": r.id,
                "title": r.title[:120],
                "jurisdiction": r.jurisdiction,
                "effective_date": r.effective_date,
                "critical_level": r.critical_level,
                "summary": r.summary[:200],
                "confidence": round(r.confidence * 100),
                "status": r.status,
                "source_url": r.source_url,
            }
            for r in rows
        ]

    def trend_by_day(self, days: int = 30) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with get_session() as db:
            rows = (
                db.query(
                    func.date(RegulationRecord.extracted_at).label("day"),
                    RegulationRecord.jurisdiction,
                    func.count().label("cnt"),
                )
                .filter(RegulationRecord.extracted_at >= cutoff)
                .group_by("day", RegulationRecord.jurisdiction)
                .order_by("day")
                .all()
            )
        return [{"day": r.day, "jurisdiction": r.jurisdiction, "cnt": r.cnt} for r in rows]

    def kpis(self, days: int = 7) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with get_session() as db:
            total = db.query(func.count(RegulationRecord.id)).scalar() or 0
            week  = db.query(func.count(RegulationRecord.id)).filter(RegulationRecord.extracted_at >= cutoff).scalar() or 0
            crit  = db.query(func.count(RegulationRecord.id)).filter(
                RegulationRecord.critical_level == "CRITICAL",
                RegulationRecord.extracted_at >= cutoff,
            ).scalar() or 0
            review= db.query(func.count(RegulationRecord.id)).filter(
                RegulationRecord.status == "HUMAN_REVIEW",
            ).scalar() or 0
        return {"total": total, "week": week, "critical": crit, "review": review}


class RegulatorRepo:
    def all_active(self) -> list[Regulator]:
        with get_session() as db:
            return db.query(Regulator).filter_by(active=True).all()

    def seed(self, rows: list[dict]):
        with get_session() as db:
            if db.query(Regulator).count():
                return
            for r in rows:
                db.add(Regulator(**r))
            db.commit()


class JobRepo:
    def create(self, regulator_name: str, jurisdiction: str) -> int:
        with get_session() as db:
            job = ScrapeJob(regulator_name=regulator_name, jurisdiction=jurisdiction)
            db.add(job)
            db.commit()
            db.refresh(job)
            return job.id

    def finish(self, job_id: int, docs_found: int, docs_saved: int, error: Optional[str] = None):
        with get_session() as db:
            job = db.get(ScrapeJob, job_id)
            if job:
                job.status = "ERROR" if error else "DONE"
                job.docs_found = docs_found
                job.docs_saved = docs_saved
                job.error_msg = error
                job.finished_at = datetime.utcnow()
                db.commit()

    def recent(self, limit: int = 20) -> list[dict]:
        with get_session() as db:
            rows = db.query(ScrapeJob).order_by(ScrapeJob.started_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "regulator": r.regulator_name,
                "jurisdiction": r.jurisdiction,
                "status": r.status,
                "found": r.docs_found,
                "saved": r.docs_saved,
                "error": r.error_msg or "",
                "started": r.started_at.strftime("%H:%M:%S %d.%m"),
                "duration": (
                    f"{int((r.finished_at - r.started_at).total_seconds())}s"
                    if r.finished_at else "running"
                ),
            }
            for r in rows
        ]


reg_repo  = RegulationRepo()
reg_repo_r= RegulatorRepo()
job_repo  = JobRepo()


# ── Default regulators ────────────────────────────────────────────
DEFAULT_REGULATORS = [
    {
        "name": "Минфин РФ",
        "jurisdiction": "RU",
        "base_url": "https://minfin.gov.ru/ru/document/",
        "strategy": "STATIC",
        "link_pattern": ".pdf",
    },
    {
        "name": "ЦБ РФ",
        "jurisdiction": "RU",
        "base_url": "https://cbr.ru/press/pr/",
        "strategy": "FOLLOW_HTML",     # listing → article → PDF
        "link_pattern": ".pdf",
    },
    {
        "name": "ЦБА Азербайджан",
        "jurisdiction": "AZ",
        "base_url": "https://www.cbar.az/page-6/regulatory-legal-acts",
        "strategy": "STATIC",
        "link_pattern": ".pdf",
    },
    {
        "name": "НБ Казахстана",
        "jurisdiction": "KZ",
        "base_url": "https://nationalbank.kz/ru/link/normativnaya-pravovaya-baza",
        "strategy": "JS_RENDER",       # SPA — нужен Playwright
        "link_pattern": ".pdf",
    },
    {
        "name": "НБРБ Беларусь",
        "jurisdiction": "BY",
        "base_url": "https://www.nbrb.by/legislation",
        "strategy": "JS_RENDER",       # SPA
        "link_pattern": ".pdf",
    },
    {
        "name": "АРРФР Казахстана",
        "jurisdiction": "KZ",
        "base_url": "https://www.gov.kz/memleket/entities/ardfm/documents",
        "strategy": "STATIC",
        "link_pattern": ".pdf",
    },
]
