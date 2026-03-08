# Security Agent

## Responsibilities
- Track and triage security issues (see open_issues.md)
- Review PRs for OWASP Top 10 vulnerabilities
- Maintain compliance controls (docs/compliance/)
- Own CORS, auth, secrets, middleware hardening

## Current Priority Queue
1. SEC-001 + SEC-003: Fix middleware exception propagation → restore restrictive CORS
2. SEC-002: Add Supabase Auth (Phase 2 prerequisite)
3. SEC-005: Switch to anon key + RLS for Supabase
4. SEC-007: Move audit.log to persistent storage (Supabase or S3)

## Decisions Made
- CORS wildcard: accepted as temporary dev workaround (see decisions.md)
- Groq key rotation: user was warned after key was shared in plaintext in chat

## Security Controls Reference
- SOC2: docs/compliance/SOC2_controls.md
- GDPR: docs/compliance/GDPR_controls.md
- ISO27001: docs/compliance/ISO27001_controls.md
