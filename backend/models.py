from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class DocType(str, Enum):
    soc2 = "soc2"
    iso27001 = "iso27001"
    policy = "policy"
    manual = "manual"


class TrustLevel(str, Enum):
    high = "high"
    medium = "medium"


class AnswerFormat(str, Enum):
    yes_no = "yes_no"
    yes_no_evidence = "yes_no_evidence"
    freeform = "freeform"
    select = "select"
    numeric = "numeric"


class EvidenceCoverage(str, Enum):
    none = "none"
    partial = "partial"
    covered = "covered"


class AnswerTone(str, Enum):
    assertive = "assertive"
    hedged = "hedged"
    cannot_answer = "cannot_answer"


class AnswerStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    edited = "edited"


class Question(BaseModel):
    id: str
    text: str
    answer_format: AnswerFormat = AnswerFormat.freeform
    category: Optional[str] = None
    framework_hint: Optional[str] = None
    original_row: Optional[int] = None


class Answer(BaseModel):
    question_id: str
    question_text: str
    draft_answer: str
    evidence_coverage: EvidenceCoverage
    coverage_reason: str
    ai_certainty: int
    certainty_reason: str
    evidence_sources: List[str] = []
    suggested_addition: Optional[str] = None
    answer_tone: AnswerTone
    needs_review: bool
    status: AnswerStatus = AnswerStatus.draft


class ComplianceDoc(BaseModel):
    filename: str
    doc_type: DocType
    trust_level: TrustLevel
    text: str
    pages: int
