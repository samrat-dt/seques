# Security Decisions

| Date | Decision | Rationale | Revisit |
|---|---|---|---|
| 2026-03-08 | CORS wildcard for dev | Middleware exception propagation broke restrictive CORS | Phase 2 pre-prod |
| 2026-03-08 | Custom middleware disabled | Same root cause as CORS; workaround | Phase 2 |
| 2026-03-08 | No auth in Phase 1 | Speed to working product; no multi-tenancy needed yet | Phase 2 |
| 2026-03-08 | Supabase service key from backend | Simplest integration; RLS not yet configured | Phase 2 |
| 2026-03-08 | `.env` for secrets | Local dev only; prod needs secrets manager | Before prod deploy |
