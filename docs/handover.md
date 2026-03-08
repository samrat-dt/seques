# Agent / Engineer Handover Document
**Product**: Seques — Security Questionnaire Co-Pilot
Last updated: 2026-03-09

This document is the single source of truth for any agent or engineer picking up this codebase.
Read this first, then `docs/architecture.md`.

---

## Phase 1 Complete — State as of 2026-03-09

Phase 1 (MVP) is **feature-complete and running**. All items below reflect the current deployed state. A new engineer can clone, set env vars, and have the full stack running in under 10 minutes.

### What is working

| Capability | Status | Notes |
|---|---|---|
| Multi-provider LLM (Groq / Google / Anthropic) | Live | `LLM_PROVIDER` env var switches provider at runtime |
| Groq key rotation across 5 keys | Live | Round-robins to spread TPD quota |
| Questionnaire parsing (Excel, PDF, CSV, paste) | Live | `parser.py` |
| Compliance doc ingestion (PDF, DOCX) | Live | `ingest.py`; 32KB char budget per prompt |
| Answer generation with `assertive` / `hedged` tone | Live | `engine.py`; `cannot_answer` is a bug, not a valid tone |
| SSE streaming of answers as they complete | Live | `GET /api/sessions/{id}/stream` |
| Review / edit / approve UI | Live | `Review.jsx` |
| Excel + PDF export | Live | `export.py` |
| Structured JSON logging + request tracing | Live | `observability.py` |
| Append-only audit trail | Live | `audit.py` → `audit.log` |
| Mixpanel analytics | Live | Token configured; 5-step funnel tracked |
| Security headers + in-memory rate limiter | Live | `security.py` |
| Supabase DB schema | Schema ready, not wired | `migrations/001_initial_schema.sql` — Phase 2 wires it |
| Branch protection on `main` | Active | PR required, no force push, no deletion |

### Active configuration (free Groq tier)

```
ANSWER_CONCURRENCY=1
QUESTION_DELAY_S=1.5
DOC_CHAR_BUDGET=32000
GROQ_API_KEY_1 … GROQ_API_KEY_5  (5 keys, rotate at midnight UTC if exhausted)
```

See `docs/runbook.md → Phase 1 Checkpoint` for scale-up settings and TPD recovery steps.

---

## What This Product Does

Seques is a B2B SaaS tool that helps security teams respond to vendor questionnaires faster.
A user uploads their compliance documents (SOC 2 reports, ISO 27001 certs, policies)
and the prospect's questionnaire (PDF, Excel, or pasted text). An LLM reads the evidence
and drafts every answer. The user then reviews, edits, approves, and exports the response.

---

## Repository Layout

```
seques/
├── backend/
│   ├── main.py           ← FastAPI app entry point
│   ├── engine.py         ← LLM answering logic
│   ├── parser.py         ← Questionnaire parsing
│   ├── ingest.py         ← Compliance doc ingestion
│   ├── llm.py            ← Multi-provider LLM wrapper
│   ├── models.py         ← Pydantic data models
│   ├── export.py         ← Excel + PDF generation
│   ├── observability.py  ← Structured logging + request tracing
│   ├── audit.py          ← Immutable audit trail
│   ├── analytics.py      ← Mixpanel event tracking
│   ├── security.py       ← Security headers + rate limiting
│   ├── requirements.txt
│   ├── .env              ← Secrets (gitignored)
│   └── .env.example      ← Template — copy to .env
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api.js         ← All fetch calls
│       └── screens/
│           ├── Upload.jsx     ← Step 1: upload docs + questionnaire
│           ├── Processing.jsx ← Step 2: poll /status
│           ├── Review.jsx     ← Step 3: edit/approve answers
│           └── Export.jsx     ← Step 4: download
└── docs/
    ├── handover.md          ← THIS FILE
    ├── architecture.md      ← System diagram + module map
    ├── runbook.md           ← Ops procedures
    └── compliance/
        ├── data_inventory.md   ← GDPR Art 30 register
        ├── SOC2_controls.md
        ├── GDPR_controls.md
        └── ISO27001_controls.md
```

---

## Running Locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in at least one LLM key
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

Swagger UI: http://localhost:8000/docs
Audit log: `backend/audit.log`

---

## Key Decisions & Why

| Decision | Reason |
|---|---|
| FastAPI + uvicorn | Async-native, auto-generates OpenAPI/Swagger, Python ecosystem |
| In-memory sessions | MVP simplicity; Supabase persistence is Phase 2 |
| Multi-provider LLM (llm.py) | User wanted to test free providers (Groq, Google) before paying Anthropic |
| `LLM_PROVIDER` env var | Single switch, no code changes needed to swap models |
| Append-only `audit.log` | Simplest SOC 2 CC7.2 implementation; ship to SIEM in Phase 2 |
| Doc truncation to 8KB | Prevents runaway token costs; Phase 2 adds RAG for large docs |
| Mixpanel analytics | User-requested; events are PII-free (no doc content) |
| Tailwind + React | Rapid UI iteration; no design system dependencies |

---

## Known Gaps — Phase 1 (do not re-investigate, already documented)

These are intentional Phase 1 trade-offs, not bugs. All are accepted and tracked for Phase 2.

