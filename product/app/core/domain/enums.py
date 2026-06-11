from enum import Enum


class Jurisdiction(str, Enum):
    RU = "RU"
    KZ = "KZ"
    AZ = "AZ"
    BY = "BY"
    UZ = "UZ"


class CriticalLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ScrapeStrategy(str, Enum):
    STATIC = "STATIC"
    DYNAMIC = "DYNAMIC"


class PipelineStatus(str, Enum):
    PROCESSING = "PROCESSING"
    VALIDATED = "VALIDATED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
