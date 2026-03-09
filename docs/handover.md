# Agent / Engineer Handover Document
**Product**: Seques — Security Questionnaire Co-Pilot
Last updated: 2026-03-09

This document is the single source of truth for any agent or engineer picking up this codebase.
Read this first, then `docs/architecture.md`.

---

## Current State — Phase 2 active (2026-03-10)

Phase 1 is **complete**. Phase 2 core is now live:
auth gate active (Supabase Magic Link), Supabase migrations run, security middleware enabled, test suite green (185 tests).

### Capability table

| Capability | Status | Notes |
|---|---|---|
| Multi-provider LLM (Groq / Google / Anthropic) | Live | `LLM_PROVIDER` env var switches provider at runtime |
| Groq key pool (up to 19 keys) | Live | `GROQ_API_KEY`, `GROQ_API_KEY_2` … `GROQ_API_KEY_19`; TPD-aware blacklisting |
| Questionnaire parsing (Excel, PDF, CSV, paste) | Live | `parser.py` |
| Compliance doc ingestion (PDF, DOCX) | Live | 32KB total budget, 16KB per doc (`DOC_CHAR_BUDGET`, `DOC_CHAR_LIMIT`) |
| Draft-first answer generation | Live | `engine.py`; assertive / hedged tones; never blank |
| Dynamic `max_tokens` per answer format | Live | yes_no → 512, yes_no_evidence → 900, default → 2048 |
| Sequential processing (default) | Live | `ANSWER_CONCURRENCY=1`, `QUESTION_DELAY_S=1.5` |
| Parallel processing (optional) | Available | Set `ANSWER_CONCURRENCY > 1`; ThreadPoolExecutor; 6-8× faster but not the default |
| SSE streaming of answers | Live | `GET /api/sessions/{id}/stream` |
| Landing page | Live | First screen in React SPA; hero, highlights, "where we stand", phase 2 roadmap, CTA |
| Review / edit / approve / un-approve UI | Live | `Review.jsx` + `QuestionCard.jsx` |
| Session URL persistence | Live | `?s=<sessionId>` in URL; hard refresh restores to Review screen |
| Tab labels | Live | "Answered" and "Flagged" (renamed from "Ready" / "Review") |
| Excel + PDF export | Live | `export.py` |
| Structured JSON logging + request tracing | Live | `observability.py` |
| Append-only audit trail | Live | `audit.py` → `audit.log` |
| Mixpanel analytics | Live | Token configured; 5-step funnel tracked |
| Security headers middleware | **Live** | Active in `main.py` — X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy |
| In-memory rate limiter | **Live** | 30 req/min per IP; Redis replacement is Phase 3 |
| Auth gate (App.jsx) | **Live** | Magic Link gate active — `if (supabase && !user) return <Auth />` |
| JWT validation (backend) | **Live** | `verify_token` on all session/answer routes; enabled via `SUPABASE_JWT_SECRET` |
| Per-user session cap | **Live** | `MAX_SESSIONS_PER_USER=3`; enforced when auth is enabled |
| Max questions per session | Live | `MAX_QUESTIONS_PER_SESSION=100`; enforced on questionnaire upload |
| Supabase DB schema | **Live** | `001_initial_schema.sql` run 2026-03-10 |
| RLS policies | **Live** | `002_rls_policies.sql` run 2026-03-10 — per-user isolation |
| Session restore from Supabase | **Live** | `_restore_session()` loads from Supabase on cache miss |
| Test suite | **Green** | 185 tests passing — test_api, test_engine, test_llm, test_parser, test_ingest, test_audit |

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
│   ├── main.py           ← FastAPI app; all routes; auth scaffolding; session store
│   ├── engine.py         ← LLM answering logic; draft-first generation
│   ├── parser.py         ← Questionnaire parsing (Excel, PDF, CSV, text)
│   ├── ingest.py         ← Compliance doc ingestion (PDF, DOCX)
│   ├── llm.py            ← Multi-provider LLM wrapper; Groq key pool; backoff
│   ├── models.py         ← Pydantic data models
│   ├── export.py         ← Excel + PDF generation
│   ├── observability.py  ← Structured logging + request tracing
│   ├── audit.py          ← Immutable audit trail
│   ├── analytics.py      ← Mixpanel event tracking
│   ├── security.py       ← Security headers + rate limiting (currently disabled)
│   ├── database.py       ← Supabase CRUD scaffold
│   ├── requirements.txt
│   ├── .env              ← Secrets (gitignored)
│   ├── .env.example      ← Template — copy to .env
│   └── migrations/
│       ├── 001_initial_schema.sql  ← sessions, questions, answers, audit_events
│       └── 002_rls_policies.sql    ← RLS policies (run after auth activated)
├── frontend/
│   ├── .env.example      ← VITE_API_URL, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
│   └── src/
│       ├── App.jsx        ← Root; screen state; URL persistence; no auth gate currently
│       ├── api.js         ← All fetch calls; setAuthToken() wired but not called yet
│       ├── supabase.js    ← Supabase client (null if env vars absent)
│       └── screens/
│           ├── Landing.jsx    ← First screen; marketing + CTA
│           ├── Upload.jsx     ← Step 1: upload docs + questionnaire
│           ├── Processing.jsx ← Step 2: SSE stream + terminal log
│           ├── Review.jsx     ← Step 3: filter tabs (All/Answered/Flagged/Gaps)
│           ├── Export.jsx     ← Step 4: download Excel or PDF
│           └── Auth.jsx       ← Supabase magic link screen (scaffolded, not in flow)
└── docs/
    ├── handover.md          ← THIS FILE
    ├── architecture.md      ← System diagram + module map
    ├── runbook.md           ← Ops procedures
    └── compliance/
        ├── data_inventory.md
        ├── SOC2_controls.md
        ├── GDPR_controls.md
        └── ISO27001_controls.md
