from __future__ import annotations

import json
import re
from typing import List

from llm import chat

from models import (
    Answer,
    AnswerFormat,
    AnswerStatus,
    AnswerTone,
    ComplianceDoc,
    EvidenceCoverage,
    Question,
)

# Questions containing these terms almost always need specific values
# that compliance docs rarely state explicitly
NEEDS_REVIEW_KEYWORDS = [
    "rto",
    "rpo",
    "subprocessor",
    "sub-processor",
    "last pen test",
    "last penetration test",
    "number of employees",
    "headcount",
    "certification expir",
    "insurance",
    "named certif",
    "specific date",
    "how many days",
    "patch within",
]

DOC_CHAR_LIMIT = 40_000
TOTAL_CHAR_BUDGET = 96_000


def build_doc_context(docs: List[ComplianceDoc]) -> str:
    if docs:
        per_doc_budget = min(DOC_CHAR_LIMIT, TOTAL_CHAR_BUDGET // len(docs))
    else:
        per_doc_budget = DOC_CHAR_LIMIT

    parts = []
    for doc in docs:
        text = doc.text[:per_doc_budget]
        parts.append(
            f"=== SOURCE: {doc.filename} | Type: {doc.doc_type} | Trust: {doc.trust_level} ===\n{text}"
        )
    return "\n\n".join(parts)


def check_needs_review(question: Question, data: dict) -> bool:
    q_lower = question.text.lower()

    if data.get("evidence_coverage") == "none":
        return True
    if data.get("ai_certainty", 100) < 60:
        return True
    if question.answer_format == AnswerFormat.freeform and data.get("ai_certainty", 100) < 75:
        return True
    if any(kw in q_lower for kw in NEEDS_REVIEW_KEYWORDS):
        return True

    return False


def _max_tokens_for_format(answer_format: AnswerFormat) -> int:
    if answer_format == AnswerFormat.yes_no:
        return 512
    elif answer_format == AnswerFormat.yes_no_evidence:
        return 900
    else:
        return 2048


def answer_question(
    question: Question,
    docs: List[ComplianceDoc],
    provider: str | None = None,
    doc_context: str | None = None,
) -> Answer:
    if doc_context is None:
        doc_context = build_doc_context(docs)

    prompt = f"""FRAMEWORK KNOWLEDGE:
- SOC 2 Type II certified → implies: access controls, encryption at rest/in transit, incident response, change management, vulnerability management, business continuity controls are in place.
- ISO 27001 certified → implies: ISMS, risk assessment, asset management, supplier security, HR security, physical controls, cryptography policy, continual improvement.
- Policy documents → vendor has defined and communicated specific control procedures.

QUESTION: {question.text}
FORMAT: {question.answer_format}
CATEGORY: {question.category or "general security"}

COMPLIANCE EVIDENCE FROM VENDOR'S DOCS:
{doc_context}

INSTRUCTIONS:
1. ALWAYS write a draft_answer. Never use "cannot answer", "not available", or "evidence not found" as the answer itself.
2. If uploaded docs address the question, base your answer on them (evidence_coverage: "covered" or "partial").
3. If docs do NOT cover the question, write a reasonable draft using compliance domain knowledge about what a SOC 2 / ISO 27001 certified company would typically do. Set evidence_coverage to "none", answer_tone to "hedged", and suggested_addition to instruct the vendor to confirm the answer reflects their actual practice.
4. Phrase hedged answers as: "As a SOC 2 Type II certified organization, we maintain [control]..." — never as a refusal.
5. For yes/no format: answer Yes or No first, then a one-sentence explanation.
6. Keep draft_answer professional and concise — suitable to paste directly into a prospect's questionnaire.

Return ONLY valid JSON with exactly these fields:
{{
  "draft_answer": "professional answer — NEVER empty, NEVER 'cannot answer'",
  "evidence_coverage": "none" | "partial" | "covered",
  "coverage_reason": "one sentence",
  "ai_certainty": integer 0-100,
  "certainty_reason": "one sentence if < 80, else empty string",
  "suggested_addition": "what vendor should verify or confirm, or null",
  "answer_tone": "assertive" | "hedged",
  "evidence_sources": ["filenames and sections used, or [] if domain knowledge only"]
}}

coverage: "covered" = docs directly address it; "partial" = related but incomplete; "none" = domain knowledge answer
tone: "assertive" = docs support clearly; "hedged" = based on what a certified vendor typically does
certainty: 90-100 explicit; 70-89 interpreted; 50-69 vague/tangential; 30-49 domain knowledge; <30 unusual"""

    content = chat(
        system=(
            "You are a senior security compliance consultant helping a vendor draft responses "
            "to security questionnaires. Your job is to ALWAYS produce a professional, usable "
            "draft answer — never leave a question unanswered. Return only valid JSON — "
            "no markdown fences, no preamble."
        ),
        user=prompt,
        max_tokens=_max_tokens_for_format(question.answer_format),
        provider=provider,
    )

    # Strip markdown code fences if present
    if "```" in content:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            content = match.group()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {
            "draft_answer": "This question requires vendor review. Please provide your response based on your actual security practices.",
            "evidence_coverage": "none",
            "coverage_reason": "JSON parsing error during answer generation",
            "ai_certainty": 0,
            "certainty_reason": "System error — manual review required",
            "suggested_addition": "Manually answer this question based on your actual security controls",
            "answer_tone": "hedged",
            "evidence_sources": [],
        }

    # Validate / clamp values
    try:
        coverage = EvidenceCoverage(data.get("evidence_coverage", "none"))
    except ValueError:
        coverage = EvidenceCoverage.none

    try:
        tone = AnswerTone(data.get("answer_tone", "hedged"))
    except ValueError:
        tone = AnswerTone.hedged

    certainty = max(0, min(100, int(data.get("ai_certainty", 0))))
    needs_review = check_needs_review(question, {**data, "ai_certainty": certainty})

    return Answer(
        question_id=question.id,
        question_text=question.text,
        draft_answer=data.get("draft_answer", ""),
        evidence_coverage=coverage,
        coverage_reason=data.get("coverage_reason", ""),
        ai_certainty=certainty,
        certainty_reason=data.get("certainty_reason", ""),
        evidence_sources=data.get("evidence_sources", []),
        suggested_addition=data.get("suggested_addition") or None,
        answer_tone=tone,
        needs_review=needs_review,
        status=AnswerStatus.draft,
    )
