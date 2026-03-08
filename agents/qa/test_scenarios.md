# QA Test Scenarios — Phase 1
> Last updated: 2026-03-09
> Branch: feat/backend-improvements

## Smoke Tests (run after every deploy)

| # | Scenario | Steps | Expected |
|---|---|---|---|
| S1 | Health check | GET /health | `{"status":"ok"}` |
| S2 | Provider list | GET /api/providers | JSON with `providers` array |
| S3 | Create session (Groq) | POST /api/sessions `{"provider":"groq"}` | `{"session_id":"..."}` |
| S4 | Upload PDF | POST /api/sessions/{id}/docs multipart | `{"docs":[...]}` |
| S5 | Upload questionnaire | POST /api/sessions/{id}/questionnaire multipart | questions parsed |
| S6 | Process | POST /api/sessions/{id}/process | `{"status":"processing","total":N}` — returns immediately |
| S7 | Export | GET /api/sessions/{id}/export | downloadable file |
| S8 | Upload .docx compliance doc | POST /api/sessions/{id}/docs multipart with a .docx file | 200 response; file appears in `docs` list, not in `skipped` |
| S9 | Upload unsupported type (.txt) as compliance doc | POST /api/sessions/{id}/docs multipart with a .txt file | 200 response; file appears in `skipped` list, not in `docs` |
| S10 | SSE stream opens | GET /api/sessions/{id}/stream after POST /process | HTTP 200, Content-Type: text/event-stream, connection stays open |

---

## Edge Cases

| # | Scenario | Expected |
|---|---|---|
| E1 | Upload non-PDF/non-DOCX as doc (e.g. .txt) | 200 response; unsupported file returned in `skipped` list (e.g. `{"docs": [], "skipped": ["filename.txt"]}`). No 400 error. |
| E2 | Upload empty questionnaire | graceful error or empty questions |
| E3 | Process with no docs uploaded | LLM answers with hedged framing (e.g. "As a SOC 2…"); `answer_tone: "hedged"` |
| E4 | Process with no questions uploaded | 400 or empty answers |
| E5 | Invalid session ID | 404 |
| E6 | Groq key missing, LLM_PROVIDER=groq | 500 with clear error message |
| E7 | Rapid fire 10 requests | rate limiter kicks in (when re-enabled) |

---

## Provider Scenarios

| Provider | Model | Test |
|---|---|---|
| groq | llama-3.3-70b-versatile | Full flow S1–S10 |
| anthropic | claude-haiku-4-5-20251001 | Full flow S1–S10 (requires key) |
| google | gemini-2.0-flash | Full flow S1–S10 (requires key) |

---

## Draft-First Behavior Scenarios

| # | Scenario | Steps | Expected |
|---|---|---|---|
| D1 | Process with SOC 2 PDF uploaded | Upload a SOC 2 PDF as compliance doc, upload questionnaire, POST /process | NO answer in the response contains the text "cannot answer"; all `draft_answer` fields contain substantive text |
| D2 | Process with no docs uploaded (empty doc list) | Create session, skip doc upload, upload questionnaire, POST /process | All answers have `answer_tone: "hedged"`, `evidence_coverage: "none"`, and `draft_answer` begins with "As a SOC 2" or equivalent professional framing (not a refusal) |
| D3 | Context scaling — 3 docs uploaded | Upload SOC 2 PDF + 2 policy PDFs/docx, upload questionnaire, POST /process | Processing completes without crash or timeout; all questions receive a `draft_answer` |
| D4 | 30-question XLSX questionnaire | Upload `docs/sample_questionnaire.xlsx` as questionnaire, POST /process | Exactly 30 questions parsed; all 30 receive a `draft_answer` |

---

## Parallel Execution Scenarios (feat/backend-improvements)

### P1 — All N answers arrive; none missing

**Target**: `run_answer_engine` in `main.py` — `ThreadPoolExecutor(max_workers=ANSWER_CONCURRENCY)`

**Setup**:
1. Create session, upload a SOC 2 PDF, upload a 10-question XLSX questionnaire.
2. POST /process. Wait for `processing: false` via GET /status.

**Steps**:
- GET /api/sessions/{id}/answers

**Expected**:
- `len(answers) == 10` — every `question.id` has a corresponding key in `answers`.
- No question is silently dropped. `session.processed_count == session.total_questions`.
- Confirm in server logs: `answer_generation_failed` is NOT emitted for any question.