```

---

## Running Locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in at least one LLM key
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173 (or next available port)
```

Swagger UI: http://localhost:8000/docs
Landing page: first screen at the frontend URL

---

## Exact Runtime Configuration (as shipped)

```
ANSWER_CONCURRENCY=1       # sequential — one question at a time
QUESTION_DELAY_S=1.5       # 1.5s pause between LLM calls (TPM headroom)
DOC_CHAR_BUDGET=32000      # total chars across all uploaded docs
DOC_CHAR_LIMIT=16000       # max chars per individual doc
GROQ_API_KEY_1 … (up to GROQ_API_KEY_19)
```

**LLM models (as of 2026-03-09):**
- Groq: `llama-3.3-70b-versatile`
- Anthropic: `claude-haiku-4-5-20251001`
- Google: `gemini-2.0-flash`

---

## Key Decisions & Why

| Decision | Reason |
|---|---|
| FastAPI + uvicorn | Async-native, auto-generates OpenAPI/Swagger, Python ecosystem |
| In-memory sessions | MVP simplicity; Supabase persistence is Phase 2 |
| Multi-provider LLM (llm.py) | No vendor lock-in; free providers (Groq, Google) for development |
| `LLM_PROVIDER` env var | Single switch, no code changes needed to swap models |
| Append-only `audit.log` | Simplest SOC 2 CC7.2 implementation |
| `ANSWER_CONCURRENCY=1` default | Reliability — parallel mode hit ordering anomalies under Groq rate limits |
| 32KB total / 16KB per-doc budget | Prevents runaway token costs on Groq free tier |
| Mixpanel analytics | PII-free funnel tracking; Mixpanel free tier generous |
| Tailwind + React | Rapid UI iteration; no design system dependencies |
| Landing page as first React screen | No separate deploy; same Vite app; consistent dark theme |
| Auth scaffolded but not gated | App must work today without credentials; gate activates when Supabase is configured |
| Security middleware disabled | Was intercepting exceptions before CORS headers applied; revisit in Phase 2 |

