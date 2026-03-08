# Seques Product Backlog

**Last updated:** 2026-03-08
**Owner:** Project Manager Agent

---

## P0 — Must Have Before Production

- [ ] User authentication (Supabase Auth)
- [ ] Fix CORS wildcard → specific origins
- [ ] Re-enable SecurityHeaders + RateLimit middleware
- [ ] Run Supabase migration SQL
- [ ] Sign DPAs (Supabase, Groq, Anthropic, Google, Mixpanel)
- [ ] Publish privacy notice
- [ ] Full test suite with CI passing

---

## P1 — Phase 2 Core Features

- [ ] RAG pipeline: chunk, embed, semantic search
- [ ] Answer confidence scores
- [ ] Answer history / version tracking
- [ ] Multi-tenant: user_id on sessions, RLS in Supabase
- [ ] Export to Word/PDF

---

## P2 — Phase 2 Nice to Have

- [ ] Questionnaire template library (standard CAIQ, SIG, VSA)
- [ ] Auto-detect questionnaire format
- [ ] Collaborative review (share session link)
- [ ] Slack notifications on processing complete

---

## P3 — Future

- [ ] Vendor portal (buyers send questionnaire directly to Seques)
- [ ] Continuous monitoring (re-score on new SOC 2 report)
- [ ] API for programmatic integration
- [ ] SOC 2 Type II audit readiness score
