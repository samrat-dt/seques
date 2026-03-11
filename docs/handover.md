# Agent / Engineer Handover Document
**Product**: Seques — Security Questionnaire Co-Pilot
Last updated: 2026-03-11

This document is the single source of truth for any agent or engineer picking up this codebase.
Read this first, then `docs/architecture.md`.

---

## What This Product Does

Seques is a B2B SaaS tool that helps security teams respond to vendor questionnaires faster.
A user uploads their compliance documents (SOC 2 reports, ISO 27001 certs, policies)
and the prospect's questionnaire (PDF, Excel, or pasted text). An LLM reads the evidence
and drafts every answer. The user then reviews, edits, approves, and exports the response.

---

## Current State — v1.0.0-stable (2026-03-11)

Production is fully working end-to-end. This is the stable baseline for Phase 3.

### Capability table

| Capability | Status | Notes |
|---|---|---|
| Access-code auth gate | Live | `Auth.jsx` code-entry form; code checked against `VITE_ACCESS_CODE` (default: seques2026); stored in localStorage |
| Multi-provider LLM (Groq / Anthropic) | Live | `LLM_PROVIDER` env var; Groq default, Anthropic configured |
| Google LLM | Not configured | No API key on Railway; do not reference as active |
| Groq key pool (up to 19 keys) | Live | `GROQ_API_KEY` through `GROQ_API_KEY_19`; TPD-aware blacklisting |
| Questionnaire parsing (Excel, PDF, CSV, paste) | Live | `parser.py` |
| Compliance doc ingestion (PDF, DOCX) | Live | 32KB total / 16KB per doc (`DOC_CHAR_BUDGET`, `DOC_CHAR_LIMIT`) |
| Draft-first answer generation | Live | `engine.py`; assertive / hedged tones; never blank |
| Sequential processing (default) | Live | `ANSWER_CONCURRENCY=1`, `QUESTION_DELAY_S=1.5` |
| Parallel processing (optional) | Available | Set `ANSWER_CONCURRENCY > 1`; not the default |
| Processing screen — polling | Live | `Processing.jsx` polls `/api/sessions/{id}/status` at 1s intervals |
| SSE streaming endpoint | Exists, unused | `/api/sessions/{id}/stream` in backend; NOT used by frontend (EventSource can't send auth headers) |
| Landing page | Live | First screen in React SPA |
| Review / edit / approve / un-approve UI | Live | `Review.jsx` + `QuestionCard.jsx` |
| Session URL persistence | Live | `?s=<sessionId>` in URL; hard refresh restores session |
| Excel + PDF export | Live | fetch+blob pattern with auth token (not direct links) |
| Supabase DB persistence | Live | sessions, questions, answers, audit_events tables; graceful fallback if not configured |
| Structured JSON logging + request tracing | Live | `observability.py` |
| Append-only audit trail | Live | `audit.py` → `audit.log` + Supabase `audit_events` |
| Mixpanel analytics | Live | Token configured; PII-free funnel events |
| Security headers middleware | Live | Active in `main.py` — X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy |
| In-memory rate limiter | Live | 30 req/min per IP |
| JWT/Supabase auth on backend | Disabled | `_AUTH_ENABLED=False` in `main.py`; re-enable with `AUTH_ENABLED=true` + `SUPABASE_JWT_SECRET` |
| Supabase Magic Link auth | Removed | Was broken ("invalid api key"); replaced with access-code gate |
| RLS policies | Inactive | `002_rls_policies.sql` exists; not enforcing since JWT auth is off |
| RAG | Phase 3 backlog | 32KB doc limit applies |
| Redis | Phase 3 backlog | In-memory rate limiter only |
| DPAs | Not signed | Pre-launch blocker |

---

## Production URLs

| Service | URL | Platform |
|---|---|---|
| Frontend | https://seques.vercel.app | Vercel, auto-deploy from `main` |
| Backend | https://seques-backend-production.up.railway.app | Railway, Docker |
| Swagger | https://seques-backend-production.up.railway.app/docs | — |

---

## Repository Layout

```
seques/
├── backend/
│   ├── main.py           ← FastAPI app; all routes; _AUTH_ENABLED=False
│   ├── engine.py         ← LLM answering logic; draft-first generation
│   ├── parser.py         ← Questionnaire parsing (Excel, PDF, CSV, text)
│   ├── ingest.py         ← Compliance doc ingestion (PDF, DOCX)
│   ├── llm.py            ← Multi-provider LLM wrapper; Groq key pool; backoff
│   ├── models.py         ← Pydantic data models
│   ├── export.py         ← Excel + PDF generation
│   ├── observability.py  ← Structured logging + request tracing
│   ├── audit.py          ← Immutable audit trail
│   ├── analytics.py      ← Mixpanel event tracking
│   ├── security.py       ← Security headers + rate limiting
│   ├── database.py       ← Supabase CRUD; graceful fallback if not configured
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.toml      ← Docker build config; healthcheck /health
│   ├── .env              ← Secrets (gitignored)
│   ├── .env.example      ← Template — copy to .env
│   └── migrations/
│       ├── 001_initial_schema.sql  ← sessions, questions, answers, audit_events
│       └── 002_rls_policies.sql    ← RLS policies (for future JWT auth)
├── frontend/
│   ├── .env.example      ← VITE_API_URL, VITE_ACCESS_CODE
│   ├── vercel.json       ← Build: cd frontend && rm -rf dist && npm run build
│   └── src/
│       ├── App.jsx        ← Root; screen state machine; access-code auth gate
│       ├── api.js         ← All fetch calls; getAuthToken() reads localStorage
│       ├── supabase.js    ← Exports null (Supabase client disabled)
│       └── screens/
│           ├── Landing.jsx    ← First screen; marketing + CTA
│           ├── Auth.jsx       ← Access-code entry form (not Supabase Magic Link)
│           ├── Upload.jsx     ← Step 1: upload docs + questionnaire
│           ├── Processing.jsx ← Step 2: polling-based progress (1s interval)
│           ├── Review.jsx     ← Step 3: filter tabs (All/Answered/Flagged/Gaps)
│           └── Export.jsx     ← Step 4: fetch+blob Excel and PDF downloads
└── docs/
    ├── handover.md          ← THIS FILE
    ├── architecture.md      ← System diagram + module map
    ├── runbook.md           ← Ops procedures
    └── compliance/
```

---

## Running Locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in at least GROQ_API_KEY or ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local
# Set VITE_API_URL=http://localhost:8000 in .env.local
npm run dev
# Opens at http://localhost:5173 (or next available port)
```

Access code locally: `seques2026` (or whatever `VITE_ACCESS_CODE` is set to).

Swagger UI: http://localhost:8000/docs

---

## Auth — How It Works

### Frontend auth (access-code gate)
- `App.jsx` checks localStorage for `seques_auth_token`
- If absent, renders `Auth.jsx` — a simple code-entry form
- User enters the access code; it's stored in localStorage as `seques_auth_token`
- Every API call includes `Authorization: Bearer <code>` via `getAuthToken()` in `api.js`
- To change the code: set `VITE_ACCESS_CODE` env var in Vercel (rebuilds required)
- Default code if env var not set: `seques2026`

### Backend auth
- `_AUTH_ENABLED = False` in `main.py` — backend does NOT validate JWT tokens
- It accepts any Bearer token (including the plain access-code string)
- To enable proper JWT validation: set `AUTH_ENABLED=true` + `SUPABASE_JWT_SECRET` on Railway

### Supabase client
- `supabase.js` exports `null` — the Supabase JS client is intentionally disabled
- Env vars `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set in Vercel but the client is not initialised

---

## Environment Variables — Production State

### Backend (Railway)
| Var | Status | Notes |
|---|---|---|
| `GROQ_API_KEY` | Configured | Default LLM provider |
| `ANTHROPIC_API_KEY` | Configured | Switch with `LLM_PROVIDER=anthropic` |
| `SUPABASE_URL` | Configured | DB persistence active |
| `SUPABASE_SERVICE_KEY` | Configured | Service role key for CRUD |
| `SUPABASE_JWT_SECRET` | Configured | JWT validation off — `AUTH_ENABLED` not set |
| `LLM_PROVIDER` | `groq` | Default |
| `ENVIRONMENT` | `production` | Affects security headers |
| `ANSWER_CONCURRENCY` | `1` | Sequential processing |

### Frontend (Vercel)
| Var | Status | Notes |
|---|---|---|
| `VITE_API_URL` | Configured | `https://seques-backend-production.up.railway.app` |
| `VITE_SUPABASE_URL` | Set but unused | Supabase client exports null |
| `VITE_SUPABASE_ANON_KEY` | Set but unused | Supabase client exports null |
| `VITE_ACCESS_CODE` | Not set | Defaults to `seques2026` in code |

---

## Exact Runtime Configuration (as shipped)

```
ANSWER_CONCURRENCY=1       # sequential — one question at a time
QUESTION_DELAY_S=1.5       # 1.5s pause between LLM calls (TPM headroom)
DOC_CHAR_BUDGET=32000      # total chars across all uploaded docs
DOC_CHAR_LIMIT=16000       # max chars per individual doc
```

**LLM models (as of 2026-03-11):**
- Groq: `llama-3.3-70b-versatile` (default)
- Anthropic: `claude-haiku-4-5-20251001` (configured, available)
- Google: `gemini-2.0-flash` (not configured — no API key)

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| Access-code auth (not Supabase Magic Link) | Magic Link returned "invalid api key" in production; access-code unblocked immediately |
| Polling in Processing (not SSE) | `EventSource` cannot send `Authorization` headers — SSE returned 401; polling works |
| fetch+blob for exports (not direct links) | Direct `<a href>` bypasses JS headers — returned 401; fetch+blob pattern includes auth |
| `_AUTH_ENABLED=False` default | Frontend uses access-code, not JWT; backend JWT validation would reject all requests |
| `ANSWER_CONCURRENCY=1` default | Parallel mode hit ordering anomalies under Groq rate limits; reliability beats speed at this scale |
| 32KB total / 16KB per-doc budget | Prevents runaway token costs; RAG will replace this in Phase 3 |
| `supabase.js` exports null | Supabase client was not initialising correctly in production; disabled intentionally |

---

## Known Gaps (do not re-investigate — already documented)

| Gap | Impact | Phase 3 Fix |
|---|---|---|
| 32KB doc budget | Large SOC 2 reports lose detail beyond first ~7 pages | RAG with pgvector |
| In-memory rate limiter | Resets on restart; doesn't share state across workers | Redis |
| No per-user auth | All sessions share one access code | Invite-based multi-user accounts |
| No DPAs signed | Pre-launch blocker for GDPR/SOC 2 | Execute DPAs with Groq, Anthropic, Mixpanel, Supabase |
| Password-protected .docx | Will raise error; not gracefully handled | Catch and return user-friendly error |
| .docx text boxes / complex tables | python-docx misses these; extraction gap | Better parser or convert-to-PDF upstream |

---

## Phase 3 — What to Build Next (priority order)

1. **RAG for large docs** — chunk compliance docs, embed with a small model, store in Supabase pgvector. Retrieve top-k chunks per question. Removes 32KB limit.
2. **Parallel processing** — revisit `ANSWER_CONCURRENCY > 1` with async LLM clients and Redis rate-budget tracking. Goal: 10× concurrency as reliable default.
3. **Redis rate limiter** — replace `security.py` in-memory dict. Required before multi-worker deploy.
4. **Multi-user / team accounts** — invite-based auth, per-user isolation, proper JWT.
5. **Session history** — list past sessions, re-open them from a dashboard.
6. **Answer templates** — pre-load standard approved language per control domain.
7. **Custom export formats** — map answers into the prospect's own Excel template.
8. **Bring-your-own-docs library** — upload compliance docs once, reuse across questionnaires.

---

## Security Checklist — Current Status

- [x] Rotate all API keys that were shared in plaintext
- [x] Enable GitHub branch protection on `main`
- [x] Append-only audit trail — live via `audit.py` / `audit.log`
- [x] Access-code auth gate — blocks unauthenticated access
- [x] SecurityHeadersMiddleware + RateLimitMiddleware active
- [x] Supabase DB persistence with service role key
- [ ] Sign DPAs with Groq, Anthropic, Mixpanel, Supabase — **pre-launch blocker**
- [ ] Enable per-user JWT auth when multi-user accounts ship (Phase 3)
- [ ] Publish privacy notice at `/privacy`
- [ ] Enable Dependabot for dependency CVE scanning
- [ ] Replace in-memory rate limiter with Redis (Phase 3)

---

## Contact / Ownership

| Role | Owner |
|---|---|
| Engineering | Samrat Talukder |
| AI/LLM | Claude (Sonnet 4.6) |
| Compliance review | TBD |
