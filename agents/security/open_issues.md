# Security Open Issues

| ID | Severity | Title | Status | Owner |
|---|---|---|---|---|
| SEC-001 | HIGH | CORS wildcard (`allow_origins=["*"]`) | Open | security |
| SEC-002 | HIGH | No authentication — all endpoints public | Open | backend |
| SEC-003 | MEDIUM | Custom middleware disabled (SecurityHeaders, RateLimit) | Open | backend |
| SEC-004 | MEDIUM | In-memory rate limiter resets on restart | Open | backend |
| SEC-005 | MEDIUM | Service role Supabase key used from backend (should be anon+RLS) | Open | infra |
| SEC-006 | LOW | No HTTPS enforced in dev | Accepted (dev only) | security |
| SEC-007 | LOW | `audit.log` stored on ephemeral filesystem | Open | infra |
| SEC-008 | LOW | API keys stored in `.env` file (not a secrets manager) | Open | infra |

### Detail: SEC-001 CORS wildcard
- **Risk**: Any origin can make credentialed requests to the API
- **Root cause**: Middleware exception propagation broke CORS headers when origins were restricted — wildcard was a workaround
- **Fix approach**: Wrap `call_next()` in try/except in SecurityHeadersMiddleware and RateLimitMiddleware so exceptions return a 500 JSON response instead of propagating past CORSMiddleware. Then restore `allow_origins=["http://localhost:5173","http://localhost:5174"]`.
- **Phase**: Fix in Phase 2 pre-prod hardening

### Detail: SEC-002 No auth
- **Risk**: Anyone with the URL can create sessions, upload docs, and read audit logs
- **Fix approach**: Add Supabase Auth (JWT) — POST /api/sessions requires `Authorization: Bearer <token>`, user_id stored on Session
- **Phase**: Phase 2

### Detail: SEC-003 Custom middleware disabled
- **Fix**: See SEC-001 fix approach — same root cause
