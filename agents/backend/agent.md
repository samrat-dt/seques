# Backend Agent
> Owns everything in `backend/`. Python 3.9, FastAPI, Supabase, multi-provider LLM.

## Responsibilities
- All FastAPI routes (`main.py`)
- LLM provider logic (`llm.py`, `engine.py`, `parser.py`)
- Supabase persistence (`database.py`)
- Audit trail (`audit.py`)
- Analytics events (`analytics.py`)
- Observability (`observability.py`)
- Security middleware (`security.py`)

## Key Constraints
- Python 3.9 — use `from __future__ import annotations` for `X | Y` union types
- All new routes need: tag, summary, docstring, audit.emit(), analytics.track()
- Never log document content — GDPR/SOC2
- All Supabase calls must fail gracefully (wrapped in `_run()`)
- Run server: `cd backend && .venv/bin/uvicorn main:app --reload --port 8000`

## Before Every Change
1. Read the target file
2. Check `agents/shared/decisions.md` for prior context
3. Write decision if architectural

## After Every Change
- Update `agents/backend/memory.md`
- Update `agents/shared/project-state.md` if status changed

---

## Performance Review — 2026-03-09

### Branch: `feat/backend-improvements`
### Files reviewed: `backend/engine.py`, `backend/llm.py`, `backend/main.py`, `frontend/src/screens/Processing.jsx`

---

### 1. `engine.py` — `_max_tokens_for_format()` and `doc_context` param

**Assessment: Correct and well-designed.**

`_max_tokens_for_format()` maps `AnswerFormat` enum values to token budgets:
- `yes_no` → 512 (tight, appropriate — answer is short)
- `yes_no_evidence` → 900 (reasonable expansion for evidence sentences)
- fallthrough (freeform) → 2048 (generous, correct for open-ended answers)

The function is called directly in `answer_question()` as the `max_tokens` argument to `chat()`. This is correct — it avoids over-provisioning tokens for short-answer questions, which reduces cost and latency on all providers.

The `doc_context: str | None = None` parameter addition to `answer_question()` is sound. When `doc_context` is `None`, the function falls back to calling `build_doc_context(docs)` locally, preserving backward compatibility for any direct callers. When provided (the new path from `run_answer_engine`), the pre-built string is reused across all questions in a session, avoiding `len(docs)` redundant re-computations of potentially large string concatenations. No issues here.

**No bugs found in engine.py changes.**

---

### 2. `llm.py` — `lru_cache` client singletons and exponential backoff

**Assessment: Mostly correct; one latent issue with Google provider.**

**`lru_cache` singletons:**

`_groq_client()` and `_anthropic_client()` are decorated with `@lru_cache(maxsize=1)`. The OpenAI-compat (Groq) and Anthropic SDK clients are both documented as thread-safe for concurrent requests, so sharing a single instance across 10 ThreadPoolExecutor threads is correct and safe.

However, there is no `lru_cache` (or equivalent singleton) for the Google provider. The `_do_chat()` branch for Google calls `genai.configure(api_key=...)` and constructs a new `GenerativeModel` on every invocation. With `ANSWER_CONCURRENCY=10` threads all hitting Google simultaneously, `genai.configure()` is called 10 times in rapid succession — this is a global side-effecting call that mutates the `google.generativeai` module's global state. This is a race condition: concurrent threads can overwrite each other's configuration, though in practice the value being written is always the same (the same API key), so the practical risk is low but it is still not thread-safe by design.

**Exponential backoff:**

The retry loop in `chat()` is structurally correct:
- 3 total attempts (indices 0, 1, 2)
- Rate-limit detection checks `type(e).__name__.lower()`, `e.status_code`, and `str(e)` — broad enough to catch vendor-specific exception types
- `wait = 2 ** attempt` yields 1s, 2s sleeps (attempt 0 and 1) — reasonable
- Non-rate-limit exceptions are re-raised immediately on any attempt

One concern: `time.sleep()` is a blocking call. In `run_answer_engine`, each `process_one()` call runs in a ThreadPoolExecutor thread. A thread sleeping for 1–2 seconds due to rate limiting reduces throughput but does not block the event loop (the function runs in a thread, not a coroutine). This is acceptable.

The final `raise RuntimeError("Max retries exceeded due to rate limiting")` after the loop is dead code under the current loop structure — the loop either returns or raises on attempt 2 inside the loop body. The statement is harmless but misleading. If the intent was to guarantee it raises after all retries, the loop's internal `raise` on `attempt == 2` already achieves this. Not a bug, but confusing.

