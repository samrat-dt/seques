# Seques — Project Root Context
> Read this first. Every agent and every session starts here.

## What This Is
**Seques** is an AI-powered security questionnaire co-pilot. Vendors upload their compliance docs (SOC 2, ISO 27001, policies) and a prospect's questionnaire. The AI drafts every answer. Users review, edit, approve, and export.

**Stack**: FastAPI (Python 3.9) + React/Vite/Tailwind
**LLM**: Multi-provider via `backend/llm.py` — Groq (default), Google, Anthropic
**Analytics**: Mixpanel (live)
**DB**: Supabase (live — run `backend/migrations/001_initial_schema.sql` first)
**Docs**: `docs/` — architecture, handover, runbook, compliance/

## Repo Layout
```
seques/
├── CLAUDE.md                  ← YOU ARE HERE
├── agents/                    ← agent definitions + memory
│   ├── orchestrator/
│   ├── backend/
│   ├── frontend/
│   ├── qa/
│   ├── testing/
│   ├── documentation/
│   ├── project-manager/
│   ├── compliance/
│   ├── security/
│   ├── infra/
│   └── blog/
├── backend/                   ← FastAPI app
│   ├── main.py                ← all routes
│   ├── llm.py                 ← multi-provider wrapper
│   ├── engine.py              ← answer generation
│   ├── parser.py              ← questionnaire parsing
│   ├── database.py            ← Supabase CRUD
│   ├── analytics.py           ← Mixpanel events
│   ├── audit.py               ← audit trail
│   ├── observability.py       ← structured logging
│   ├── security.py            ← headers + rate limiting
│   ├── migrations/
│   └── .env                   ← secrets (gitignored)
├── frontend/src/
│   ├── api.js                 ← all fetch calls
│   ├── App.jsx
│   └── screens/               ← Upload → Processing → Review → Export
└── docs/
    ├── architecture.md
    ├── handover.md
    ├── runbook.md
    └── compliance/
```

## Running Locally
```bash
cd backend && .venv/bin/uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```
- Frontend: http://localhost:5174 (or 5173)
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Active Credentials (in backend/.env — never commit)
- Groq: configured ✓
- Mixpanel: configured ✓ (token: dbf663cd...)
- Supabase: configured ✓ (deekxushpzcxmzdcvfxq.supabase.co)

## Agent System
All agents are defined in `agents/`. The orchestrator routes tasks.
Every agent reads `agents/shared/project-state.md` before acting.
Every agent writes decisions to `agents/shared/decisions.md`.
Blog posts go to `agents/blog/posts/`.

### Agent Engagement Rules
- **All agents** (backend, frontend, qa, testing, security, compliance, documentation, infra, project-manager, github) engage at **every step** — every feature, fix, or change triggers all relevant agents.
- **Blog agent** engages only at **major milestones** (phase completions, significant feature launches, customer wins).
- Orchestrator is responsible for routing tasks to all relevant agents in parallel per step.

## Current Phase
**Phase 1 (MVP)** — in-memory sessions, multi-provider LLM, basic UI
**Phase 2** — Supabase persistence (schema ready), auth, RAG for large docs

## Known Gaps (do not re-investigate — already documented)
- No auth (Phase 2)
- In-memory rate limiter (Phase 2: Redis)
- Doc truncation at 8KB (Phase 2: RAG)
- No DPAs signed with sub-processors (pre-launch blocker)
