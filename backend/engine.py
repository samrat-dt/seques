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


def build_doc_context(docs: List[ComplianceDoc]) -> str:
    parts = []
    for doc in docs:
        # Limit each doc to avoid enormous context — Phase 2 adds RAG for large docs
        text = doc.text[:8000] if len(doc.text) > 8000 else doc.text
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


def answer_question(question: Question, docs: List[ComplianceDoc], provider: str | None = None) -> Answer:
    doc_context = build_doc_context(docs)

    prompt = f"""You are a security compliance expert helping a vendor respond to a prospect's security questionnaire.

Your job: answer the question below using ONLY the evidence provided. Never fabricate facts.
If the evidence does not cover the question, say so clearly and explain what is missing.

QUESTION: {question.text}
FORMAT: {question.answer_format}
CATEGORY: {question.category or "general security"}

COMPLIANCE EVIDENCE FROM VENDOR'S DOCS:
{doc_context}

Return ONLY valid JSON — no markdown, no explanation. The JSON must have exactly these fields:
{{
  "draft_answer": "the answer to send to the prospect — professional, concise",
  "evidence_coverage": "none" | "partial" | "covered",
  "coverage_reason": "one sentence explaining why you chose this coverage level",
  "ai_certainty": integer from 0 to 100,
  "certainty_reason": "one sentence if certainty is below 80, otherwise empty string",
  "suggested_addition": "what the vendor should add to answer this better, or null if not needed",
  "answer_tone": "assertive" | "hedged" | "cannot_answer",
  "evidence_sources": ["list of source references used, e.g. 'SOC2_2024.pdf · CC6.7'"]
}}

coverage rules:
- "covered": the evidence directly and clearly addresses the question
- "partial": the evidence is related but missing specific details
- "none": no relevant evidence found

certainty rules:
- 90-100: evidence is explicit and unambiguous
- 70-89: evidence is clear but requires some interpretation
- 50-69: evidence is vague or only tangentially relevant
- below 50: very uncertain or no evidence"""

    content = chat(
        system="You are a security compliance expert. Return only valid JSON — no markdown fences, no preamble.",
        user=prompt,
        max_tokens=1024,
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
            "draft_answer": "Unable to generate answer. Please review manually.",
            "evidence_coverage": "none",
            "coverage_reason": "JSON parsing error during answer generation",
            "ai_certainty": 0,
            "certainty_reason": "System error — manual review required",
            "suggested_addition": "Manually answer this question",
            "answer_tone": "cannot_answer",
            "evidence_sources": [],
        }

    # Validate / clamp values
    try:
        coverage = EvidenceCoverage(data.get("evidence_coverage", "none"))
    except ValueError:
        coverage = EvidenceCoverage.none

    try:
        tone = AnswerTone(data.get("answer_tone", "cannot_answer"))
    except ValueError:
        tone = AnswerTone.cannot_answer

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