**Failure mode to watch**: a thread-safety race on `session.answers` (dict mutation from multiple threads) dropping an entry silently.

---

### P2 — Order independence; all answers present at DONE

**Target**: SSE stream (`/api/sessions/{id}/stream`) and `as_completed` ordering in `run_answer_engine`.

**Setup**:
1. Create session, upload 2 compliance docs, upload a 15-question questionnaire.
2. POST /process. Open GET /stream.

**Steps**:
- Consume all SSE events until `data: [DONE]`.
- Collect each parsed JSON payload and record `question_id`.

**Expected**:
- SSE events arrive in non-deterministic order (shorter LLM calls finish first).
- After `[DONE]`, the collected set of `question_id` values equals the full set of IDs returned by GET /api/sessions/{id}/answers.
- No duplicate `question_id` across SSE events.
- `len(collected_ids) == total_questions`.

**Note**: `seen` set in `event_generator` (main.py line ~550) deduplicates; verify it prevents re-sending any answer.

---

### P3 — SSE connection drop mid-stream; frontend error handling

**Target**: `Processing.jsx` — `es.onerror` handler.

**Setup**:
1. Start a session with a 20-question questionnaire. POST /process.
2. Open the frontend Processing screen. While answers are streaming, simulate a network drop (e.g. disable NIC, kill backend process mid-stream, or use browser devtools > Network > offline mode).

**Steps**:
- Observe the Processing screen UI after the network drop.

**Expected**:
- `es.onerror` fires. `es.close()` is called (no runaway EventSource).
- Red error banner appears: "Connection to server lost. Please refresh and try again."
- No unhandled JS exception in console.
- Re-enabling the network and refreshing the page allows the user to poll GET /status and continue.

**Regression check**: confirm that after `onerror`, the component cleanup (`return () => es.close()`) does not fire a second `close()` on an already-closed EventSource (benign but noisy).

---

### P4 — ANSWER_CONCURRENCY=1 fallback; sequential mode still works

**Target**: `ANSWER_CONCURRENCY` env var → `ThreadPoolExecutor(max_workers=1)` in `run_answer_engine`.

**Setup**:
1. Set `ANSWER_CONCURRENCY=1` in `backend/.env`.
2. Restart the backend server.
3. Create session, upload docs, upload a 5-question questionnaire.
4. POST /process.

**Steps**:
- Wait for `processing: false` via GET /status or `[DONE]` via SSE.
- GET /api/sessions/{id}/answers.

**Expected**:
- All 5 answers are generated and present.
- Processing time is longer than with ANSWER_CONCURRENCY=10 (acceptable — sequential is the safe fallback).
- No deadlock or hang: with `max_workers=1`, the `executor.submit(database.save_answer, ...)` inside the loop runs in the same single-thread pool. Verify this does not starve the main question-processing loop.
- `session.processed_count == 5` at completion.

**Edge case**: ensure `ANSWER_CONCURRENCY=0` is handled gracefully (ThreadPoolExecutor raises ValueError for max_workers < 1 — backend should fail loudly at startup, not silently at runtime).

---

### P5 — Rate limit hit during parallel burst; 429 retry triggers and eventually succeeds

**Target**: `chat()` in `llm.py` — exponential backoff loop (attempts 0–2, waits 1 s then 2 s).

**Setup** (mocked or live):
- Option A (mock): Patch `_do_chat` to raise a 429 exception on the first two attempts for question IDs 3 and 7, then succeed on attempt 3.
- Option B (live): Set ANSWER_CONCURRENCY=10 with a Groq free-tier key on a 30-question questionnaire to trigger organic rate limiting.

**Steps**:
1. POST /process. Monitor server logs for `rate_limit_backoff` events.
2. Wait for processing to complete.
3. GET /api/sessions/{id}/answers.

**Expected**:
- `rate_limit_backoff` log entries appear with `attempt: 0` and `attempt: 1` for affected questions.
- All answers are eventually generated — no question is left with a placeholder error answer due to exhausted retries, unless the provider returns 429 three consecutive times.
- If all 3 attempts fail (max retries exceeded), the question receives the fallback error `Answer` object with `needs_review: true` and `evidence_coverage: none` — NOT an unhandled exception that crashes the thread.
- `session.processed_count` still equals `session.total_questions` even for questions that hit max retries.

**Verify**: The backoff uses `time.sleep(2 ** attempt)` — sleep 1 s on attempt 0, 2 s on attempt 1. Confirm log timestamps reflect this delay.