**Issues:**
- Google `genai.configure()` called per-request in a multi-threaded context (low-severity race, same value always written)
- Final `raise RuntimeError(...)` after retry loop is unreachable dead code

---

### 3. `main.py` — ThreadPoolExecutor parallel answer generation

#### 3a. Correctness of ThreadPoolExecutor implementation

**Assessment: Structurally correct, with thread-safety issues on shared mutable state.**

The pattern in `run_answer_engine` follows the standard futures pattern:

```python
with ThreadPoolExecutor(max_workers=ANSWER_CONCURRENCY) as executor:
    futures = {executor.submit(process_one, q): q for q in session.questions}
    for future in as_completed(futures):
        ...
        session.answers[question.id] = answer
        session.processed_count += 1
```

The `with ThreadPoolExecutor` block correctly waits for all submitted futures to complete before exiting (the context manager calls `executor.shutdown(wait=True)`). The outer `try/finally` that sets `session.processing = False` and calls `mark_processing_complete` will always execute after all futures complete or an unhandled exception exits the block — this is correct.

#### 3b. Thread safety concerns

**`session.answers` dict writes — UNSAFE**

`session.answers` is a plain `dict`. In CPython, individual dict key assignments are protected by the GIL, making single-item `d[k] = v` assignments effectively atomic for simple values. However, this is an implementation detail of CPython, not a language guarantee. The code iterates `as_completed(futures)` in the main thread of `run_answer_engine` and writes to `session.answers[question.id] = answer` there — not from multiple worker threads simultaneously. Worker threads only run `process_one()` (LLM calls), and the result collection happens serially in the `as_completed` loop. This means there is no concurrent write to `session.answers` from multiple threads at the same time.

However, the SSE endpoint `stream_answers` reads `session.answers` concurrently from the async event loop while `run_answer_engine` is writing to it from its thread:

```python
for qid, answer in list(session.answers.items()):
```

The `list(session.answers.items())` call creates a snapshot. In CPython, `dict.items()` and the subsequent `list()` call are not atomic together — a concurrent dict resize (triggered by a new key insertion in another thread) can cause a `RuntimeError: dictionary changed size during iteration`. The `list()` wrapping mitigates but does not eliminate this: `dict.items()` returns a view that is iterated to build the list, and a concurrent insertion during that iteration can still trigger the error in CPython 3.x.

This is a real race condition. The probability is low (only occurs during the moment of a new key insertion), but it is not protected by any lock.

**`session.processed_count += 1` — UNSAFE**

`session.processed_count += 1` is a read-modify-write operation. In the current code, this increment happens in the `as_completed` loop body, which runs in a single thread (the thread running `run_answer_engine`). The `as_completed` loop is sequential — only one iteration runs at a time in that thread. So there is no concurrent increment from multiple threads.

However, the `/status` endpoint reads `session.processed_count` from the async event loop while `run_answer_engine` increments it from its worker thread. Integer reads in CPython are GIL-protected and effectively atomic for reading, so this is safe in practice on CPython. On alternative Python implementations without a GIL this would be unsafe.

**Summary of thread-safety issues:**
- `session.answers` dict: concurrent read (SSE) vs write (run_answer_engine thread) — real race risk on dict size change during iteration
- `session.processed_count`: safe on CPython due to GIL; not portable to non-GIL implementations
- No lock or `threading.RLock` anywhere in the session object

#### 3c. Fire-and-forget DB save using `executor.submit` inside the `with` block

**Assessment: UNSAFE — will block executor shutdown.**

The problematic pattern:

```python
with ThreadPoolExecutor(max_workers=ANSWER_CONCURRENCY) as executor:
    futures = {executor.submit(process_one, q): q for q in session.questions}
    for future in as_completed(futures):
        ...
        executor.submit(database.save_answer, session_id, answer)  # <-- fire-and-forget DB save
```

The `with ThreadPoolExecutor(...) as executor` context manager calls `executor.shutdown(wait=True)` on exit. This waits for ALL submitted futures — including the fire-and-forget `database.save_answer` futures — to complete before the `with` block returns.

This means:
1. The DB saves are NOT actually fire-and-forget. They block the `with` block from exiting until all DB writes complete.
2. `session.processing = False` is not set in `finally` until after all DB saves finish.
3. The SSE endpoint's termination condition checks `not session.processing` — so clients wait longer than necessary before receiving `[DONE]`.
4. In the worst case (Supabase slow or unavailable), DB saves can each timeout before the processing flag clears.
5. The `database.save_answer` calls use the same executor that is running LLM tasks. If all 10 worker slots are occupied by pending DB save futures when the `as_completed` loop submits more, it can reduce effective parallelism for LLM calls — though in practice the timing usually means LLM calls finish before DB saves are submitted.

