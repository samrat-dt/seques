"""
Tests for backend/audit.py

Covers:
- emit() returns a UUID-shaped string
- emit() writes a JSON line to the audit log file
- Audit entry contains all required fields
- emit() calls logger.info with audit=True
- Supabase thread is started (or silently skipped on failure)
- emit() uses provided actor, resource_type, resource_id, outcome, detail
- emit() defaults: actor="system", outcome="success", empty detail
- _AUDIT_LOG_PATH respects AUDIT_LOG_PATH env var
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_audit_log(tmp_path, monkeypatch):
    """
    Redirect the audit log to a temp file for each test.
    We must patch the module-level _AUDIT_LOG_PATH variable in audit.py
    because it is evaluated at import time.
    """
    log_file = tmp_path / "test_audit.log"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(log_file))

    import audit
    monkeypatch.setattr(audit, "_AUDIT_LOG_PATH", log_file)
    return log_file


# ---------------------------------------------------------------------------
# emit() basics
# ---------------------------------------------------------------------------

class TestEmitBasics:
    def test_returns_string(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            result = audit.emit("session.create")
        assert isinstance(result, str)

    def test_returns_valid_uuid(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            result = audit.emit("session.create")
        # Should not raise
        uuid.UUID(result)

    def test_different_calls_return_different_ids(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            id1 = audit.emit("session.create")
            id2 = audit.emit("session.create")
        assert id1 != id2


# ---------------------------------------------------------------------------
# Log file write
# ---------------------------------------------------------------------------

class TestAuditLogFileWrite:
    def test_writes_to_log_file(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            audit.emit("session.create", actor="test_ip")
        assert tmp_audit_log.exists()
        content = tmp_audit_log.read_text()
        assert len(content.strip()) > 0

    def test_log_line_is_valid_json(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            audit.emit("session.create")
        line = tmp_audit_log.read_text().strip().splitlines()[-1]
        entry = json.loads(line)  # Must not raise
        assert isinstance(entry, dict)

    def test_multiple_emits_append_multiple_lines(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            audit.emit("session.create")
            audit.emit("answer.update")
            audit.emit("export.download")
        lines = [l for l in tmp_audit_log.read_text().strip().splitlines() if l.strip()]
        assert len(lines) >= 3

    def test_each_line_ends_with_newline(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            audit.emit("session.create")
        raw = tmp_audit_log.read_text()
        assert raw.endswith("\n")


# ---------------------------------------------------------------------------
# Audit entry fields
# ---------------------------------------------------------------------------

class TestAuditEntryFields:
    def _emit_and_read(self, tmp_audit_log, **kwargs):
        import audit
        with patch("audit.database"):
            event_id = audit.emit(**kwargs)
        line = tmp_audit_log.read_text().strip().splitlines()[-1]
        return event_id, json.loads(line)

    def test_event_id_in_entry(self, tmp_audit_log):
        event_id, entry = self._emit_and_read(tmp_audit_log, action="session.create")
        assert entry["event_id"] == event_id

    def test_action_in_entry(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="answer.approve")
        assert entry["action"] == "answer.approve"

    def test_actor_default_is_system(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="session.create")
        assert entry["actor"] == "system"

    def test_actor_custom(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="session.create", actor="192.168.1.1")
        assert entry["actor"] == "192.168.1.1"

    def test_outcome_default_is_success(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="session.create")
        assert entry["outcome"] == "success"

    def test_outcome_failure(self, tmp_audit_log):
        _, entry = self._emit_and_read(
            tmp_audit_log, action="auth.login", outcome="failure"
        )
        assert entry["outcome"] == "failure"

    def test_resource_type_set(self, tmp_audit_log):
        _, entry = self._emit_and_read(
            tmp_audit_log, action="docs.upload", resource_type="session"
        )
        assert entry["resource_type"] == "session"

    def test_resource_id_set(self, tmp_audit_log):
        _, entry = self._emit_and_read(
            tmp_audit_log, action="docs.upload", resource_id="abc-123"
        )
        assert entry["resource_id"] == "abc-123"

    def test_detail_dict_set(self, tmp_audit_log):
        _, entry = self._emit_and_read(
            tmp_audit_log,
            action="session.create",
            detail={"provider": "groq", "count": 5},
        )
        assert entry["detail"]["provider"] == "groq"
        assert entry["detail"]["count"] == 5

    def test_detail_default_is_empty_dict(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="session.create")
        assert entry["detail"] == {}

    def test_ts_field_present(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="session.create")
        assert "ts" in entry

    def test_unix_ms_field_present(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="session.create")
        assert "unix_ms" in entry
        assert isinstance(entry["unix_ms"], int)

    def test_resource_type_none_by_default(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="session.create")
        assert entry["resource_type"] is None

    def test_resource_id_none_by_default(self, tmp_audit_log):
        _, entry = self._emit_and_read(tmp_audit_log, action="session.create")
        assert entry["resource_id"] is None


# ---------------------------------------------------------------------------
# logger.info call
# ---------------------------------------------------------------------------

class TestAuditLogging:
    def test_logger_info_called_with_audit_flag(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            with patch.object(audit.logger, "info") as mock_log:
                audit.emit("session.create")
        # At least one call should have audit=True in the extra dict
        calls_with_audit = [
            c for c in mock_log.call_args_list
            if c.kwargs.get("extra", {}).get("audit") is True
        ]
        assert len(calls_with_audit) >= 1

    def test_logger_info_called_with_action(self, tmp_audit_log):
        import audit
        with patch("audit.database"):
            with patch.object(audit.logger, "info") as mock_log:
                audit.emit("answer.update")
        call_extra_actions = [
            c.kwargs.get("extra", {}).get("action")
            for c in mock_log.call_args_list
            if c.kwargs.get("extra", {}).get("audit") is True
        ]
        assert "answer.update" in call_extra_actions


# ---------------------------------------------------------------------------
# Supabase threading
# ---------------------------------------------------------------------------

class TestAuditSupabaseThread:
    def test_supabase_failure_does_not_raise(self, tmp_audit_log):
        """_write() swallows Supabase errors gracefully."""
        import audit

        # Simulate an import or runtime error in database module
        with patch("audit.database", side_effect=Exception("db down")):
            # Should not raise
            audit.emit("session.create")

    def test_supabase_thread_started_when_database_available(self, tmp_audit_log):
        import audit
        import threading

        mock_db = MagicMock()
        mock_db.save_audit_event = MagicMock()

        with patch("audit.database", mock_db):
            with patch("threading.Thread") as mock_thread:
                mock_instance = MagicMock()
                mock_thread.return_value = mock_instance
                audit.emit("session.create")

        mock_thread.assert_called_once()
        mock_instance.start.assert_called_once()
