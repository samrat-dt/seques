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
| SEC-009 | MEDIUM | No file size limit on `.docx` uploads — zip bomb / memory exhaustion DoS | Fixed 2026-03-08 | backend |
| SEC-010 | MEDIUM | 96k char LLM context budget with no auth/rate limiting — denial-of-wallet amplification | Open (blocked on SEC-002/003/004) | backend |
| SEC-011 | LOW | Upload route validates file type by extension only — MIME type not checked | Fixed 2026-03-08 | backend |
| SEC-012 | HIGH | SSE stream endpoint leaks any session's answers to any unauthenticated caller | Open | backend |
| SEC-013 | HIGH | ThreadPoolExecutor exhaustion via repeated unauthenticated `/process` calls | Open | backend |
| SEC-014 | MEDIUM | Fire-and-forget `database.save_answer()` failures are silent — data loss, no audit | Open | backend |
| SEC-015 | MEDIUM | `ANSWER_CONCURRENCY` env var unbounded — operator misconfiguration can starve the process | Open | infra |
| SEC-016 | LOW | `lru_cache` on LLM clients pins stale API keys if env vars rotate without restart | Accepted (low risk, server-env keys only) | backend |

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

---

## Review log — 2026-03-08 (docx / engine.py changes)

### ingest.py — python-docx XXE risk
- **Reviewed**: python-docx uses lxml internally but does not configure it to resolve external entities or load external DTDs. The .docx container is a ZIP of OOXML; no XML external entity expansion occurs during `Document(filepath)`. **Accepted — no new issue.**

### ingest.py — path traversal in filepath
- **Reviewed**: `filepath` passed to `Document()` is produced by `tempfile.NamedTemporaryFile()` — OS-generated, not user-controlled. **Accepted — no path traversal risk.**

### main.py — skipped filenames in response
- **Reviewed**: The `skipped` list returns filenames that the caller itself submitted. No server-side information is disclosed beyond what the caller already knows. **Accepted — no issue.**

### main.py — suffix from os.path.splitext used in NamedTemporaryFile
- **Reviewed**: `suffix` only affects the temporary filename chosen by the OS; it is not used in any path traversal context. `os.path.splitext` returns only the extension component (e.g. `.docx`), which cannot contain path separators. **Accepted — no issue.**

### Detail: SEC-009 No file size limit on .docx uploads
- **Risk**: A malicious actor uploads a zip-bomb `.docx` (high compression ratio) or a document with millions of paragraphs, causing the process to exhaust memory or CPU before the 96k char budget truncates the extracted text. `python-docx` must fully decompress and parse the ZIP before any truncation applies.
- **Root cause**: `upload_docs()` calls `await file.read()` with no size cap, then writes the full content to a temp file and passes it directly to `Document()`.
- **Fix approach**: Add a per-file size check before writing to the temp file (e.g. reject files > 50 MB). Optionally enforce a per-paragraph iteration limit in `extract_docx_text()` as a secondary guard.
- **Phase**: Fix before any public / multi-tenant exposure.
- **Resolution (2026-03-08)**: Added `MAX_DOC_BYTES = 50 MB` check in `upload_docs()` before writing to temp file. Returns HTTP 413 with clear message.

### Detail: SEC-010 96k char LLM context budget amplifies denial-of-wallet
- **Risk**: The context budget in `engine.py` was raised from 8k to 96k characters per request. With no authentication (SEC-002) and no functioning rate limiter (SEC-003/004), an unauthenticated caller can upload large documents and trigger `/process` repeatedly, generating LLM requests with up to 96k chars of context per question. For a questionnaire with 100 questions, a single session can send ~9.6M chars of context to the LLM provider. This is 12x the previous blast radius for the same abuse pattern.
- **Root cause**: Context budget increase without corresponding controls on session creation or processing frequency.
- **Fix approach**: This issue is best resolved by closing SEC-002 (auth) and SEC-003/004 (rate limiting). As an interim measure, add a cap on total document chars ingested per session (e.g., reject uploads that would exceed 200k raw chars across all docs).
- **Phase**: Interim cap before Phase 2 auth; full fix in Phase 2.