**The correct fix** would be a separate `ThreadPoolExecutor` (or `asyncio.get_event_loop().run_in_executor`) dedicated to DB writes, or to batch-save all answers after the `with` block exits. Using `executor.submit` inside the same executor's `with` block is misleading and not truly non-blocking.

This is a **confirmed bug**. The fire-and-forget intent is not achieved. The behavior is currently: all DB saves complete synchronously before `session.processing` clears.

---

### 4. SSE endpoint — `/api/sessions/{session_id}/stream`

**Assessment: Functional but has several edge cases that are not handled.**

```python
async def event_generator():
    seen: set = set()
    while True:
        for qid, answer in list(session.answers.items()):
            if qid not in seen:
                seen.add(qid)
                yield f"data: {json.dumps(answer.model_dump())}\n\n"
        if not session.processing and len(seen) >= session.total_questions and session.total_questions > 0:
            yield "data: [DONE]\n\n"
            break
        await asyncio.sleep(0.3)
```

**Edge case 1: Client connects before `process` is called (session not yet processing)**

If a client connects to `/stream` before `/process` has been called, `session.processing` is `False` and `session.total_questions` is 0. The termination condition evaluates:

```
not False and len(set()) >= 0 and 0 > 0
```

The last clause `0 > 0` is `False`, so the loop does NOT terminate — it will spin indefinitely at 0.3s intervals consuming server resources. This is an infinite loop for pre-process clients.

**Edge case 2: `session.total_questions` is 0 after processing (empty questionnaire)**

If an empty questionnaire is processed (0 questions), `session.total_questions` remains 0. The condition `session.total_questions > 0` is `False` even after processing completes. The loop again spins forever. The endpoint has no timeout and no escape for this case.

**Edge case 3: Race between `session.processing = False` and final answers**

`session.processing` is set to `False` in the `finally` block of `run_answer_engine`, which runs after the `with ThreadPoolExecutor` block exits. As established in section 3c, the executor waits for DB saves, so `processing = False` is set only after all DB saves complete. By then, all answers are in `session.answers`. The SSE generator checks `list(session.answers.items())` before the termination condition in the same loop iteration, so newly completed answers are emitted before `[DONE]` is sent. This ordering is correct.

However, if the last few answers land in `session.answers` and `session.processing` flips to `False` between two 0.3s sleep intervals, those answers will be caught in the next polling cycle before `[DONE]` is sent. No answers are lost, but there is up to a 0.3s delay before `[DONE]` is emitted after the last answer. Acceptable.

**Edge case 4: Client disconnect not detected**

If the SSE client disconnects (browser tab closed, network drop), the `event_generator` async generator continues running, polling `session.answers` every 0.3s indefinitely until processing completes. FastAPI/Starlette's `StreamingResponse` does not inject a cancellation signal into the generator. For short processing runs this is not a problem, but for sessions that take minutes, orphaned generators accumulate. A `GeneratorExit` or `asyncio.CancelledError` handler is absent.

**Edge case 5: Session not found after initial lookup**

`get_session(session_id)` is called before the generator starts — if the session doesn't exist, it raises a 404 HTTPException correctly. But if the session is somehow evicted from `sessions` dict between the initial check and subsequent polling iterations (e.g., memory pressure causing manual cleanup in a future implementation), subsequent `session.answers` and `session.processing` reads would work because Python holds a reference to the `session` object via local variable capture — the session object itself won't be GC'd as long as the generator holds its reference. This is safe.

**Edge case 6: `answer.model_dump()` may contain enum values**

`answer.model_dump()` on a Pydantic model with `Enum` fields will serialize enums as their `.value` strings by default in Pydantic v2. This should produce valid JSON. No issue observed, but worth confirming the frontend handles all enum string values the SSE payload contains.

**Missing: SSE reconnection / `Last-Event-ID` support**

The endpoint has no `id:` field on events and no `Last-Event-ID` header handling. If the browser's `EventSource` auto-reconnects after a dropped connection, the server starts streaming from the beginning again (`seen` is reset, a new generator instance is created). The client will re-count answers, causing `answered` to exceed `total` in the UI. The frontend does not deduplicate by question ID — it just increments `answered` on every received message — so reconnects produce inflated counts.

