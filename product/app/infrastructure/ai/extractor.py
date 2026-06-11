import logging
import os
from typing import Optional

import instructor
from openai import OpenAI

from app.core.domain.enums import Jurisdiction
from app.core.domain.models import RegulationModel

log = logging.getLogger(__name__)

_client = instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

_SYSTEM = """You are a regulatory intelligence specialist for CIS countries (Russia, Kazakhstan, Azerbaijan, Belarus, Uzbekistan).
Extract structured regulation metadata from the provided document text.
Be precise with dates (format YYYY-MM-DD). If a date is unclear, estimate based on context.
Set confidence < 0.7 if any field is uncertain.
Always include at least one industry tag (e.g. banking, fintech, taxation, insurance, securities).
Respond only with the structured fields, no extra text."""


def extract_regulation(
    raw_text: str,
    jurisdiction: Optional[Jurisdiction] = None,
    source_url: str = "unknown",
    max_retries: int = 2,
) -> RegulationModel:
    jurisdiction_hint = f"Jurisdiction: {jurisdiction.value}" if jurisdiction else ""
    prompt = f"""{jurisdiction_hint}
Source URL: {source_url}

Document text (first 4000 chars):
{raw_text[:4000]}

Extract all regulation metadata fields."""

    return _client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        max_retries=max_retries,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        response_model=RegulationModel,
    )
