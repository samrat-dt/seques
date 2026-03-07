# Security Agent
> Owns OWASP, secrets management, headers, rate limiting, auth.

## Responsibilities
- Review all new routes for injection, auth bypass, data leakage
- Keep `backend/security.py` current
- Manage secrets — nothing in code, everything in `.env`
- Track CVEs in dependencies (run `pip-audit` weekly)
- Auth implementation (Phase 2: Supabase JWT)

## Current Security State
| Control | Status |
|---|---|
| Security headers | ✅ SecurityHeadersMiddleware |
| Rate limiting | ✅ 30 req/min (in-memory — upgrade to Redis in Phase 2) |
| CORS | ⚠️ Wildcard (`*`) — MUST restrict before production |
| Auth | ❌ None — P0 for Phase 2 |
| Secrets in env | ✅ `.env` gitignored |
| TLS | ✅ Enforced via HSTS in prod mode |
| Prompt injection | ✅ Mitigated — output validated as JSON |
| Dependency scanning | ❌ Not set up — add Dependabot |

## Pre-Production Checklist
- [ ] Replace `allow_origins=["*"]` with explicit origin list
- [ ] Add Dependabot to `.github/dependabot.yml`
- [ ] Run `pip-audit` and fix any HIGH/CRITICAL CVEs
- [ ] Implement JWT auth middleware
- [ ] Add `ENVIRONMENT=production` check before deploying

## Secrets Rotation Schedule
| Secret | Last Rotated | Next Due |
|---|---|---|
| GROQ_API_KEY | 2026-03-08 | 2026-06-08 |
| MIXPANEL_TOKEN | 2026-03-08 | Never (token) |
| SUPABASE_SERVICE_KEY | 2026-03-08 | 2026-06-08 |
