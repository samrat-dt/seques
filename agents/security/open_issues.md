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

---

## Phase 1 Checkpoint Security Sign-Off — 2026-03-09

**Branch reviewed**: `feat/backend-improvements`
**Reviewer**: security agent
**Verdict**: CONDITIONAL GO — Phase 1 internal/dev use only. NOT cleared for production or any shared multi-tenant environment. Specific blockers for production listed below.

---

### 1. Verification of SEC-013, SEC-014, SEC-015 Fixes

#### SEC-013 — ThreadPoolExecutor exhaustion via repeated unauthenticated `/process` calls
**Status: FIXED (verified)**

- `main.py` line 457–458: `if session.processing: raise HTTPException(status_code=409, detail="Session is already being processed. Wait for it to complete.")` — the idempotency guard is in place. A session whose `processing` flag is `True` will now reject a second `/process` call with HTTP 409 before spawning any new executor.
- `main.py` lines 115–119: `ANSWER_CONCURRENCY = min(_CONCURRENCY_RAW, 20)` — thread pool size is hard-capped at 20 regardless of env var.
- `main.py` line 126: `_db_save_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="db-save")` — a separate, bounded, module-level executor handles DB saves, eliminating the prior pattern where DB futures competed with LLM futures in the same pool.
- **Residual risk**: The per-session `ThreadPoolExecutor(max_workers=ANSWER_CONCURRENCY)` at line 494 is still created fresh per `run_answer_engine()` invocation rather than being a process-wide singleton. The idempotency guard at line 457 prevents re-entry on a live session, but N concurrent sessions each create their own pool. With the 20-thread cap, maximum concurrency is 20 × (number of concurrent sessions). For Phase 1 (low concurrent session count) this is acceptable; for Phase 2 a global executor singleton is recommended.

#### SEC-014 — Silent fire-and-forget `database.save_answer()` failures
**Status: FIXED (verified)**

- `main.py` lines 503–508: A `_on_save_done` callback is attached to every `_db_save_executor.submit(database.save_answer, ...)` future via `.add_done_callback()`. If the future raises, `fut.exception()` is non-None and a structured `logger.error("db_save_failed", ...)` is emitted with `session_id` and `question_id`.
- DB save futures now run in the dedicated `_db_save_executor` (4 threads) defined at module level, not in the LLM answer pool.
- **Residual gap**: The callback logs to the observability logger but does not emit an `audit.emit()` entry. A SOC 2 CC7.2 auditor may expect that every failed persistence attempt appears in the audit trail, not only in the structured log. This gap is low priority for Phase 1 but should be closed before a SOC 2 audit.
- **Residual gap**: There is no retry on DB save failure. In-memory state is preserved, but if the process restarts before a successful retry the answer is lost. Acceptable for Phase 1 in-memory sessions; Phase 2 Supabase persistence must add a retry or write-ahead log.

#### SEC-015 — `ANSWER_CONCURRENCY` env var unbounded
**Status: FIXED (verified)**

- `main.py` lines 115–119: Value is read, clamped to 20, and a `warnings.warn()` is emitted if the raw value exceeded the cap. Code path:
  ```
  _CONCURRENCY_RAW = int(os.getenv("ANSWER_CONCURRENCY", "1"))
  ANSWER_CONCURRENCY = min(_CONCURRENCY_RAW, 20)
  if _CONCURRENCY_RAW > 20:
      warnings.warn(f"ANSWER_CONCURRENCY={_CONCURRENCY_RAW} exceeds max of 20; clamped to 20.")
  ```
- Note: the default changed from `"10"` (as documented in the original SEC-015 issue) to `"1"`. This is a more conservative default that reduces denial-of-wallet blast radius (SEC-010) and is consistent with the new `QUESTION_DELAY_S` throttle. The original issue description's documented default (`"10"`) is now outdated — no action required, but the runbook should be updated to reflect default of 1.

---

### 2. SEC-012 — SSE Endpoint (Unauthenticated Session Stream)
**Status: OPEN — documented as Phase 2, no immediate code fix required**

