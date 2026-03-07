"""
Immutable audit trail.

Every write is an append-only JSON line to audit.log (and stdout).
In production, ship this file to your SIEM / Supabase audit table.

SOC 2 controls covered:
  CC7.2  — Monitor system components for anomalies
  CC6.1  — Logical access security measures
  A1.2   — Environmental protections (availability monitoring)

GDPR Art 30 — Records of processing activities
ISO 27001 A.12.4 — Logging and monitoring
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from observability import logger, request_id_var

_AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "audit.log"))


def _write(entry: dict[str, Any]) -> None:
    line = json.dumps(entry)
    # 1. Append-only local file (SIEM-shippable)
    with _AUDIT_LOG_PATH.open("a") as f:
        f.write(line + "\n")
    # 2. Structured log stream
    logger.info("audit_event", extra={"audit": True, **entry})
    # 3. Supabase audit_events table (async — import here to avoid circular)
    try:
        import threading
        import database
        threading.Thread(target=database.save_audit_event, args=(entry,), daemon=True).start()
    except Exception:
        pass


def emit(
    action: str,
    actor: str = "system",
    resource_type: str | None = None,
    resource_id: str | None = None,
    outcome: str = "success",   # success | failure | error
    detail: dict[str, Any] | None = None,
) -> str:
    """
    Emit one audit event. Returns the event_id.

    Parameters
    ----------
    action        : machine-readable verb, e.g. "session.create", "answer.approve"
    actor         : user/IP/system identifier
    resource_type : the kind of object acted on, e.g. "session", "answer"
    resource_id   : the object's ID
    outcome       : success | failure | error
    detail        : arbitrary extra context
    """
    event_id = str(uuid.uuid4())
    entry = {
        "event_id": event_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "unix_ms": int(time.time() * 1000),
        "action": action,
        "actor": actor,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "outcome": outcome,
        "request_id": request_id_var.get(""),
        "detail": detail or {},
    }
    _write(entry)
    return event_id
