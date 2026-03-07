# Architecture Decision Log
> Append-only. Never delete. Format: ## [DATE] [DECISION TITLE]

---

## 2026-03-08 — Multi-provider LLM abstraction

**Decision**: Create `backend/llm.py` as a thin wrapper supporting Anthropic, Groq, Google via a single `chat()` function. Provider selected by `LLM_PROVIDER` env var, overridable per-session.

**Context**: User wanted to test with free providers (Groq, Google) before spending on Anthropic credits.

**Trade-offs**:
- ✅ No vendor lock-in, free testing
- ✅ Single switch to change provider
- ❌ Each provider has slightly different JSON output quality (Anthropic best for structured JSON)

**Outcome**: Groq set as default. Anthropic available when needed for quality.

---

## 2026-03-08 — In-memory session store (Phase 1)

**Decision**: Store all session data in a Python dict. No database in Phase 1.

**Context**: MVP speed. Supabase integration was Phase 2.

**Trade-offs**:
- ✅ Zero infra setup, instant to code
- ❌ All data lost on server restart
- ❌ Can't scale horizontally

**Outcome**: Acceptable for demo/beta. Supabase schema designed and ready. Session restore from Supabase implemented (`_restore_session()` in main.py).

---

## 2026-03-08 — Append-only audit log + Supabase dual-write

**Decision**: All audit events write to both `audit.log` (local file) and Supabase `audit_events` table.

**Context**: SOC 2 CC7.2 requirement. Local file is SIEM-ready. Supabase enables queryable audit trail.

**Trade-offs**:
- ✅ Audit survives Supabase outages (file backup)
- ✅ Queryable via `GET /api/audit/supabase`
- ❌ Two places to check (acceptable trade-off)

---

## 2026-03-08 — Mixpanel for product analytics

**Decision**: Mixpanel over PostHog or custom analytics. Events are PII-free (session ID + counts only, no document content).

**Context**: User requested. Mixpanel free tier is generous. GDPR-friendly by design.

**Trade-offs**:
- ✅ No PII exposure
- ✅ Rich funnel and cohort analysis
- ❌ Another vendor dependency
- ❌ Requires DPA before production

---

## 2026-03-08 — Doc truncation at 8KB per document

**Decision**: Truncate each compliance doc to 8,000 chars before sending to LLM.

**Context**: Prevents runaway token costs. Average SOC 2 report is 50-100KB.

**Trade-offs**:
- ✅ Cost control
- ❌ Detail loss on large docs — questions about specific controls may miss evidence

**Outcome**: Phase 2 mitigation: RAG with vector embeddings. Tracked in backlog.

---

## 2026-03-08 — Security headers middleware (Python 3.9 compat)

**Decision**: Custom `SecurityHeadersMiddleware` using Starlette's `BaseHTTPMiddleware`. `MutableHeaders` doesn't support `.pop()` — use `try/del` instead.

**Context**: Bug discovered at runtime. Fixed in same session.

**Lesson**: Test middleware on target Python version before shipping.
