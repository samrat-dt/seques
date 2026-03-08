# Sprint 001 Retrospective + Sprint 002 Plan

---

## Sprint 001 — Retrospective

**Dates:** Phase 1 build session
**Status:** Complete

### Goal

Ship a working AI-powered security questionnaire co-pilot end-to-end: upload a vendor compliance document, upload a questionnaire, and receive AI-generated answers.

### What We Shipped

- Multi-provider LLM integration (Groq, Anthropic, Google Gemini) with runtime provider selection
- Supabase integration (database, RLS schema, session tracking, audit logging)
- Mixpanel analytics (anonymous events, no PII)
- Observability and audit trail (all API events logged with IP, timestamp, session ID)
- CI/CD pipeline (GitHub Actions, lint + test + deploy)
- Compliance documentation (privacy notice, DPA checklist, breach notification procedure)
- Multi-agent system (compliance, project-manager, and engineering agents)
- FastAPI backend with document parsing and in-memory LLM processing
- React/Next.js frontend with questionnaire upload and answer display

### Blockers Encountered

| Blocker | Impact | Resolution |
|---|---|---|
| CORS middleware bug — custom SecurityHeaders middleware caused `call_next` to fail on some routes | Blocked API from being callable from browser | Temporarily disabled custom middleware; wildcard CORS applied as workaround |
| Python 3.9 union type syntax (`X \| Y`) not supported in 3.9 | Test/CI failure | Reverted to `Optional[X]` / `Union[X, Y]` syntax for 3.9 compatibility |
| Supabase migration SQL not yet run | Schema not applied to production database | Workaround: migration SQL documented; user must paste into Supabase SQL editor manually |

### Velocity

High. The entire Phase 1 build was completed in a single focused session using multiple parallel agents. The multi-agent approach (compliance, PM, engineering running concurrently) significantly reduced sequential blockers.

### What Went Well

- Parallel agent execution allowed compliance and engineering work to proceed simultaneously
- Multi-provider LLM abstraction means no single-vendor lock-in from day one
- In-memory document processing kept the privacy surface minimal
- Audit logging implemented from the start, not bolted on later

### What to Improve

- Custom middleware needs proper async exception handling before re-enabling
- CORS wildcard is a security gap that must be resolved before production
- Supabase migration should be automated via CLI or seeded in CI, not manual
- No auth in Phase 1 means no user-level audit trails or session ownership

---

## Sprint 002 — Plan

**Status:** Planned
**Theme:** Production Hardening + RAG Pipeline

### Goals

| # | Goal | Owner | Priority |
|---|---|---|---|
| 1 | Implement Supabase Auth (JWT on all routes, user_id on sessions) | Engineering | P0 |
| 2 | Fix custom middleware (SecurityHeaders + RateLimit — wrap `call_next` in try/except) | Engineering | P0 |
| 3 | Restore restrictive CORS (replace wildcard with specific allowed origins) | Engineering | P0 |
| 4 | Run Supabase migration SQL (user pastes into dashboard or automate via CLI) | Engineering / User | P0 |
| 5 | Build RAG pipeline (chunk documents, embed with vector model, semantic search for relevant chunks) | Engineering | P1 |
| 6 | Finalize and publish privacy notice (linked from product UI) | Compliance / PM | P0 |
| 7 | Sign DPAs with all sub-processors (Supabase, Groq, Anthropic, Google, Mixpanel) | Legal / PM | P0 |
| 8 | Full pytest suite passing in CI (unit + integration tests, no skips) | Engineering | P0 |
| 9 | Frontend: display confidence scores per AI-generated answer | Engineering | P1 |
| 10 | Frontend: answer history and version tracking (compare revisions) | Engineering | P1 |

### Definition of Done for Sprint 002

- [ ] All P0 items complete and verified in staging
- [ ] Auth flow working end-to-end (sign up, sign in, JWT on all API calls)
- [ ] CORS locked to specific origins with no wildcard
- [ ] Custom middleware re-enabled and verified in CI
- [ ] Supabase migration applied to production schema
- [ ] All DPAs signed and filed
- [ ] Privacy notice live in product
- [ ] CI passing with full test suite
- [ ] RAG pipeline returning semantically relevant chunks in answers
- [ ] Confidence scores visible in frontend

### Sprint 002 Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| DPA negotiation takes longer than sprint | High | Start DPA outreach immediately; track separately from engineering sprint |
| RAG pipeline latency too high for UX | Medium | Implement async processing with progress indicator |
| Supabase Auth integration breaks existing session model | Medium | Implement behind feature flag; keep anonymous sessions as fallback |

---

## Sprint 002 — Mid-Sprint Delivery (2026-03-08)

**Status:** Shipped
**Delivered by:** Engineering (single session, 2026-03-08)

These features were completed and merged during Sprint 002 ahead of the planned sprint items. They represent significant product improvements and are now live on `main`.

### Features Shipped

| Feature | Description | Files Changed |
|---|---|---|
| Draft-first answer generation | Every question now receives a professional draft answer using SOC 2/ISO 27001 domain knowledge when vendor docs don't cover the topic. Hedged answers tell vendors what to verify. Context budget raised from 8KB → 96k chars total (40k per doc, dynamic allocation). max_tokens raised 1024 → 2048. | `backend/engine.py` |
| Multi-doc .docx upload | Vendors can now upload Word documents alongside PDFs. Unsupported file types are returned in a `skipped` list (improved UX vs silent drop). | `backend/ingest.py`, `backend/main.py`, `backend/requirements.txt` |
| Sample test questionnaire | 30-question security questionnaire across 8 categories, color-coded. Ready for demos and QA testing. | `docs/sample_questionnaire.xlsx` |

### Impact on Backlog

- "Doc truncation at 8KB" known gap is now significantly mitigated. Context budget is 40k chars per doc / 96k total. Full RAG still planned for Phase 2 but urgency reduced.
- Two new P1 backlog items added: password-protected .docx handling, and .docx text-box / complex-table extraction gaps (python-docx limitation).

### Upload UI Changes

- Drop zone now accepts PDF + .docx
- Multi-select keyboard tip added to upload screen
- Section heading updated
