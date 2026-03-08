# Seques — Shared Project State
> Updated by any agent after significant changes. Read before acting.

Last updated: 2026-03-09
Updated by: Project Manager Agent

## Current Status
| Area | Status | Owner Agent |
|---|---|---|
| Backend API | ✅ Running on :8001 — sequential + streaming (ANSWER_CONCURRENCY=1) | backend |
| Frontend UI | ✅ Running on :5175 — dark UI merged | frontend |
| Mixpanel | ✅ Live | infra |
| Supabase | ⚠️ Schema not yet run in dashboard | infra |
| Auth | ❌ Not started (Phase 2) | backend |
| RAG | ❌ Phase 2 | backend |
| Tests | ❌ Not started (Phase 2) | testing |
| CI/CD | ✅ Set up | infra |
| DPAs | ❌ Not signed (pre-launch blocker) | compliance |
| Privacy notice | ❌ Not written | compliance |

## Phase 1 — COMPLETE (v0.3.0-checkpoint)
**Checkpoint tagged**: `v0.3.0-checkpoint`
**Open PR**: #19 `feat/backend-improvements` → `main`
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

### Performance Benchmarks (Phase 1 final)
| Metric | Before | After | Delta |
|---|---|---|---|
| 30-question session time | ~120s | ~15-20s | 6-8x faster (parallel) |
| Answer concurrency | 1 (sequential) | 1 (sequential, reliability default) | stable |
| max_tokens yes/no | 2048 (hardcoded) | 512 (dynamic) | -75% tokens |
| LLM client init | per-request | persistent pool | eliminated overhead |
| Rate limit handling | hard fail | exp. backoff + jitter | resilient |
| Doc context per session | 8k | 96k total / 40k per doc | 12x more content |

## Phase 2 — PENDING (awaiting founder instructions)
**Status**: No sprint started. Awaiting direction.

### Known Phase 2 items (backlog)
- [ ] Run Supabase migration (infra)
- [ ] Write test suite (testing)
- [ ] Sign DPAs (compliance)
- [ ] Write privacy notice (compliance)
- [ ] Auth — Supabase JWT (backend)
- [ ] Redis rate limiter (backend)
- [ ] RAG pipeline + pgvector (backend)
- [ ] CORS hardening (backend)
- [ ] SEC-009/SEC-011 — file size + MIME validation (security)
- [ ] UI revamp (frontend)

## Known Gaps
| Gap | Status | Notes |
|---|---|---|
| Doc truncation | Mitigated (96k total, 40k/doc) | Full RAG Phase 2 |
| In-memory rate limiter | Open | Phase 2: Redis |
| No auth | Open | Phase 2: Supabase Auth |
| No DPAs signed | Open | Pre-launch blocker |
| Password-protected .docx | Open | Will raise error; graceful handling needed |
| .docx text boxes / complex tables | Open | python-docx misses these; extraction gap |

## Backlog
See `agents/project-manager/backlog.md`

## Last 5 Decisions
See `agents/shared/decisions.md`

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
