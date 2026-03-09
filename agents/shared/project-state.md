# Seques — Shared Project State
> Updated by any agent after significant changes. Read before acting.

Last updated: 2026-03-09
Updated by: Frontend Audit Agent

## Current Status
| Area | Status | Owner Agent |
|---|---|---|
| Backend API | Running on :8001 — sequential + streaming (ANSWER_CONCURRENCY=1) | backend |
| Frontend UI | Running on :5175 — dark UI, landing page, URL persistence, un-approve | frontend |
| Mixpanel | Live | infra |
| Supabase | Schema not yet run in dashboard | infra |
| Auth | Auth.jsx + supabase.js exist but NOT wired into App.jsx — app runs without auth | backend/frontend |
| RAG | Phase 2 | backend |
| Tests | Not started (Phase 2) | testing |
| CI/CD | Set up | infra |
| DPAs | Not signed (pre-launch blocker) | compliance |
| Privacy notice | Not written | compliance |

## Phase 1 — COMPLETE (v0.3.0-checkpoint)
**Checkpoint tagged**: `v0.3.0-checkpoint`
**Servers**: backend :8001, frontend :5175

### Everything shipped in Phase 1
- [x] Multi-provider LLM abstraction (Groq default, Google, Anthropic)
- [x] In-memory session store with Supabase dual-write ready
- [x] Append-only audit log (local file + Supabase)
- [x] Mixpanel analytics (PII-free)
- [x] Security headers middleware (Python 3.9 compat)
- [x] Draft-first answer generation — every question gets a professional draft
- [x] Dynamic context budget — 40k per doc / 96k total (was 8k)
- [x] Multi-doc upload — PDF and .docx support
- [x] Sample 30-question test questionnaire in `docs/`
- [x] Parallel answer generation via ThreadPoolExecutor (`ANSWER_CONCURRENCY`)
- [x] SSE streaming — answers appear progressively in the UI
- [x] Dynamic `max_tokens` per answer format (yes_no → 512, long_text → 2048)
- [x] Persistent LLM clients with connection pooling
- [x] Exponential backoff on rate-limit errors (4 retries, jitter)
- [x] 5-key Groq API key pool with TPD-aware blacklisting
- [x] Sequential processing mode (`ANSWER_CONCURRENCY=1`) — reliability default
- [x] Dark UI merged
- [x] CI/CD pipeline set up
- [x] Landing page added as first screen in the React SPA (not a separate static page)
- [x] Session URL persistence via `?s=<sessionId>` query param — restores directly to Review on reload
- [x] Un-approve button on QuestionCard — reverts approved answer back to edited state
- [x] Review tab rename: "Ready" → "Answered", "Review" → "Flagged"
- [x] Auth.jsx (magic link) and supabase.js scaffolded for Phase 2 — not wired into app flow

### Performance Benchmarks (Phase 1 final)
| Metric | Before | After | Delta |
|---|---|---|---|
| 30-question session time | ~120s | ~15-20s | 6-8x faster (parallel) |
| Answer concurrency | 1 (sequential) | 1 (sequential, reliability default) | stable |
| max_tokens yes/no | 2048 (hardcoded) | 512 (dynamic) | -75% tokens |
| LLM client init | per-request | persistent pool | eliminated overhead |
| Rate limit handling | hard fail | exp. backoff + jitter | resilient |
| Doc context per session | 8k | 96k total / 40k per doc | 12x more content |

## Frontend Screen Inventory (ground truth as of 2026-03-09)

### App flow
`landing` → `upload` → `processing` → `review` → `export`

State lives in `App.jsx`. No router library. Screen is a string state variable.

### Landing (`screens/Landing.jsx`)
- First screen shown on app load (`useState('landing')` initial value)
- Marketing page: hero headline, v0.3.0 highlights, "Where we are today", Phase 2 roadmap, CTA
- Two "Try it now →" buttons and a nav button all call `onStart` which sets screen to `upload`
- No auth gate here — anyone can proceed
- Footer: © 2026 Seques, contact link to access@seques.ai

### Upload (`screens/Upload.jsx`)
- Fetches available LLM providers from `/api/providers` on mount; renders a provider selector
- Left panel: compliance docs (PDF/.docx) — drag-and-drop or file browse, multi-file, removable
- Right panel: prospect questionnaire — PDF/.xlsx/.xls upload OR paste text; mutually exclusive
- "Run it →" button disabled until at least 1 doc + questionnaire present
- On submit: `createSession` → `uploadDocs` → `uploadQuestionnaire` → `processQuestionnaire` → calls `onStart(sessionId)` which pushes `?s=<sessionId>` to URL and advances to `processing`

### Processing (`screens/Processing.jsx`)
- Terminal-style log panel with macOS traffic-light chrome
- Opens an `EventSource` SSE connection to `/api/sessions/<id>/stream`
- Parses each SSE event as JSON (one answer); increments counter and updates "Answering X of Y..." line
- Polls `/api/sessions/<id>/status` at 800ms intervals to discover total question count early
- On `[DONE]` event: calls `getAnswers` then fires `onDone(data)` which advances to `review`
- Error state shows "Something broke. Try again →" with `window.location.reload()`

