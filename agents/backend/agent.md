# Backend Agent
> Owns everything in `backend/`. Python 3.9, FastAPI, Supabase, multi-provider LLM.

## Responsibilities
- All FastAPI routes (`main.py`)
- LLM provider logic (`llm.py`, `engine.py`, `parser.py`)
- Supabase persistence (`database.py`)
- Audit trail (`audit.py`)
- Analytics events (`analytics.py`)
- Observability (`observability.py`)
- Security middleware (`security.py`)

## Key Constraints
- Python 3.9 — use `from __future__ import annotations` for `X | Y` union types
- All new routes need: tag, summary, docstring, audit.emit(), analytics.track()
- Never log document content — GDPR/SOC2
- All Supabase calls must fail gracefully (wrapped in `_run()`)
- Run server: `cd backend && .venv/bin/uvicorn main:app --reload --port 8000`

## Before Every Change
1. Read the target file
2. Check `agents/shared/decisions.md` for prior context
3. Write decision if architectural

## After Every Change
- Update `agents/backend/memory.md`
- Update `agents/shared/project-state.md` if status changed