- `main.py` lines 568–610: The `GET /api/sessions/{session_id}/stream` endpoint calls `get_session(session_id)` (line 578) and immediately begins streaming `session.answers` as SSE events. No `Authorization` header, no session ownership check, no read token validation is present.
- This is intentional and correctly deferred: no authentication layer exists at all in Phase 1 (SEC-002). Patching `/stream` in isolation while every other endpoint (`/answers`, `/status`, `/export/*`) remains unauthenticated provides no meaningful incremental security.
- The full fix requires SEC-002 (Supabase JWT auth) + SEC-001 (CORS restriction), both Phase 2 items. The interim session-scoped read token approach described in the SEC-012 detail section remains viable if Phase 1 is exposed to multiple users before Phase 2 ships.
- **Production blocker**: This is a hard blocker for any production or shared deployment where multiple distinct users or organisations share the same server instance. It is not a blocker for single-operator/dev use.

---

### 3. New Issues Identified in This Review

#### NEW-001 — Global exception handler leaks internal exception messages to callers
**Severity**: MEDIUM
**Location**: `main.py` lines 82–89

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", extra={"path": request.url.path, "error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )
```

- `str(exc)` is interpolated directly into the HTTP 500 response body returned to the caller. Python exceptions frequently include internal details: file paths, variable values, library version strings, SQL fragments, and third-party API error messages (e.g. Supabase client errors, OpenAI SDK errors).
- An attacker can deliberately trigger exceptions (e.g. malformed JSON body, invalid session ID formats, oversized payloads on un-guarded paths) and read the response body to extract implementation details useful for further attacks.
- **Fix approach**: Return a generic message (`"Internal server error. See server logs for details."`) in the response body. Keep `str(exc)` in the structured logger call only, where it is not visible to external callers.
- **Phase**: Low-effort fix; implement before any non-local deployment.

#### NEW-002 — `QUESTION_DELAY_S` applies globally including to errors, serialising the executor
**Severity**: LOW (operational risk, not a security vulnerability per se)
**Location**: `main.py` lines 532–533

```python
finally:
    session.processed_count += 1
    if QUESTION_DELAY_S > 0:
        time.sleep(QUESTION_DELAY_S)
