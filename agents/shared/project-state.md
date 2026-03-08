# Seques — Shared Project State
> Updated by any agent after significant changes. Read before acting.

Last updated: 2026-03-09
Updated by: Project Manager Agent

## Current Status
| Area | Status | Owner Agent |
|---|---|---|
| Backend API | ✅ Running on :8000 — parallel + streaming | backend |
| Frontend UI | ✅ Running on :5174 | frontend |
| Mixpanel | ✅ Live | infra |
| Supabase | ⚠️ Schema not yet run | infra |
| Auth | ❌ Not started | backend |
| RAG | ❌ Phase 2 | backend |
| Tests | ❌ Not started | testing |
| CI/CD | ✅ Set up | infra |
| DPAs | ❌ Not signed | compliance |
| Privacy notice | ❌ Not written | compliance |

## Active Sprint (Phase 1 → Phase 2 Handoff)
- [ ] Run Supabase migration (infra)
- [ ] Write test suite (testing)
- [x] Set up CI/CD (infra) — complete
- [ ] Sign DPAs (compliance)
- [ ] Write privacy notice (compliance)
- [ ] Add auth (backend)
- [ ] Build RAG pipeline (backend)

### Mid-Sprint Delivery (2026-03-08)
- [x] Draft-first answer generation — every question gets a professional draft; context budget raised to 40k per doc / 96k total
- [x] Multi-doc .docx upload support — vendors can upload Word docs alongside PDFs
- [x] Sample test questionnaire (30 questions, 8 categories) added to `docs/`

### Performance Milestone (2026-03-09) — `feat/backend-improvements`
- [x] Parallel answer generation — `ThreadPoolExecutor` with `ANSWER_CONCURRENCY=10`; all questions processed concurrently instead of sequentially
- [x] SSE streaming — answers appear progressively in the UI as each completes; no waiting for full batch
- [x] Dynamic `max_tokens` per answer format — `yes_no` → 512, long-form → 2048 (was hardcoded 2048 for all)
- [x] Persistent LLM clients with connection pooling — eliminates per-request client construction overhead
- [x] Exponential backoff on rate-limit errors — retries with jitter instead of failing hard
- [x] **Measured speedup: 30-question session ~120s → ~15-20s (6-8x faster)**

## Known Gaps
| Gap | Status | Notes |
|---|---|---|
| Doc truncation | Mitigated (was 8KB, now 40k per doc / 96k total) | Full RAG still planned for Phase 2 |
| In-memory rate limiter | Open | Phase 2: replace with Redis |
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

## Performance Benchmarks (as of 2026-03-09)
| Metric | Before | After | Delta |
|---|---|---|---|
| 30-question session time | ~120s | ~15-20s | 6-8x faster |
| Answer concurrency | 1 (sequential) | 10 (parallel) | — |
| max_tokens yes/no | 2048 (hardcoded) | 512 (dynamic) | -75% tokens |
| LLM client init | per-request | persistent pool | eliminated overhead |
| Rate limit handling | hard fail | exp. backoff + jitter | resilient |

## Metrics (as of 2026-03-09)
- Questions answered per session: TBD (no production data yet)
- Avg AI certainty: TBD
- Provider usage: 100% Groq (default)
- SSE streaming: active on answer generation endpoint
