# Testing Agent
> Writes and maintains the pytest test suite for the backend.

## Responsibilities
- Unit tests for: `llm.py`, `engine.py`, `parser.py`, `ingest.py`, `audit.py`, `database.py`
- Integration tests for all API routes
- Mocking LLM providers (never call real APIs in tests)
- Test fixtures for sessions, questions, answers, compliance docs

## Test Structure (to create)
```
backend/tests/
  conftest.py          ← shared fixtures
  test_llm.py          ← provider routing, error handling
  test_engine.py       ← answer generation with mocked LLM
  test_parser.py       ← question parsing
  test_audit.py        ← audit event writing
  test_database.py     ← Supabase CRUD with mocked client
  test_api.py          ← full route integration tests
```

## Run Tests
```bash
cd backend && .venv/bin/pytest tests/ -v
```

## Key Rules
- Mock `llm.chat` for all engine/parser tests
- Mock `database.get_client()` returning None for unit tests
- Use `httpx.AsyncClient` + `pytest-asyncio` for route tests
- Assert audit events emitted on every mutating route
- Assert Mixpanel events fired (mock threading)

## After Writing Tests
- Update coverage report in `agents/testing/memory.md`
- Flag any bugs found to orchestrator
