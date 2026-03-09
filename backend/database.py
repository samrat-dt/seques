"""
Supabase persistence layer.

All operations fail gracefully — if Supabase is not configured or unavailable,
the app continues with in-memory state only (Phase 1 behaviour).

Tables (see migrations/001_initial_schema.sql):
  sessions, questions, answers, audit_events
"""

from __future__ import annotations

import os
from typing import Any

from observability import logger

_client = None


def get_client():
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")

    if not url or not key or "your_supabase" in url:
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        logger.info("supabase_connected", extra={"url": url})
    except Exception as exc:
        logger.warning("supabase_init_failed", extra={"error": str(exc)})

    return _client


def _run(operation, label: str) -> Any | None:
    """Execute a Supabase operation, log and swallow errors."""
    try:
        result = operation()
        return result
    except Exception as exc:
        logger.warning(f"supabase_{label}_failed", extra={"error": str(exc)})
        return None


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def save_session(session) -> None:
    db = get_client()
    if not db:
        return
    _run(
        lambda: db.table("sessions").upsert({
            "id": session.id,
            "provider": session.provider,
            "client_ip": session.client_ip,
            "questionnaire_type": session.questionnaire_type,
            "questionnaire_filename": session.questionnaire_filename,
            "total_questions": session.total_questions,
            "processing": session.processing,
            "user_id": getattr(session, "user_id", None),
        }).execute(),
        "save_session",
    )


def load_session_row(session_id: str) -> dict | None:
    db = get_client()
    if not db:
        return None
    result = _run(
        lambda: db.table("sessions").select("*").eq("id", session_id).execute(),
        "load_session",
    )
    if result and result.data:
        return result.data[0]
    return None


def load_questions(session_id: str) -> list[dict]:
    db = get_client()
    if not db:
        return []
    result = _run(
        lambda: db.table("questions").select("*").eq("session_id", session_id).execute(),
        "load_questions",
    )
    return result.data if result else []


def load_answers(session_id: str) -> list[dict]:
    db = get_client()
    if not db:
        return []
    result = _run(
        lambda: db.table("answers").select("*").eq("session_id", session_id).execute(),
        "load_answers",
    )
    return result.data if result else []


def mark_processing_started(session_id: str) -> None:
    db = get_client()
    if not db:
        return
    from datetime import datetime, timezone
    _run(
        lambda: db.table("sessions").update({
            "processing": True,
            "processing_started_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", session_id).execute(),
        "mark_processing_started",
    )


def mark_processing_complete(session_id: str) -> None:
    db = get_client()
    if not db:
        return
    from datetime import datetime, timezone
    _run(
        lambda: db.table("sessions").update({
            "processing": False,
            "processing_completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", session_id).execute(),
        "mark_processing_complete",
    )


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------

def save_questions(session_id: str, questions: list) -> None:
    db = get_client()
    if not db or not questions:
        return
    rows = [
        {
            "id": q.id,
            "session_id": session_id,
            "text": q.text,
            "answer_format": q.answer_format,
            "category": q.category,
            "original_row": q.original_row,
        }
        for q in questions
    ]
    _run(
        lambda: db.table("questions").upsert(rows).execute(),
        "save_questions",
    )


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------

def save_answer(session_id: str, answer) -> None:
    db = get_client()
    if not db:
        return
    _run(
        lambda: db.table("answers").upsert({
            "question_id": answer.question_id,
            "session_id": session_id,
            "question_text": answer.question_text,
            "draft_answer": answer.draft_answer,
            "evidence_coverage": answer.evidence_coverage,
            "coverage_reason": answer.coverage_reason,
            "ai_certainty": answer.ai_certainty,
            "certainty_reason": answer.certainty_reason,
            "answer_tone": answer.answer_tone,
            "needs_review": answer.needs_review,
            "status": answer.status,
            "evidence_sources": answer.evidence_sources,
            "suggested_addition": answer.suggested_addition,
        }).execute(),
        "save_answer",
    )


# ---------------------------------------------------------------------------
# Audit events
# ---------------------------------------------------------------------------

def save_audit_event(event: dict) -> None:
    db = get_client()
    if not db:
        return
    _run(
        lambda: db.table("audit_events").insert(event).execute(),
        "save_audit_event",
    )
