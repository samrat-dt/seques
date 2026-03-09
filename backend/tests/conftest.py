"""
Shared pytest fixtures for the Seques backend test suite.
"""

from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Ensure the backend source directory is on the Python path so that
# imports like `from llm import chat` resolve when tests run from any cwd.
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ---------------------------------------------------------------------------
# Environment variables — must be set BEFORE importing any backend module
# that reads them at module-load time.
# ---------------------------------------------------------------------------
os.environ["LLM_PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "test_key"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_KEY"] = ""
os.environ["SUPABASE_JWT_SECRET"] = ""  # disable auth in tests
os.environ["MIXPANEL_TOKEN"] = ""
os.environ["AUDIT_LOG_PATH"] = "/tmp/test_audit.log"
os.environ["RATE_LIMIT_PER_MINUTE"] = "10000"  # disable effective rate limiting in tests

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    """
    Session-scoped TestClient wrapping the FastAPI app.

    Supabase and Mixpanel are patched at the database/analytics module level
    so that no real network calls are made.
    """
    with (
        patch("database.get_client", return_value=None),
        patch("database.save_session", return_value=None),
        patch("database.save_questions", return_value=None),
        patch("database.save_answer", return_value=None),
        patch("database.mark_processing_started", return_value=None),
        patch("database.mark_processing_complete", return_value=None),
        patch("database.load_session_row", return_value=None),
        patch("analytics.track"),
    ):
        from main import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


# ---------------------------------------------------------------------------
# Per-test database / analytics patches
# (useful for individual test files that import main directly)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_db_and_analytics(monkeypatch):
    """
    Automatically patch all Supabase and Mixpanel calls so nothing hits the
    network even in unit tests that don't use the TestClient fixture.
    """
    noop = MagicMock(return_value=None)
    monkeypatch.setattr("database.save_session", noop)
    monkeypatch.setattr("database.save_questions", noop)
    monkeypatch.setattr("database.save_answer", noop)
    monkeypatch.setattr("database.mark_processing_started", noop)
    monkeypatch.setattr("database.mark_processing_complete", noop)
    monkeypatch.setattr("database.load_session_row", MagicMock(return_value=None))
    monkeypatch.setattr("analytics.track", noop)


# ---------------------------------------------------------------------------
# Sample model instances
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_question():
    from models import AnswerFormat, Question
    return Question(
        id="q_001",
        text="Does your organisation encrypt data at rest?",
        answer_format=AnswerFormat.yes_no_evidence,
        category="data security",
        original_row=0,
    )


@pytest.fixture()
def sample_freeform_question():
    from models import AnswerFormat, Question
    return Question(
        id="q_002",
        text="Describe your incident response process.",
        answer_format=AnswerFormat.freeform,
        category="incident management",
        original_row=1,
    )


@pytest.fixture()
def sample_compliance_doc():
    from models import ComplianceDoc, DocType, TrustLevel
    return ComplianceDoc(
        filename="SOC2_2024.pdf",
        doc_type=DocType.soc2,
        trust_level=TrustLevel.high,
        text="We encrypt all data at rest using AES-256. SOC 2 Type II certified.",
        pages=42,
    )


@pytest.fixture()
def sample_answer():
    from models import Answer, AnswerStatus, AnswerTone, EvidenceCoverage
    return Answer(
        question_id="q_001",
        question_text="Does your organisation encrypt data at rest?",
        draft_answer="Yes, we encrypt data at rest using AES-256.",
        evidence_coverage=EvidenceCoverage.covered,
        coverage_reason="SOC 2 report explicitly states AES-256 encryption at rest.",
        ai_certainty=92,
        certainty_reason="",
        evidence_sources=["SOC2_2024.pdf · CC6.7"],
        suggested_addition=None,
        answer_tone=AnswerTone.assertive,
        needs_review=False,
        status=AnswerStatus.draft,
    )


@pytest.fixture()
def good_llm_json():
    """A valid JSON string that the LLM would return for answer_question."""
    return (
        '{"draft_answer": "Yes, we encrypt data at rest using AES-256.", '
        '"evidence_coverage": "covered", '
        '"coverage_reason": "SOC 2 report states AES-256.", '
        '"ai_certainty": 92, '
        '"certainty_reason": "", '
        '"suggested_addition": null, '
        '"answer_tone": "assertive", '
        '"evidence_sources": ["SOC2_2024.pdf · CC6.7"]}'
    )


@pytest.fixture()
def good_parser_json():
    """A valid JSON array that the LLM would return for parse_text_questionnaire."""
    return (
        '[{"number": "1", "question_text": "Do you encrypt data at rest?", "answer_format": "yes_no_evidence"}, '
        '{"number": "2", "question_text": "Describe your patch management process.", "answer_format": "freeform"}]'
    )