### Review (`screens/Review.jsx`)
- Four filter tabs: **All**, **Answered**, **Flagged**, **Gaps**
  - "Answered" = `!needs_review && evidence_coverage !== 'none'`
  - "Flagged" = `needs_review === true`
  - "Gaps" = `evidence_coverage === 'none'`
- Header shows counts: total / answered / flagged / gaps / approved
- "Export →" button advances to export screen
- Renders `QuestionCard` for each filtered question

### QuestionCard (`components/QuestionCard.jsx`)
- Left-border accent: green=approved, blue=edited, amber=needs_review, grey=default
- Header badges: APPROVED (green), EDITED (blue), REVIEW (amber) — mutually exclusive priority
- Actions (top-right):
  - **Edit** button — always shown when not editing; opens inline textarea
  - **Un-approve** button — shown only when `status === 'approved'` and not editing; calls `onUpdate({ status: 'edited' })`
  - **Approve** button — shown only when `status !== 'approved'` and not editing; calls `onUpdate({ status: 'approved' })`
- Edit mode: textarea pre-filled with `draft_answer`; Save calls `onUpdate({ draft_answer, status: 'edited' })`, Cancel dismisses
- Footer metadata: evidence source file chips, coverage badge (Covered/Partial/No evidence), AI certainty %
- Suggested addition callout (info box with bulb icon) if `suggested_addition` present
- Coverage reason and certainty reason shown as italic muted text if present

### Export (`screens/Export.jsx`)
- Stats: approved count / total / gaps (gaps column shown only if > 0)
- Warning callouts: amber if any unapproved, red if any gaps
- Download buttons: "Download Excel" (primary amber), "Download PDF" (secondary surface)
- "← Back to review" text button
- Note: Export counts approved as `status === 'approved' || status === 'edited'`

### Session URL persistence (in `App.jsx`)
- On `handleProcessStart`: `window.history.pushState({}, '', ?s=${sid})`
- On mount: reads `?s=` param, calls `getStatus` — if `!processing && processed > 0` loads answers and jumps to `review`; on error strips the param
- On reset (`handleReset`): `window.history.replaceState({}, '', pathname)` to clear param

### Auth status
- `Auth.jsx` exists: Supabase magic link OTP flow, email input, "Check your email" confirmation state
- `supabase.js`: exports `supabase = (url && anonKey) ? createClient(url, anonKey) : null` — gracefully null when env vars absent
- `App.jsx` does NOT import Auth.jsx or supabase.js — **there is no auth gate in the running app**
- Auth is infrastructure for Phase 2; the app runs fully without Supabase env vars configured

### api.js
- `setAuthToken(token)` is implemented and exported — sets `_authToken` module variable
- Every `request()` call includes `Authorization: Bearer <token>` header if `_authToken` is set
- No code in the app currently calls `setAuthToken()` — it will be wired up when auth lands
- Exports: `getProviders`, `createSession`, `uploadDocs`, `uploadQuestionnaire`, `processQuestionnaire`, `getStatus`, `getAnswers`, `updateAnswer`, `getExcelUrl`, `getPdfUrl`

## Frontend Dependencies (package.json)
| Package | Version |
|---|---|
| react | ^18.2.0 |
| react-dom | ^18.2.0 |
| @supabase/supabase-js | ^2.98.0 |
| lucide-react | ^0.344.0 |
| vite | ^5.1.4 |
| @vitejs/plugin-react | ^4.2.1 |
| tailwindcss | ^3.4.1 |
| autoprefixer | ^10.4.18 |
| postcss | ^8.4.35 |

Note: `lucide-react` is installed but not used in any screen file (icons are inline SVGs). It may be a dependency kept for future use or a leftover.

## Phase 2 — PENDING (awaiting founder instructions)
**Status**: No sprint started. Awaiting direction.

### Known Phase 2 items (backlog)
- [ ] Run Supabase migration (infra)
- [ ] Write test suite (testing)
- [ ] Sign DPAs (compliance)
- [ ] Write privacy notice (compliance)
- [ ] Auth — wire Auth.jsx into App.jsx; call `setAuthToken()` in api.js with Supabase JWT (backend/frontend)
- [ ] Redis rate limiter (backend)
- [ ] RAG pipeline + pgvector (backend)
- [ ] CORS hardening (backend)
- [ ] SEC-009/SEC-011 — file size + MIME validation (security)

## Known Gaps
| Gap | Status | Notes |
|---|---|---|
| Doc truncation | Mitigated (96k total, 40k/doc) | Full RAG Phase 2 |
| In-memory rate limiter | Open | Phase 2: Redis |
| No auth | Open | Phase 2: wire Auth.jsx + supabase.js into App.jsx |
| No DPAs signed | Open | Pre-launch blocker |
| Password-protected .docx | Open | Will raise error; graceful handling needed |
| .docx text boxes / complex tables | Open | python-docx misses these; extraction gap |

## Blockers
- Supabase migration SQL not yet run in dashboard
- No auth = no multi-tenancy
- No DPAs signed (pre-launch blocker)

## Metrics (as of 2026-03-09)
- Questions answered per session: TBD (no production data yet)
- Avg AI certainty: TBD
- Provider usage: 100% Groq (default)
- SSE streaming: active on answer generation endpoint
- Groq key pool: 5 keys, TPD-aware blacklisting active

## Backlog
See `agents/project-manager/backlog.md`

## Decisions
See `agents/shared/decisions.md`
