"""
Mixpanel analytics wrapper.

All calls are fire-and-forget (background thread). If MIXPANEL_TOKEN is not set,
events are logged as structured JSON so nothing is lost — you can replay them
once you wire up the token.

Events tracked (and their Mixpanel dashboard equivalents):
  - session_created         → Funnel step 1
  - docs_uploaded           → Funnel step 2
  - questionnaire_uploaded  → Funnel step 3
  - processing_started      → Funnel step 4
  - processing_completed    → Core metric (success rate, latency)
  - answer_edited           → Engagement
  - answer_approved         → Quality signal
  - export_downloaded       → Conversion
  - provider_selected       → A/B signal (which LLM gets used)
  - api_error               → Error tracking
"""

from __future__ import annotations

import os
import threading
from typing import Any

from observability import logger

_TOKEN = os.getenv("MIXPANEL_TOKEN", "")
_mp = None  # lazy-init


def _get_client():
    global _mp, _TOKEN
    if _mp is not None:
        return _mp
    _TOKEN = os.getenv("MIXPANEL_TOKEN", "")
    if not _TOKEN or _TOKEN == "your_mixpanel_token_here":
        return None
    try:
        from mixpanel import Mixpanel
        _mp = Mixpanel(_TOKEN)
        logger.info("mixpanel_initialized")
    except ImportError:
        logger.warning("mixpanel_sdk_missing", extra={"hint": "pip install mixpanel"})
    return _mp


def _fire(distinct_id: str, event: str, props: dict[str, Any]) -> None:
    client = _get_client()
    props.setdefault("app", "seques")
    props.setdefault("env", os.getenv("ENVIRONMENT", "development"))
    props.setdefault("version", os.getenv("APP_VERSION", "1.0.0"))
    if client:
        try:
            client.track(distinct_id, event, props)
        except Exception as exc:
            logger.warning("mixpanel_send_failed", extra={"error": str(exc), "event": event})
    else:
        logger.info("analytics_event_queued", extra={"event": event, "props": props, "distinct_id": distinct_id})


def track(distinct_id: str, event: str, props: dict[str, Any] | None = None) -> None:
    """Non-blocking: sends to Mixpanel in a background thread."""
    threading.Thread(
        target=_fire,
        args=(distinct_id, event, props or {}),
        daemon=True,
    ).start()


# ---------------------------------------------------------------------------
# Typed helpers — one per tracked event
# ---------------------------------------------------------------------------

def session_created(session_id: str, provider: str, ip: str) -> None:
    track(session_id, "session_created", {"provider": provider, "ip": ip})


def docs_uploaded(session_id: str, doc_count: int, doc_types: list[str]) -> None:
    track(session_id, "docs_uploaded", {"doc_count": doc_count, "doc_types": doc_types})


def questionnaire_uploaded(session_id: str, question_count: int, source_type: str, provider: str) -> None:
    track(session_id, "questionnaire_uploaded", {
        "question_count": question_count,
        "source_type": source_type,
        "provider": provider,
    })


def processing_started(session_id: str, question_count: int, provider: str) -> None:
    track(session_id, "processing_started", {
        "question_count": question_count,
        "provider": provider,
    })


def processing_completed(
    session_id: str,
    question_count: int,
    provider: str,
    duration_ms: int,
    needs_review_count: int,
    error_count: int,
) -> None:
    track(session_id, "processing_completed", {
        "question_count": question_count,
        "provider": provider,
        "duration_ms": duration_ms,
        "needs_review_count": needs_review_count,
        "error_count": error_count,
        "success_rate": round((question_count - error_count) / max(question_count, 1) * 100, 1),
    })


def answer_edited(session_id: str, question_id: str) -> None:
    track(session_id, "answer_edited", {"question_id": question_id})


def answer_status_changed(session_id: str, question_id: str, new_status: str) -> None:
    track(session_id, "answer_status_changed", {
        "question_id": question_id,
        "new_status": new_status,
    })


def export_downloaded(session_id: str, format: str, question_count: int) -> None:
    track(session_id, "export_downloaded", {
        "format": format,
        "question_count": question_count,
    })


def api_error(session_id: str, path: str, status_code: int, detail: str) -> None:
    track(session_id, "api_error", {
        "path": path,
        "status_code": status_code,
        "detail": detail[:200],
    })
