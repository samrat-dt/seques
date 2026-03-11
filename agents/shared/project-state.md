# Seques — Shared Project State
> Updated by any agent after significant changes. Read before acting.

Last updated: 2026-03-11
Updated by: Orchestrator

## Current Status
| Area | Status | Owner Agent |
|---|---|---|
| Backend API | Production — Railway (Docker) — https://seques-backend-production.up.railway.app | backend |
| Frontend UI | Production — Vercel (auto-deploy from main) — https://seques.vercel.app | frontend |
| Auth | Access-code gate (default: seques2026, overridable via VITE_ACCESS_CODE) — App.jsx | frontend |
| LLM | Groq (llama-3.3-70b-versatile, default) + Anthropic (claude-haiku-4-5-20251001, configured) | backend |
| Supabase DB | Live — sessions, questions, answers, audit_events tables active | infra |
| Security middleware | Active — SecurityHeadersMiddleware + RateLimitMiddleware (30 req/min per IP) | backend |
| Mixpanel | Live | infra |
| JWT/backend auth | DISABLED — _AUTH_ENABLED=False in main.py; re-enable with AUTH_ENABLED=true + SUPABASE_JWT_SECRET | backend |
| Google LLM | Not configured — no API key on Railway | backend |
| SSE endpoint | Exists in backend but NOT used by frontend | backend |
| RAG | Phase 3 backlog | backend |
| Redis | Phase 3 backlog | infra |
| DPAs | Not signed (pre-launch blocker) | compliance |

## Version
**v1.0.0-stable** — git tag created, confirmed working end-to-end in production.

## Deployment
| Service | URL | Platform |
|---|---|---|
| Frontend | https://seques.vercel.app | Vercel, auto-deploy from main |
| Backend | https://seques-backend-production.up.railway.app | Railway, Docker |

## Phase 1 — COMPLETE (v0.3.0-checkpoint)
See decisions.md for full history. Key items:
- Multi-provider LLM, draft-first answer generation, sequential processing, SSE endpoint
- Landing page, Upload, Processing (then SSE, now polling), Review, Export screens
- Audit log, Mixpanel analytics, security headers

## Phase 2 — COMPLETE (v0.4.0, 2026-03-10)
- Supabase migrations run (001 + 002)
- Auth gate attempted (Supabase Magic Link) — later removed, replaced with access-code
- Security middleware active
- Supabase write-through persistence + session restore

## v1.0.0-stable — CONFIRMED WORKING (2026-03-11)

### What is working in production
- [x] Access-code auth gate (localStorage, default: seques2026)
- [x] Upload compliance docs — PDF, DOCX, up to 50MB
- [x] Upload questionnaire — PDF, Excel, pasted text
- [x] AI answer generation — Groq (default) + Anthropic (configured)
- [x] Processing screen — polling-based at 1s interval (NOT SSE)
- [x] Review + edit + approve + un-approve answers
- [x] Export to Excel and PDF (fetch-based with auth token, not direct links)
- [x] Sessions persist to Supabase DB
- [x] Rate limiting: 30 req/min per IP (in-memory)
- [x] Security headers active

### What is NOT active
- Supabase magic link auth: REMOVED (broken "invalid api key"), replaced with access-code
- JWT/Supabase auth on backend: DISABLED (_AUTH_ENABLED=False by default)
- Google LLM: not configured (no API key on Railway)
- SSE stream endpoint: exists in backend but not used by frontend (EventSource can't send auth headers)
- RAG: not implemented (32KB doc limit applies)
- Redis: not implemented (in-memory rate limiter)
- Parallel processing: ANSWER_CONCURRENCY=1 (sequential default)

## Frontend Screen Inventory (ground truth as of 2026-03-11)

### App flow
`landing` → `auth` (access-code gate) → `upload` → `processing` → `review` → `export`

State lives in `App.jsx`. No router library. Screen is a string state variable.
Auth check is access-code stored in localStorage; `Auth.jsx` is a simple code-entry form.

### Processing (`screens/Processing.jsx`)
- Terminal-style log panel
- Polls `/api/sessions/<id>/status` at 1s intervals (NOT SSE/EventSource)
- Reason: EventSource cannot send Authorization headers → 401 in production
- On `processing === false && processed > 0`: calls `getAnswers` then fires `onDone(data)`

### Export (`screens/Export.jsx`)
- Download buttons use `fetch()` + blob URL (NOT direct `<a href>` links)
- Reason: direct links can't include the Authorization header → 401 in production
- Both Excel and PDF exports use `getAuthToken()` helper from api.js

### api.js
- `getAuthToken()` reads access code from localStorage
- Every request includes `Authorization: Bearer <token>` header
- Exports: `getProviders`, `createSession`, `uploadDocs`, `uploadQuestionnaire`, `processQuestionnaire`, `getStatus`, `getAnswers`, `updateAnswer`, `downloadExport` (fetch+blob)

### supabase.js
- Exports `null` — Supabase client disabled (env vars set but client intentionally null)
- App.jsx does NOT use Supabase client for auth

## Backend Key Facts (as of 2026-03-11)
- `main.py`: `_AUTH_ENABLED = False` (hardcoded default); set `AUTH_ENABLED=true` env var to enable JWT
- `security.py`: SecurityHeadersMiddleware + RateLimitMiddleware active
- `engine.py`: sequential processing (ANSWER_CONCURRENCY=1)
- `database.py`: Supabase CRUD with graceful fallback if not configured
- LLM_PROVIDER: groq (default); ANTHROPIC_API_KEY configured on Railway

## Environment Variables — Production State

### Backend (Railway)
| Var | Status |
|---|---|
| GROQ_API_KEY | Configured |
| ANTHROPIC_API_KEY | Configured |
| SUPABASE_URL | Configured |
| SUPABASE_SERVICE_KEY | Configured |
| SUPABASE_JWT_SECRET | Configured but AUTH_ENABLED not set → auth off |
| LLM_PROVIDER | groq |
| ENVIRONMENT | production |
| ANSWER_CONCURRENCY | 1 |

### Frontend (Vercel)
| Var | Status |
|---|---|
| VITE_API_URL | https://seques-backend-production.up.railway.app |
| VITE_SUPABASE_URL | Set but Supabase client exports null |
| VITE_SUPABASE_ANON_KEY | Set but Supabase client exports null |
| VITE_ACCESS_CODE | Not set — defaults to seques2026 in code |

## Phase 3 — Next (priority order)
1. RAG for large docs (pgvector, chunk + embed compliance docs) — removes 32KB limit
2. Parallel processing (ANSWER_CONCURRENCY=10 reliable) — 6-8x faster
3. Redis rate limiter — for horizontal scaling
4. Multi-user / team accounts — proper invite-based auth
5. Session history — list past sessions, re-open them
6. Answer templates — pre-load standard approved language
7. Custom export formats — map into prospect's Excel template
8. Bring-your-own-docs library — upload once, reuse across questionnaires

## Known Gaps
| Gap | Status | Notes |
|---|---|---|
| Doc truncation | 32KB total / 16KB per doc | Full RAG Phase 3 |
| In-memory rate limiter | Open | Phase 3: Redis |
| No user-level auth | Open | Phase 3: invite-based multi-user |
| No DPAs signed | Open | Pre-launch blocker |
| Password-protected .docx | Open | Will raise error; graceful handling needed |
| .docx text boxes / complex tables | Open | python-docx misses these; extraction gap |

## Decisions
See `agents/shared/decisions.md`
