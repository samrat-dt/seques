"""
Tests for backend/engine.py

Covers:
- answer_question happy path (covered evidence, high certainty)
- answer_question with partial evidence
- answer_question when LLM returns no evidence
- needs_review logic (keyword triggers, certainty thresholds, freeform format)
- build_doc_context text truncation
- Graceful fallback when LLM returns invalid JSON
- Graceful fallback when evidence_coverage / answer_tone values are invalid enums
- check_needs_review edge cases
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    Answer,
    AnswerFormat,
    AnswerStatus,
    AnswerTone,
    ComplianceDoc,
    DocType,
    EvidenceCoverage,
    Question,
    TrustLevel,
)
from engine import answer_question, build_doc_context, check_needs_review


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_question(text="Do you encrypt data at rest?", fmt=AnswerFormat.yes_no_evidence, qid="q_001"):
    return Question(id=qid, text=text, answer_format=fmt, original_row=0)


def make_doc(text="We use AES-256 encryption at rest. SOC 2 Type II certified."):
    return ComplianceDoc(
        filename="SOC2_2024.pdf",
        doc_type=DocType.soc2,
        trust_level=TrustLevel.high,
        text=text,
        pages=10,
    )


GOOD_JSON = json.dumps({
    "draft_answer": "Yes, we encrypt data at rest using AES-256.",
    "evidence_coverage": "covered",
    "coverage_reason": "SOC 2 report explicitly states AES-256.",
    "ai_certainty": 92,
    "certainty_reason": "",
    "suggested_addition": None,
    "answer_tone": "assertive",
    "evidence_sources": ["SOC2_2024.pdf · CC6.7"],
})

PARTIAL_JSON = json.dumps({
    "draft_answer": "We do encrypt data, but specifics are limited.",
    "evidence_coverage": "partial",
    "coverage_reason": "Policy references encryption but no detail.",
    "ai_certainty": 55,
    "certainty_reason": "Vague reference only.",
    "suggested_addition": "Add specific encryption standard.",
    "answer_tone": "hedged",
    "evidence_sources": [],
})

NO_EVIDENCE_JSON = json.dumps({
    "draft_answer": "Unable to confirm from available evidence.",
    "evidence_coverage": "none",
    "coverage_reason": "No relevant evidence found.",
    "ai_certainty": 10,
    "certainty_reason": "No evidence at all.",
    "suggested_addition": "Add a data encryption policy.",
    "answer_tone": "hedged",
    "evidence_sources": [],
})


# ---------------------------------------------------------------------------
# answer_question — happy paths
# ---------------------------------------------------------------------------

class TestAnswerQuestionHappyPath:
    def test_returns_answer_instance(self):
        with patch("engine.chat", return_value=GOOD_JSON):
            result = answer_question(make_question(), [make_doc()])
        assert isinstance(result, Answer)

    def test_question_id_preserved(self):
        q = make_question(qid="q_042")
        with patch("engine.chat", return_value=GOOD_JSON):
            result = answer_question(q, [make_doc()])
        assert result.question_id == "q_042"

    def test_question_text_preserved(self):
        q = make_question(text="Do you use MFA?")
        with patch("engine.chat", return_value=GOOD_JSON):
            result = answer_question(q, [make_doc()])
        assert result.question_text == "Do you use MFA?"

    def test_covered_evidence_high_certainty(self):
        with patch("engine.chat", return_value=GOOD_JSON):
            result = answer_question(make_question(), [make_doc()])
        assert result.evidence_coverage == EvidenceCoverage.covered
        assert result.ai_certainty == 92
        assert result.answer_tone == AnswerTone.assertive
        assert result.needs_review is False

    def test_status_is_draft(self):
        with patch("engine.chat", return_value=GOOD_JSON):
            result = answer_question(make_question(), [make_doc()])
        assert result.status == AnswerStatus.draft

    def test_evidence_sources_populated(self):
        with patch("engine.chat", return_value=GOOD_JSON):
            result = answer_question(make_question(), [make_doc()])
        assert "SOC2_2024.pdf · CC6.7" in result.evidence_sources

    def test_suggested_addition_none(self):
        with patch("engine.chat", return_value=GOOD_JSON):
            result = answer_question(make_question(), [make_doc()])
        assert result.suggested_addition is None


# ---------------------------------------------------------------------------
# answer_question — partial / no evidence
# ---------------------------------------------------------------------------

class TestAnswerQuestionPartialEvidence:
    def test_partial_coverage(self):
        with patch("engine.chat", return_value=PARTIAL_JSON):
            result = answer_question(make_question(), [make_doc()])
        assert result.evidence_coverage == EvidenceCoverage.partial

    def test_partial_needs_review_due_to_low_certainty(self):
        with patch("engine.chat", return_value=PARTIAL_JSON):
            result = answer_question(make_question(), [make_doc()])
        # certainty 55 < 60 threshold triggers needs_review
        assert result.needs_review is True

    def test_no_evidence_forces_needs_review(self):
        with patch("engine.chat", return_value=NO_EVIDENCE_JSON):
            result = answer_question(make_question(), [make_doc()])
        assert result.needs_review is True
        assert result.evidence_coverage == EvidenceCoverage.none

    def test_suggested_addition_populated(self):
        with patch("engine.chat", return_value=PARTIAL_JSON):
            result = answer_question(make_question(), [make_doc()])
        assert result.suggested_addition == "Add specific encryption standard."


# ---------------------------------------------------------------------------
# answer_question — LLM returns invalid JSON (fallback)
# ---------------------------------------------------------------------------

class TestAnswerQuestionInvalidJson:
    def test_invalid_json_returns_answer(self):
        with patch("engine.chat", return_value="not valid json at all"):
            result = answer_question(make_question(), [make_doc()])
        assert isinstance(result, Answer)

    def test_invalid_json_sets_hedged_tone(self):
        with patch("engine.chat", return_value="garbage"):
            result = answer_question(make_question(), [make_doc()])
        assert result.answer_tone == AnswerTone.hedged

    def test_invalid_json_sets_zero_certainty(self):
        with patch("engine.chat", return_value="garbage"):
            result = answer_question(make_question(), [make_doc()])
        assert result.ai_certainty == 0

    def test_invalid_json_needs_review_true(self):
        with patch("engine.chat", return_value="garbage"):
            result = answer_question(make_question(), [make_doc()])
        assert result.needs_review is True

    def test_llm_returns_markdown_fenced_json(self):
        """Markdown code fences should be stripped before JSON parsing."""
        fenced = f"```json\n{GOOD_JSON}\n```"
        with patch("engine.chat", return_value=fenced):
            result = answer_question(make_question(), [make_doc()])
        assert result.evidence_coverage == EvidenceCoverage.covered


# ---------------------------------------------------------------------------
# answer_question — invalid enum values (fallback to defaults)
# ---------------------------------------------------------------------------

class TestAnswerQuestionInvalidEnums:
    def test_invalid_evidence_coverage_defaults_to_none(self):
        bad = json.dumps({
            **json.loads(GOOD_JSON),
            "evidence_coverage": "unknown_value",
        })
        with patch("engine.chat", return_value=bad):
            result = answer_question(make_question(), [make_doc()])
        assert result.evidence_coverage == EvidenceCoverage.none

    def test_invalid_answer_tone_defaults_to_hedged(self):
        bad = json.dumps({
            **json.loads(GOOD_JSON),
            "answer_tone": "unknown_tone",
        })
        with patch("engine.chat", return_value=bad):
            result = answer_question(make_question(), [make_doc()])
        assert result.answer_tone == AnswerTone.hedged

    def test_certainty_clamped_above_100(self):
        bad = json.dumps({**json.loads(GOOD_JSON), "ai_certainty": 150})
        with patch("engine.chat", return_value=bad):
            result = answer_question(make_question(), [make_doc()])
        assert result.ai_certainty == 100

    def test_certainty_clamped_below_0(self):
        bad = json.dumps({**json.loads(GOOD_JSON), "ai_certainty": -50})
        with patch("engine.chat", return_value=bad):
            result = answer_question(make_question(), [make_doc()])
        assert result.ai_certainty == 0


# ---------------------------------------------------------------------------
# check_needs_review
# ---------------------------------------------------------------------------

class TestCheckNeedsReview:
    def test_none_coverage_triggers_review(self):
        q = make_question()
        assert check_needs_review(q, {"evidence_coverage": "none", "ai_certainty": 95}) is True

    def test_certainty_below_60_triggers_review(self):
        q = make_question()
        assert check_needs_review(q, {"evidence_coverage": "covered", "ai_certainty": 55}) is True

    def test_freeform_certainty_below_75_triggers_review(self):
        q = make_question(fmt=AnswerFormat.freeform)
        assert check_needs_review(q, {"evidence_coverage": "covered", "ai_certainty": 74}) is True

    def test_freeform_certainty_at_75_no_review(self):
        q = make_question(fmt=AnswerFormat.freeform)
        # No review-triggering keywords in question text
        result = check_needs_review(q, {"evidence_coverage": "covered", "ai_certainty": 75})
        assert result is False

    def test_rto_keyword_triggers_review(self):
        q = make_question(text="What is your RTO?")
        assert check_needs_review(q, {"evidence_coverage": "covered", "ai_certainty": 95}) is True

    def test_rpo_keyword_triggers_review(self):
        q = make_question(text="What is your RPO?")
        assert check_needs_review(q, {"evidence_coverage": "covered", "ai_certainty": 95}) is True

    def test_subprocessor_keyword_triggers_review(self):
        q = make_question(text="List all subprocessors.")
        assert check_needs_review(q, {"evidence_coverage": "covered", "ai_certainty": 95}) is True

    def test_pen_test_keyword_triggers_review(self):
        q = make_question(text="When was the last pen test?")
        assert check_needs_review(q, {"evidence_coverage": "covered", "ai_certainty": 95}) is True

    def test_clean_high_certainty_no_review(self):
        q = make_question(text="Do you encrypt data at rest?", fmt=AnswerFormat.yes_no)
        assert check_needs_review(q, {"evidence_coverage": "covered", "ai_certainty": 90}) is False


# ---------------------------------------------------------------------------
# build_doc_context
# ---------------------------------------------------------------------------

class TestBuildDocContext:
    def test_includes_filename(self):
        doc = make_doc()
        ctx = build_doc_context([doc])
        assert "SOC2_2024.pdf" in ctx

    def test_includes_doc_type(self):
        doc = make_doc()
        ctx = build_doc_context([doc])
        assert "soc2" in ctx

    def test_includes_trust_level(self):
        doc = make_doc()
        ctx = build_doc_context([doc])
        assert "high" in ctx

    def test_text_truncated_to_16000_chars(self):
        long_text = "A" * 10000
        doc = ComplianceDoc(
            filename="big.pdf",
            doc_type=DocType.policy,
            trust_level=TrustLevel.medium,
            text=long_text,
            pages=5,
        )
        ctx = build_doc_context([doc])
        # The doc text portion should be at most 16000 A's
        assert "A" * 16001 not in ctx

    def test_multiple_docs_separated(self):
        doc1 = make_doc("First doc text.")
        doc2 = ComplianceDoc(
            filename="ISO27001.pdf",
            doc_type=DocType.iso27001,
            trust_level=TrustLevel.high,
            text="Second doc text.",
            pages=3,
        )
        ctx = build_doc_context([doc1, doc2])
        assert "First doc text." in ctx
        assert "Second doc text." in ctx

    def test_empty_docs_list(self):
        assert build_doc_context([]) == ""

    def test_provider_forwarded_to_chat(self):
        """answer_question should pass the provider kwarg through to chat()."""
        with patch("engine.chat", return_value=GOOD_JSON) as mock_chat:
            answer_question(make_question(), [make_doc()], provider="groq")
        _, kwargs = mock_chat.call_args
        assert kwargs.get("provider") == "groq"
