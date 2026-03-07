# Agent / Engineer Handover Document
**Product**: Seques — Security Questionnaire Co-Pilot
Last updated: 2026-03-08

This document is the single source of truth for any agent or engineer picking up this codebase.
Read this first, then `docs/architecture.md`.

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

## Current Limitations (Known Phase 1 Gaps)

1. **No authentication** — any caller can create sessions and read any answer. Fix in Phase 2.
2. **In-memory only** — restart loses everything. Fix: Supabase persistence.
3. **Single process** — all sessions share one Python process. Fix: Celery workers.
4. **Rate limiter uses in-memory dict** — won't work with multiple workers. Fix: Redis.
5. **8KB doc truncation** — large SOC 2 reports lose detail. Fix: vector embeddings + RAG.
6. **No retry on LLM failure** — if Groq times out, that question errors. Fix: retry with backoff.

---

## Mixpanel Dashboard Setup (Manual — Pending Token)

Once you have a Mixpanel token:
1. Add it to `.env`: `MIXPANEL_TOKEN=your_token`
2. Restart backend
3. Run a test session — events will appear in Mixpanel Live View

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

- [ ] Rotate all API keys that were shared in plaintext (Groq key was exposed in chat — ROTATE NOW)
- [ ] Add authentication (Supabase Auth recommended)
- [ ] Set `ENVIRONMENT=production` to enable HSTS + strict CSP
- [ ] Verify TLS termination at load balancer/CDN
- [ ] Execute DPAs with Groq, Google, Anthropic, Mixpanel, Supabase
- [ ] Publish privacy notice at `/privacy`
- [ ] Enable GitHub branch protection on `main`
- [ ] Enable Dependabot for dependency CVE scanning
- [ ] Ship `audit.log` to a SIEM or Supabase `audit_events` table
- [ ] Replace in-memory rate limiter with Redis

---

## Contact / Ownership

| Role | Owner | Contact |
|---|---|---|
| Engineering | Samrat Talukder | — |
| AI/LLM | Claude (Sonnet 4.6) | — |
| Compliance review | TBD | — |