---

## Known Gaps (do not re-investigate — already documented)

| Gap | Impact | Phase 2 Fix |
|---|---|---|
| No auth gate | Any caller can create/read sessions | Wire Auth.jsx into App.jsx; add `Depends(verify_token)` to all routes |
| In-memory sessions | Restart wipes all sessions | Wire Supabase persistence (scaffold in `database.py`) |
| Security middleware disabled | No CSP / HSTS / rate limiting in process | Fix middleware exception handling; re-enable |
| 32KB doc budget | Large SOC 2 reports lose detail beyond ~7 pages | RAG with pgvector in Phase 2 |
| No DPAs signed | Pre-launch blocker for GDPR/SOC 2 | Execute DPAs with Groq, Google, Anthropic, Mixpanel, Supabase |
| JWT only on POST /api/sessions | Other session routes unprotected | Add `Depends(verify_token)` to all session/answer routes |
| _user_sessions dict resets | Per-user session cap lost on restart | Move to Supabase query when persistence is wired |
| password-protected .docx | Will raise error; not gracefully handled | Catch and return user-friendly error |

---

## Phase 2 — DONE (2026-03-10)

- [x] Run Supabase migrations (001 + 002)
- [x] Activate auth gate (App.jsx + backend verify_token on all routes)
- [x] Security middleware enabled (SecurityHeadersMiddleware + RateLimitMiddleware)
- [x] Supabase write-through persistence + session restore
- [x] Test suite green (185 tests)

## Phase 3 — What to Build Next

Priority order:

1. **RAG for large docs** — chunk compliance docs, embed with `text-embedding-3-small`, store in Supabase `pgvector`. Retrieve top-k chunks per question instead of flat 32KB char budget.
2. **Redis rate limiter** — replace `security.py` in-memory dict with Redis-backed counter. Required before multi-worker deploy.
3. **Parallel processing** — revisit `ANSWER_CONCURRENCY > 1` with Redis rate budget tracking. Goal: 10× concurrency as reliable default.
4. **Sign DPAs** — legal task, not engineering. Block production launch on this.

---

## Security Checklist Before Production

Status updated 2026-03-09.

- [x] Rotate all API keys that were shared in plaintext
- [x] Enable GitHub branch protection on `main`
- [x] Append-only audit trail — live via `audit.py` / `audit.log`
- [x] Auth scaffolded — JWT validation in `verify_token`, RLS migration ready
- [x] Activate auth gate in App.jsx and all backend routes — done 2026-03-10
- [x] Run RLS migration (`002_rls_policies.sql`) in Supabase dashboard — done 2026-03-10
- [x] Re-enable `SecurityHeadersMiddleware` + `RateLimitMiddleware` — done 2026-03-10
- [ ] Set `ENVIRONMENT=production` to enable HSTS + strict CSP — pre-launch
- [ ] Verify TLS termination at load balancer/CDN — pre-launch
- [ ] Execute DPAs with Groq, Google, Anthropic, Mixpanel, Supabase — **pre-launch blocker**
- [ ] Publish privacy notice at `/privacy` — pre-launch
- [ ] Enable Dependabot for dependency CVE scanning — pre-launch
- [ ] Ship `audit.log` to Supabase `audit_events` table — Phase 2
- [ ] Replace in-memory rate limiter with Redis — Phase 2

---

## Supabase Schema (Phase 2 Target)

Run `migrations/001_initial_schema.sql` then `migrations/002_rls_policies.sql` in the Supabase SQL editor.

Key tables: `sessions` (with `user_id` FK to `auth.users`), `questions`, `answers`, `audit_events`.
RLS policies: per-user ownership on sessions/questions/answers; INSERT-only audit via service role.

---

## Contact / Ownership

| Role | Owner |
|---|---|
| Engineering | Samrat Talukder |
| AI/LLM | Claude (Sonnet 4.6) |
| Compliance review | TBD |
