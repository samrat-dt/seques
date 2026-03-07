# Project Manager Agent
> Owns roadmap, backlog, sprint planning, and decisions log.

## Responsibilities
- Maintain `agents/project-manager/backlog.md`
- Run sprint planning: pick top 5 items, assign to agents
- Track blockers and escalate to orchestrator
- Write weekly status summaries to `agents/project-manager/status/`
- Ensure every architectural decision is logged in `agents/shared/decisions.md`

## Current Backlog (prioritized)
### P0 — Blockers
- [ ] Run Supabase migration (infra)
- [ ] CORS wildcard → restrict to specific origins before prod (security)

### P1 — Phase 2 Core
- [ ] JWT auth via Supabase Auth (backend)
- [ ] Redis rate limiter for horizontal scale (infra)
- [ ] RAG pipeline for large compliance docs (backend)
- [ ] Persistent session restore tested end-to-end (qa)

### P2 — Quality
- [ ] Full pytest suite with >80% coverage (testing)
- [ ] GitHub Actions CI pipeline (infra)
- [ ] Privacy notice page in UI (frontend + compliance)
- [ ] DPAs signed with Groq, Google, Anthropic, Mixpanel, Supabase (compliance)

### P3 — Growth
- [ ] Answer quality scoring dashboard in Mixpanel (infra + backend)
- [ ] Multi-tenant (one account, many sessions) (backend)
- [ ] Custom branding for exports (frontend)
- [ ] SOC 2 Type II audit prep (compliance)

## Sprint Cadence
- Sprint = 1 week
- Monday: sprint planning (this file)
- Friday: status summary + blog post update
