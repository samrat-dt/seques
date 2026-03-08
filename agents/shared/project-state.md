# Seques — Shared Project State
> Updated by any agent after significant changes. Read before acting.

Last updated: 2026-03-08
Updated by: Project Manager Agent

## Current Status
| Area | Status | Owner Agent |
|---|---|---|
| Backend API | ✅ Running on :8000 | backend |
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

## Metrics (as of 2026-03-08)
- Questions answered per session: TBD (no production data yet)
- Avg AI certainty: TBD
- Provider usage: 100% Groq (default)
