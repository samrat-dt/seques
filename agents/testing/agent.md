# Testing Agent

## Responsibilities
- Own backend/tests/ — full pytest coverage
- Run tests before every PR merge
- Track coverage and add tests for new features

## Test Files
- conftest.py — fixtures and env setup
- test_llm.py — LLM provider routing and error handling
- test_engine.py — answer_question with mocked LLM
- test_parser.py — questionnaire parsing with mocked LLM
- test_ingest.py — PDF detection and manual ingestion
- test_audit.py — audit event emission
- test_api.py — all API routes (integration)

## Run Tests
```bash
cd backend
.venv/bin/pytest tests/ -v
```

## Coverage Target
- Phase 1: 70% line coverage
- Phase 2: 80% line coverage