---

### 5. Frontend `Processing.jsx` — SSE consumer

**Assessment: Functional. Two minor issues.**

**Issue 1: `onDone` as `useEffect` dependency**

`onDone` is listed in the `useEffect` dependency array. If the parent component defines `onDone` as an inline arrow function (which is the common pattern), `onDone` will have a new reference on every render, causing the `useEffect` to re-run, closing and reopening the `EventSource` on every parent re-render. This is a standard React hook pitfall. The fix is for the parent to wrap `onDone` in `useCallback`, or for `Processing.jsx` to use `useRef` to hold `onDone`. As-written, whether this is a bug depends on how the parent passes `onDone`.

**Issue 2: `total` state initialized to 0, updated only on `[DONE]`**

Before `[DONE]` arrives, `total` is estimated from the answer stream (`setTotal((t) => (t === 0 ? 1 : t))`). This means the progress percentage is meaningless until `[DONE]` fires. The `answerPct` calculation uses:

```js
const answerPct = total > 0 ? (answered / total) * 100 : answered > 0 ? 50 : 0
```

When `total` is 0 and `answered > 0`, it shows 50% indefinitely. This is intentional UX (indeterminate progress) but the comment "will be updated properly on DONE" is misleading because `total` is set from `data.questions.length` only after `getAnswers()` resolves, which happens after the SSE stream closes. During the entire processing run, the progress bar percentage is not accurate. For a questionnaire with 50 questions, users will see 50% for most of the processing time.

**Issue 3: `es.onerror` closes the connection without retry**

The `onerror` handler closes the `EventSource` and sets an error message. `EventSource` natively auto-reconnects on error, but since `es.close()` is called immediately in `onerror`, the auto-reconnect is suppressed. If the connection drops briefly (server restart, transient network blip), the user sees a hard error with no recovery path other than refreshing the page. This is a deliberate tradeoff but reduces resilience.

---

### Summary of Findings

| # | Severity | File | Issue |
|---|----------|------|-------|
| 1 | HIGH | `main.py` | Fire-and-forget DB save (`executor.submit` inside `with` block) is NOT fire-and-forget — it blocks executor shutdown, delaying `session.processing = False` |
| 2 | HIGH | `main.py` | SSE generator infinite loop when client connects before `/process` is called (`total_questions == 0`) |
| 3 | MEDIUM | `main.py` | `session.answers` dict race: concurrent read (`list(session.answers.items())`) from async event loop vs write from worker thread — can raise `RuntimeError` during dict resize |
| 4 | MEDIUM | `main.py` | SSE has no `Last-Event-ID` / reconnection support — client reconnect inflates `answered` count in frontend |
| 5 | MEDIUM | `main.py` | Empty questionnaire (0 questions) causes SSE generator infinite loop |
| 6 | LOW | `llm.py` | Google provider calls `genai.configure()` on every request — not thread-safe (global state mutation), low practical risk since value is always the same key |
| 7 | LOW | `llm.py` | Final `raise RuntimeError("Max retries exceeded...")` after retry loop is unreachable dead code |
| 8 | LOW | `Processing.jsx` | `onDone` in `useEffect` deps may cause EventSource to reopen on parent re-render if `onDone` is not stable |
| 9 | LOW | `Processing.jsx` | `total` state unknown during processing — progress percentage inaccurate (50% placeholder) for entire run |
| 10 | LOW | `Processing.jsx` | `onerror` closes EventSource without retry — hard error on transient network drop |

### What Is Correct

- ThreadPoolExecutor `as_completed` loop is single-threaded for result collection — no concurrent writes to `session.answers` from worker threads
- `processed_count` increment is in the `as_completed` loop (single thread) — safe on CPython
- `build_doc_context` called once per session and passed as `doc_context` — correct optimization, avoids per-question string reconstruction
- `_max_tokens_for_format()` logic is correct and appropriately sized per format
- `lru_cache` on Groq and Anthropic clients is correct — both SDKs are thread-safe
- Exponential backoff retry logic correctly identifies rate limit errors and re-raises non-rate-limit errors immediately
- SSE termination condition ordering (emit remaining answers, then `[DONE]`) is correct
- `list(session.answers.items())` snapshot approach is the right mitigation attempt for concurrent iteration (though not fully safe)
- SSE `Cache-Control: no-cache` and `X-Accel-Buffering: no` headers are correct for nginx-proxied SSE
- `session` object reference captured by generator closure prevents GC even if evicted from `sessions` dict