| Gap | Impact | Phase 2 Fix |
|---|---|---|
| No authentication | Any caller can create/read sessions | Supabase Auth (JWT) |
| In-memory sessions | Restart wipes all sessions | Wire Supabase persistence (`database.py` scaffold exists) |
| Single process | All sessions share one uvicorn worker | Celery workers + Redis broker |
| In-memory rate limiter | Won't scale to multiple workers | Redis-backed rate limiter |
| 32KB doc char budget | Large SOC 2 reports lose detail beyond ~10 pages | Vector embeddings + RAG pipeline |
| No LLM retry on failure | Groq timeout → that question errors, no auto-recover | Exponential backoff retry in `engine.py` |
| No DPAs with sub-processors | Pre-launch blocker for GDPR/SOC 2 | Execute DPAs with Groq, Google, Anthropic, Mixpanel, Supabase |

## Phase 2 — What to Build Next (2026-03-09)

Priority order for the next engineer picking this up:

1. **Supabase persistence** — `database.py` has the CRUD scaffold; `migrations/001_initial_schema.sql` has the full schema. Wire `main.py` to write sessions/questions/answers to Supabase instead of the in-memory dict. This unblocks multi-worker deployment.
2. **Authentication** — Add Supabase Auth. Gate all `/api/sessions/*` routes on a valid JWT. Add user_id to audit events.
3. **LLM retry with backoff** — Wrap the `llm.py` `complete()` call in a retry loop (3 attempts, exponential backoff). Catches transient Groq 429s and timeouts.
4. **Redis rate limiter** — Replace the in-memory dict in `security.py` with a Redis-backed counter (e.g., `redis-py` + `slowapi`). Required before multi-worker deploy.
5. **RAG for large docs** — Chunk compliance docs, embed with a small model (e.g., `text-embedding-3-small`), store vectors in Supabase `pgvector`. At query time, retrieve the top-k chunks relevant to each question instead of the flat char budget.
6. **DPAs** — Legal task, not engineering. Block production launch on this.

## Mixpanel Dashboard Setup

---

## Mixpanel Dashboard Setup

Mixpanel is **live** — token is configured in `backend/.env`. Events flow on every session.

To verify it is working:
1. Start backend and run a test session end-to-end.
2. Open Mixpanel Live View — you should see `session_created`, `docs_uploaded`, `processing_started`, `processing_completed`, `export_downloaded` events within seconds.

**Recommended dashboards to create in Mixpanel UI**:

| Dashboard | Key metrics |
|---|---|
| Funnel | session_created → docs_uploaded → questionnaire_uploaded → processing_started → export_downloaded |
| Quality | avg ai_certainty, needs_review_count / question_count |
| Provider A/B | processing_completed broken down by provider; avg duration_ms |
| Errors | api_error count by path and status_code |
| Engagement | answer_edited + answer_approved rates |

---

## Supabase Schema (Phase 2 Target)

```sql
-- sessions table
create table sessions (
  id uuid primary key,
  provider text not null,
  client_ip text,
  created_at timestamptz default now(),
  processing_started_at timestamptz,
  processing_completed_at timestamptz,
  questionnaire_type text,
  questionnaire_filename text
);

-- questions table
create table questions (
  id text primary key,  -- e.g. "q_001"
  session_id uuid references sessions(id) on delete cascade,
  text text not null,
  answer_format text,
  category text,
  original_row int
);

-- answers table
create table answers (
  question_id text references questions(id) on delete cascade,
  session_id uuid references sessions(id) on delete cascade,
  draft_answer text,
  evidence_coverage text,
  ai_certainty int,
  answer_tone text,
  status text default 'draft',
  needs_review boolean,
  evidence_sources jsonb,
  updated_at timestamptz default now(),
  primary key (question_id, session_id)
);

-- audit_events table (replaces audit.log file)
create table audit_events (
  event_id uuid primary key,
  ts timestamptz not null,
  action text not null,
  actor text,
  resource_type text,
  resource_id text,
  outcome text,
  request_id text,
  detail jsonb
);
-- Row-level security: audit_events should be INSERT-only for app role
```

---

## Security Checklist Before Production

Status updated 2026-03-09.

- [x] Rotate all API keys that were shared in plaintext — done
- [x] Enable GitHub branch protection on `main` — PR required, no force push, no deletion
- [x] Security headers + in-memory rate limiter — live via `security.py`
- [x] Append-only audit trail — live via `audit.py` / `audit.log`
- [ ] Add authentication (Supabase Auth recommended) — Phase 2
- [ ] Set `ENVIRONMENT=production` to enable HSTS + strict CSP — pre-launch
- [ ] Verify TLS termination at load balancer/CDN — pre-launch
- [ ] Execute DPAs with Groq, Google, Anthropic, Mixpanel, Supabase — pre-launch blocker
- [ ] Publish privacy notice at `/privacy` — pre-launch
- [ ] Enable Dependabot for dependency CVE scanning — pre-launch
- [ ] Ship `audit.log` to a SIEM or Supabase `audit_events` table — Phase 2
- [ ] Replace in-memory rate limiter with Redis — Phase 2

---

## Contact / Ownership

| Role | Owner | Contact |
|---|---|---|
| Engineering | Samrat Talukder | — |
| AI/LLM | Claude (Sonnet 4.6) | — |
| Compliance review | TBD | — |