```

- The `time.sleep(QUESTION_DELAY_S)` call is inside the `finally` block of the per-question `try/except` in `run_answer_engine()`. This means the delay fires even when a question fails immediately (e.g. LLM key missing, network error). With `ANSWER_CONCURRENCY=1` (the new default) and a 1.5-second delay, each failed question adds 1.5 s of unrecoverable wait to the processing pipeline.
- From a security standpoint: an attacker who triggers repeated failures (e.g. by causing the LLM provider to 429 every request) can force the processing pipeline into a slow-walk state, degrading throughput for concurrent legitimate sessions. This is a weak amplification of the DoS vectors in SEC-010 and SEC-013, not an independent blocker.
- **Phase**: Accept for Phase 1. Revisit if the delay causes user-visible issues in practice.

#### NEW-003 — `_exhausted_keys` set is process-lifetime; no persistence or cross-process synchronisation
**Severity**: LOW
**Location**: `llm.py` lines 59–60, 73–79

```python
_exhausted_keys: set[str] = set()
_exhausted_lock = threading.Lock()
```

- Once a Groq API key is added to `_exhausted_keys` via `_mark_exhausted()`, it is never removed for the life of the process. There is no time-based expiry and no persistence across restarts.
- **Consequence 1 — false permanent blacklist**: A transient TPD-like error (e.g. a malformed 429 response that matches the `_is_tpd_error()` heuristic at `llm.py` lines 100–102) will permanently blacklist a healthy key for the process lifetime. The heuristic matches any exception whose `str()` contains `"tokens per day"` or `"per day"` (case-insensitive). This is a substring match, not a structured API field check; a Supabase or other library error whose message happens to include `"per day"` would incorrectly trigger exhaustion.
- **Consequence 2 — restart clears blacklist**: The daily exhaustion state is not persisted. If the process restarts at 11:59 PM, keys correctly exhausted for that UTC day will be retried at restart, burning quota from the new day correctly, but any legitimate mid-day restart clears genuine exhaustion and causes renewed 429s until keys are re-exhausted.
- **Consequence 3 — no cross-worker sync**: In a multi-worker deployment (e.g. Gunicorn with multiple workers), each worker maintains its own `_exhausted_keys`. A key exhausted in worker A continues to be used by worker B.
- **Fix approach**: Use a structured field from the API error object (e.g. `exc.code == "rate_limit_exceeded"` combined with a `"daily"` subtype) rather than substring matching. Add a time-based expiry to `_exhausted_keys` (e.g. reset at midnight UTC). For Phase 1 single-worker dev use, this is low risk.
- **Phase**: Accept for Phase 1 single-worker deployment. Flag for Phase 2 multi-worker hardening.

---

### 4. Issue Table — Updated Status

| ID | Severity | Title | Status | Owner |
|---|---|---|---|---|
| SEC-001 | HIGH | CORS wildcard (`allow_origins=["*"]`) | Open — Phase 2 | security |
| SEC-002 | HIGH | No authentication — all endpoints public | Open — Phase 2 | backend |
| SEC-003 | MEDIUM | Custom middleware disabled (SecurityHeaders, RateLimit) | Open — Phase 2 | backend |
| SEC-004 | MEDIUM | In-memory rate limiter resets on restart | Open — Phase 2 | backend |
| SEC-005 | MEDIUM | Service role Supabase key used from backend (should be anon+RLS) | Open | infra |
| SEC-006 | LOW | No HTTPS enforced in dev | Accepted (dev only) | security |
| SEC-007 | LOW | `audit.log` stored on ephemeral filesystem | Open | infra |
| SEC-008 | LOW | API keys stored in `.env` file (not a secrets manager) | Open | infra |
| SEC-009 | MEDIUM | No file size limit on `.docx` uploads — zip bomb / memory exhaustion DoS | Fixed 2026-03-08 | backend |
| SEC-010 | MEDIUM | 96k char LLM context budget with no auth/rate limiting — denial-of-wallet amplification | Open (blocked on SEC-002/003/004) | backend |
| SEC-011 | LOW | Upload route validates file type by extension only — MIME type not checked | Fixed 2026-03-08 | backend |
| SEC-012 | HIGH | SSE stream endpoint leaks any session's answers to any unauthenticated caller | Open — Phase 2 (deferred, no immediate code fix) | backend |
| SEC-013 | HIGH | ThreadPoolExecutor exhaustion via repeated unauthenticated `/process` calls | Fixed 2026-03-09 | backend |
| SEC-014 | MEDIUM | Fire-and-forget `database.save_answer()` failures are silent — data loss, no audit | Fixed 2026-03-09 (logging callback added; audit trail gap remains LOW) | backend |
| SEC-015 | MEDIUM | `ANSWER_CONCURRENCY` env var unbounded — operator misconfiguration can starve the process | Fixed 2026-03-09 (clamped to 20, warns on excess) | infra |
| SEC-016 | LOW | `lru_cache` on LLM clients pins stale API keys if env vars rotate without restart | Accepted — Phase 1 | backend |
| NEW-001 | MEDIUM | Global exception handler leaks `str(exc)` to HTTP response body — information disclosure | Open | backend |
| NEW-002 | LOW | `QUESTION_DELAY_S` fires on error paths, serialising executor under failure conditions | Accepted — Phase 1 | backend |
| NEW-003 | LOW | `_exhausted_keys` heuristic uses substring match; no time-based expiry; no cross-worker sync | Accepted — Phase 1 single-worker | backend |

---

### 5. Production Go/No-Go Assessment

**PHASE 1 (single-operator, local/dev): GO**
All Phase 1 targetted issues are resolved or formally accepted. The three fixes (SEC-013, SEC-014, SEC-015) are correctly implemented and verified at the code level. No regressions introduced.

**PRODUCTION / MULTI-TENANT: NO-GO**
The following issues are hard blockers for production deployment:

| Blocker | Issue | Reason |
|---|---|---|
| BLOCK-1 | SEC-002 | No authentication — any actor with any session UUID can read, modify, or export any session |
| BLOCK-2 | SEC-012 | SSE endpoint streams all draft answers without ownership verification |
| BLOCK-3 | SEC-001 | CORS wildcard enables cross-origin exploitation of BLOCK-1 and BLOCK-2 from any browser tab |
| BLOCK-4 | NEW-001 | Exception messages leaked in HTTP 500 bodies disclose internal stack and library details |
| BLOCK-5 | SEC-010 | No rate limiting on session creation or `/process` — denial-of-wallet attack is trivially executable |

NEW-001 is the only new blocker introduced since the last review. It is a low-effort fix (change one line in `global_exception_handler`) and should be resolved before any non-localhost deployment regardless of Phase 2 timeline.
