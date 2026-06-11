from datetime import date, datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from .enums import Jurisdiction, CriticalLevel, PipelineStatus


class RegulationModel(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    jurisdiction: Jurisdiction
    publication_date: date
    effective_date: date
    summary: str = Field(..., min_length=10, max_length=2000)
    industries: list[str] = Field(default_factory=list)
    critical_level: CriticalLevel = CriticalLevel.LOW
    source_url: str = Field(..., min_length=10)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    status: PipelineStatus = PipelineStatus.PROCESSING
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def cross_field_integrity(self):
        # Annual reports legitimately have effective_date (year covered) < publication_date (release date).
        # Allow up to 2 years gap; flag only extreme inversions as OCR errors.
        two_years = timedelta(days=730)
        if self.publication_date - self.effective_date > two_years:
            raise ValueError(
                f"effective_date {self.effective_date} < publication_date {self.publication_date} "
                "(possible OCR transposition)"
            )
        five_years = date.today() + timedelta(days=5 * 365)
        if self.effective_date > five_years:
            raise ValueError(f"effective_date {self.effective_date} more than 5 years ahead — likely OCR error")
        if self.critical_level in (CriticalLevel.HIGH, CriticalLevel.CRITICAL):
            if len(self.summary) < 50:
                raise ValueError(f"{self.critical_level} regulation requires summary >= 50 chars")
        return self


class RegulatorConfig(BaseModel):
    name: str
    jurisdiction: Jurisdiction
    base_url: str
    strategy: str = "STATIC"
    link_pattern: str = ".pdf"
    active: bool = True