### Detail: SEC-011 Extension-only file type validation
- **Risk**: An attacker can rename any file (e.g. a crafted binary or archive) to `.docx` and upload it. `python-docx` will raise an exception (`BadZipFile`) if the file is not a valid ZIP, which is caught by the `try/finally` in `upload_docs()` and results in a 500-level error. This is a robustness issue: it leaks a stack trace in debug mode and could be used to probe parser behavior. It is not currently exploitable for RCE given `python-docx`'s sandboxed parsing, but MIME validation is a defense-in-depth requirement for any file upload endpoint.
- **Root cause**: `SUPPORTED_DOC_TYPES` checks `os.path.splitext(file.filename)[1].lower()` only; `file.content_type` is not validated.
- **Fix approach**: Check `file.content_type` against an allowlist (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`) in addition to the extension check. Also ensure exceptions from parsers return a structured 400 error rather than propagating as 500.
- **Phase**: Fix in Phase 2 pre-prod hardening.
- **Resolution (2026-03-08)**: Added `SUPPORTED_MIME_TYPES` allowlist per extension. `upload_docs()` now checks `file.content_type` against the allowlist and adds non-matching files to `skipped`. `ingest_docx()` exceptions are now caught and returned as HTTP 400 (not 500).

---

## Review log — 2026-03-09 (feat/backend-improvements: SSE endpoint, ThreadPoolExecutor, lru_cache clients, fire-and-forget DB saves)

### Detail: SEC-012 SSE stream endpoint leaks session answers to any unauthenticated caller
- **Severity**: HIGH
- **Endpoint**: `GET /api/sessions/{session_id}/stream`
- **Risk**: The SSE endpoint streams every AI-generated answer (including full `draft_answer` text, `evidence_sources`, `ai_certainty`, `coverage_reason`) for any `session_id` supplied by the caller. There is no authentication (SEC-002 is open) and no ownership check — the caller does not need to be the session creator. Because `session_id` values are UUIDs (v4), direct enumeration is impractical, but:
  1. A UUID in a URL is not a secret. It is logged by proxies, appears in browser history, and is trivially captured from a shared link, a screenshot, or a network intercept.
  2. The CORS wildcard (SEC-001) means any page in any browser can call this endpoint cross-origin.
  3. The SSE connection keeps a long-lived socket open, leaking answers in real time as they are generated. This is a more severe disclosure channel than the polling `/status` + `/answers` pair, because the caller does not need to time polls — the server pushes data.
- **Data exposed**: draft security questionnaire answers, vendor compliance evidence excerpts cited as `evidence_sources`, LLM certainty scores, internal coverage reasoning. In a multi-tenant context this constitutes unauthorised disclosure of another tenant's confidential vendor security posture data.
- **Root cause**: `stream_answers()` calls `get_session(session_id)` (which accepts any UUID) and immediately begins emitting `session.answers` without checking that the requesting client owns or is authorised to read that session. No `Authorization` header is required. No session token / secret is verified.
- **Fix approach**:
  1. Short-term (before any shared/cloud deployment): Add a session-scoped read token (a random secret generated at session creation, returned only to the creator, required as a query parameter or `Authorization: Bearer` header on all read endpoints including `/stream`, `/answers`, `/status`, `/export/*`).
  2. Phase 2: Replace with Supabase JWT auth (closes SEC-002). Enforce Row-Level Security so a user can only read their own sessions.
  3. Independently: Restrict CORS to known frontend origin(s) (closes SEC-001) to remove the cross-origin amplification vector.
- **Phase**: Fix before any production or shared-environment deployment. Blocked on SEC-002; interim token approach is viable for Phase 1 multi-user scenarios.

### Detail: SEC-013 ThreadPoolExecutor thread pool exhaustion via unauthenticated `/process` calls
- **Severity**: HIGH
- **Risk**: `run_answer_engine()` is invoked as a FastAPI `BackgroundTask` whenever `POST /api/sessions/{session_id}/process` is called. Inside it creates a `ThreadPoolExecutor(max_workers=ANSWER_CONCURRENCY)` (default 10). The endpoint has no authentication (SEC-002), no functioning rate limiter (SEC-003/004), and no guard preventing a session from being re-processed multiple times. An attacker can:
  1. Create N sessions (each a cheap, unauthenticated POST).
  2. Upload minimal docs and a questionnaire to each.
  3. Fire `/process` against all N sessions simultaneously (or rapidly in sequence).
  4. Each call spawns up to `ANSWER_CONCURRENCY` new OS threads. With N=50 sessions and concurrency=10, the attacker drives 500 concurrent threads in the FastAPI process. Python threads are OS threads; 500 threads will exhaust available memory and scheduler time on a typical single-core container, causing degraded or failed responses for legitimate users (DoS).
- **Compounding factor**: There is no check at the process endpoint that `session.processing` is already `True` before setting it again and adding another background task. A single attacker session can be submitted to `/process` multiple times, each call spawning a fresh `ThreadPoolExecutor`. This is a single-session amplification vector that does not require session enumeration.
- **Root cause**: No idempotency guard on `/process` (the `session.processing` flag is set but not checked before accepting the new task), combined with absence of authentication and rate limiting.
- **Fix approach**:
  1. Immediate: Add an idempotency guard — if `session.processing` is already `True`, return HTTP 409 Conflict instead of launching another background task.
  2. Short-term: Use a single process-wide `ThreadPoolExecutor` (module-level singleton) rather than creating one per session. This hard-caps total thread count regardless of concurrent sessions.
  3. Phase 2: Close SEC-002 (auth) and SEC-003/004 (rate limiting) to prevent session creation floods.
- **Phase**: Idempotency guard is a one-line fix — implement immediately. Module-level executor is a low-risk refactor for Phase 1. Auth/rate-limit for Phase 2.

### Detail: SEC-014 Fire-and-forget `database.save_answer()` failures are silent — risk of data loss and audit gap
- **Severity**: MEDIUM
- **Location**: `run_answer_engine()` in `main.py`, line `executor.submit(database.save_answer, session_id, answer)` — the returned `Future` is never stored, awaited, or checked.
- **Risk**:
  1. **Data loss**: If `database.save_answer()` raises (Supabase network timeout, auth error, schema mismatch), the exception is swallowed silently. The in-memory `session.answers` dict holds the correct answer, but the Supabase row is never written. On a server restart the session will be restored from Supabase via `_restore_session()`, and any answer whose save failed will be missing — the user loses completed answers with no warning.
  2. **Audit gap**: Failed DB saves are not recorded in the audit log. SOC 2 CC7.2 / GDPR Art 30 require that data write failures be detectable. A silent failure breaks the audit chain.
  3. **Executor queue saturation**: The fire-and-forget submit reuses the same `ThreadPoolExecutor` that is running LLM generation. Under high question counts, the DB save futures pile up in the executor queue and compete with pending LLM futures, potentially delaying answer generation and masking performance problems.
- **Root cause**: The return value of `executor.submit(database.save_answer, ...)` is discarded. There is no callback, no error handler, and no fallback retry.
- **Fix approach**:
  1. Collect the returned `Future` objects and check them after the `as_completed` loop (or use `add_done_callback` to log failures without blocking).
  2. On DB save failure, log a structured error event and emit an audit entry at `WARNING` level so the failure is surfaced in Supabase audit and observability tooling.
  3. Consider separating DB persistence into a dedicated background queue (e.g. a second executor or an `asyncio.Queue`) so it does not consume threads from the LLM concurrency pool.
- **Phase**: Fix before any production deployment. Logging callback is a low-risk change implementable in Phase 1.

### Detail: SEC-015 `ANSWER_CONCURRENCY` env var unbounded — operator misconfiguration can starve the process
- **Severity**: MEDIUM
- **Location**: `main.py` line `ANSWER_CONCURRENCY = int(os.getenv("ANSWER_CONCURRENCY", "10"))`
- **Risk**: The value is read directly from the environment with no upper bound check. If an operator (or a compromised deployment pipeline) sets `ANSWER_CONCURRENCY=500`, each invocation of `run_answer_engine()` spawns a 500-thread pool. On a standard container (1–2 vCPU, 512 MB RAM) this will:
  1. Exhaust thread stack memory (default 8 MB per thread on Linux → 4 GB for 500 threads), causing OOM kills.
  2. Trigger the LLM provider's concurrent-request limits, causing cascading 429 errors that the retry loop (up to 3 attempts, exponential back-off to 4 s) will amplify into multi-minute hangs per thread.
  3. Fully starve the FastAPI event loop of CPU time during the thread creation burst, making the service unresponsive to health checks.
- **Compounding factor**: Because `ANSWER_CONCURRENCY` controls a per-session executor (see SEC-013), an inflated value multiplied across concurrent sessions compounds the blast radius.
- **Root cause**: No input validation or clamping is applied to the env var at startup.
- **Fix approach**: Clamp the value at startup to a safe maximum (e.g. `min(int(os.getenv("ANSWER_CONCURRENCY", "10")), 20)`) and log a warning if the configured value exceeds the cap. Document the recommended range (3–10) in the runbook.
- **Phase**: One-line fix — implement immediately before any deployment where operators control env vars.

### Detail: SEC-016 `lru_cache` on LLM clients pins stale API keys if env vars rotate without restart
- **Severity**: LOW
- **Location**: `llm.py` — `_groq_client()` and `_anthropic_client()` decorated with `@lru_cache(maxsize=1)`
- **Risk**: The cached key risk is assessed as **low** for the following reasons: API keys are sourced exclusively from environment variables set at server start-up (`os.getenv("GROQ_API_KEY")`, `os.getenv("ANTHROPIC_API_KEY")`). They are not user-supplied, not derived from request parameters, and not stored in a mutable location the caller can influence. The `lru_cache` therefore does not introduce a cross-request key contamination vector.
- **Residual concern**: If an API key is rotated (e.g. revoked and reissued after a suspected leak), the cached client will continue using the old key until the process restarts. This means a revoked key remains in use for the life of the current process, which could be hours in a long-running deployment. There is no mechanism to invalidate the cache without a restart.
- **Fix approach**: If key rotation without downtime becomes a requirement, replace `lru_cache` with a manual singleton that re-reads the env var and re-instantiates the client when the key changes. For Phase 1 this is not a blocker.
- **Accepted**: Yes — for Phase 1 (server-env keys only, no user-supplied keys). Revisit in Phase 2 if key rotation SLAs are introduced.
