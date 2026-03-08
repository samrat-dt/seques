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
