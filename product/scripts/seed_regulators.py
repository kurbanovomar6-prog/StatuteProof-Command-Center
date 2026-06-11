"""Seed initial regulators into the database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.db.session import init_db, SessionLocal
from app.infrastructure.db.models import Regulator

REGULATORS = [
    {"name": "Банк России", "jurisdiction": "RU", "base_url": "https://cbr.ru/press/pr/", "strategy": "STATIC", "link_pattern": ".pdf"},
    {"name": "Минфин РФ", "jurisdiction": "RU", "base_url": "https://minfin.gov.ru/ru/document/?id_4=80&area_id=4&page_id=2104&popup=Y", "strategy": "STATIC", "link_pattern": ".pdf"},
    {"name": "НБ Казахстана", "jurisdiction": "KZ", "base_url": "https://nationalbank.kz/ru/news/press-releasy", "strategy": "STATIC", "link_pattern": ".pdf"},
    {"name": "ЦБА Азербайджан", "jurisdiction": "AZ", "base_url": "https://www.cbar.az/", "strategy": "STATIC", "link_pattern": ".pdf"},
    {"name": "НБРБ Беларусь", "jurisdiction": "BY", "base_url": "https://www.nbrb.by/legislation/documents/", "strategy": "STATIC", "link_pattern": ".pdf"},
]


def seed():
    init_db()
    with SessionLocal() as db:
        existing = db.query(Regulator).count()
        if existing > 0:
            print(f"Already have {existing} regulators, skipping seed.")
            return
        for r in REGULATORS:
            db.add(Regulator(**r))
        db.commit()
        print(f"Seeded {len(REGULATORS)} regulators.")


if __name__ == "__main__":
    seed()