---

### P6 — max_tokens per answer format; yes_no answers use 512 tokens with no truncation

**Target**: `_max_tokens_for_format()` in `engine.py` and `chat()` call in `answer_question()`.

**Token budget by format** (as implemented):
| Format | max_tokens |
|---|---|
| `yes_no` | 512 |
| `yes_no_evidence` | 900 |
| `freeform` | 2048 |

**Setup**:
1. Create a questionnaire with at least one question of each format type.
   - yes_no example: "Do you have a formal information security policy? (Yes/No)"
   - yes_no_evidence example: "Do you encrypt data at rest? If yes, describe the method."
   - freeform example: "Describe your incident response process in detail."
2. Upload a SOC 2 PDF and POST /process.

**Steps**:
- GET /api/sessions/{id}/answers.
- Inspect each answer's `draft_answer` field.

**Expected**:
- `yes_no` answers: `draft_answer` is complete — starts with "Yes" or "No", followed by a one-sentence explanation. No mid-sentence truncation at 512 tokens.
- `yes_no_evidence` answers: includes both the yes/no verdict and a description. Complete within 900 tokens.
- `freeform` answers: detailed multi-sentence response; no truncation visible (answer does not end abruptly mid-word or mid-sentence).
- No `draft_answer` field is an empty string.

**Implementation note**: `_max_tokens_for_format` is called per-question inside `answer_question()`. The `doc_context` is built once (P7) and passed in — the token budget applies only to the LLM output, not the context. This is correct behavior; confirm it is not being confused with prompt token limits.

---

### P7 — doc_context built once; same context used for all questions in session

**Target**: `build_doc_context()` called once in `run_answer_engine()` (main.py line ~463), then passed as `doc_context=` kwarg to every `answer_question()` call.

**Verification approach** (instrumentation or logging):

**Steps**:
1. Add a temporary `logger.debug("build_doc_context_called")` inside `build_doc_context()` in engine.py.
2. Run a session with 10 questions. POST /process.
3. Check server logs.

**Expected**:
- `build_doc_context_called` appears exactly **once** per session, regardless of question count.
- Every `answer_question()` invocation receives the same non-None `doc_context` string (the early-exit guard `if doc_context is None: doc_context = build_doc_context(docs)` should NOT be triggered for any parallel call).
- Remove the debug log after verification.

**Why this matters**: building doc_context is O(N_docs × doc_char_limit) work. If it were called per-question with ANSWER_CONCURRENCY=10 and 10 docs, it would execute 100 times instead of once. The current implementation is correct; this scenario guards against future regressions that move the call inside `process_one()`.

**Secondary check**: verify that `build_doc_context` with 0 docs returns an empty string `""` (not None, not an exception), so `answer_question()` can still produce hedged answers without crashing.

---

## Regression Checklist (after any backend change)
- [ ] ingest.py: upload a multi-page PDF — no `ValueError: document closed`
- [ ] CORS: frontend can reach all API endpoints
- [ ] Audit log: every action emitted to audit.log
- [ ] Analytics: Mixpanel events visible in dashboard
- [ ] engine.py: no answer has `draft_answer` containing "cannot answer", "not available", or "evidence not found"
- [ ] engine.py: hedged answers start with "As a SOC 2" or equivalent professional framing (no refusal language)
- [ ] ingest.py: .docx upload extracts text correctly (paragraphs joined with double newline)
- [ ] main.py: uploading a .txt file returns `{"docs": [], "skipped": ["filename.txt"]}`
- [ ] main.py: POST /process returns immediately with `{"status":"processing","total":N}` — not blocking
- [ ] main.py: GET /stream closes with `data: [DONE]` after all answers complete
- [ ] main.py: `session.processed_count` always equals `session.total_questions` at end of `run_answer_engine` (even on per-question errors)
- [ ] llm.py: `_groq_client()` and `_anthropic_client()` are only instantiated once per process (lru_cache — confirm by checking no redundant SDK init logs)
- [ ] llm.py: 429 from any provider triggers backoff log entry and retry, not an immediate exception bubble
- [ ] engine.py: `_max_tokens_for_format` returns 512 for yes_no, 900 for yes_no_evidence, 2048 for freeform
- [ ] Processing.jsx: EventSource is closed on component unmount (no memory leak on navigation away mid-stream)
- [ ] Processing.jsx: onerror shows user-facing error message, not a blank screen
