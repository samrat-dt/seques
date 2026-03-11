# Seques — Architecture Reference
Last updated: 2026-03-11

---

## System Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    User Browser                          │
│  React + Vite + Tailwind  (https://seques.vercel.app)    │
│                                                          │
│  Auth: access-code gate (localStorage; Auth.jsx)         │
│  Every request: Authorization: Bearer <code>             │
│                                                          │
│  Screens: Landing → Auth → Upload → Processing → Review → Export
│  Processing: polling GET /api/sessions/{id}/status (1s)  │
│  Export: fetch()+blob (not direct <a href> links)        │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTPS (CORS)
                          ▼
┌──────────────────────────────────────────────────────────┐
│   FastAPI Backend  (https://seques-backend-production    │
│                     .up.railway.app)                     │
│                                                          │
│  _AUTH_ENABLED = False  (accepts any Bearer token;       │
│   JWT validation off — set AUTH_ENABLED=true to enable)  │
│                                                          │
│  Middleware stack (outermost → innermost):               │
│    RequestTracingMiddleware  — X-Request-ID header       │
│    SecurityHeadersMiddleware — HSTS, CSP, X-Frame etc.   │
│    RateLimitMiddleware       — 30 req/min per IP         │
│    CORSMiddleware            — configured origins        │
│                                                          │
│  Routes:                                                 │
│    GET  /health                                          │
│    GET  /api/providers                                   │
│    POST /api/sessions                  → create session  │
│    POST /api/sessions/{id}/docs        → ingest PDFs/DOCX│
│    POST /api/sessions/{id}/manual-doc  → ingest text     │
│    POST /api/sessions/{id}/questionnaire → parse Q's     │
│    POST /api/sessions/{id}/process     → kick off AI     │
│    GET  /api/sessions/{id}/status      → poll progress   │
│    GET  /api/sessions/{id}/stream      → SSE (unused*)   │
│    GET  /api/sessions/{id}/answers     → fetch results   │
│    PATCH /api/sessions/{id}/answers/{qid} → edit/approve │
│    GET  /api/sessions/{id}/export/excel                  │
│    GET  /api/sessions/{id}/export/pdf                    │
│    GET  /api/audit                     → audit log read  │
│                                                          │
│  * SSE endpoint exists but frontend uses polling instead │
│    (EventSource cannot send Authorization headers)       │
│                                                          │
│  Swagger UI:  /docs                                      │
│  ReDoc:       /redoc                                     │
│  OpenAPI JSON: /openapi.json                             │
└──────┬──────────────┬───────────────┬────────────────────┘
       │              │               │
       ▼              ▼               ▼
  LLM Provider   Mixpanel        audit.log (disk)        Supabase DB
  Groq (default) (analytics      append-only JSON        sessions, questions,
  Anthropic      events)        one line per event       answers, audit_events
  (Google: not
   configured)
```

---

## Module Map

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, all routes, middleware wiring, `_AUTH_ENABLED=False` |
| `engine.py` | `answer_question()` — draft-first answer generation; dynamic context scaling; domain knowledge fallback |
| `parser.py` | `parse_pdf/excel/text_questionnaire()` — extracts questions |
| `ingest.py` | `ingest_pdf/ingest_docx/manual()` — extracts text from PDF and DOCX, detects doc type |
| `llm.py` | `chat()` — unified LLM wrapper (Groq / Anthropic); key pool; exponential backoff |
| `models.py` | Pydantic data models |
| `export.py` | Excel and PDF export |
| `database.py` | Supabase CRUD; graceful fallback if not configured |
| `observability.py` | JSON logging, `RequestTracingMiddleware` |
| `audit.py` | Immutable audit event writer |
| `analytics.py` | Mixpanel wrapper (typed event helpers) |
| `security.py` | `SecurityHeadersMiddleware`, `RateLimitMiddleware` |

---

## Data Flow — Single Question Answered

```
1. User enters access code → stored in localStorage as seques_auth_token
   Every subsequent request includes: Authorization: Bearer <code>

2. User uploads SOC2.pdf and/or Policy.docx
   → ingest_pdf() / ingest_docx() extracts text → ComplianceDoc in session.docs
   → Unsupported file types returned in the "skipped" list

3. User pastes/uploads questionnaire
   → parser.py calls llm.chat() → returns JSON array of Question objects
   → stored in session.questions

4. User clicks "Process"
   → POST /process → background task runs run_answer_engine()
   → build_doc_context() called ONCE for all questions (not per-question)
   → Questions dispatched sequentially (ANSWER_CONCURRENCY=1 default)
   → For each question, answer_question() runs:
       a. engine.py builds a prompt using a "senior security compliance consultant"
          system persona with embedded SOC 2 / ISO 27001 framework knowledge and
          the pre-built shared doc context
       b. If uploaded docs lack relevant text, engine falls back to domain
          knowledge — answer_tone is always "assertive" or "hedged";
          "cannot_answer" is never emitted
       c. llm.chat() sends to chosen provider (dynamic max_tokens per format)
       d. Provider returns JSON with draft_answer, certainty, coverage
       e. engine.py validates + creates Answer object
       f. session.answers[question.id] = answer; written to Supabase DB
   → On completion: audit.emit("processing.complete"), analytics.processing_completed()

5. Frontend polls GET /api/sessions/{id}/status at 1-second intervals
   → Returns { processing, processed, total } for a progress indicator
   → When processing=false and processed>0: frontend calls getAnswers() then proceeds
   → Note: SSE endpoint (/stream) exists but is NOT used — EventSource cannot
     send Authorization headers, so it returned 401 in production

6. User edits or approves
   → PATCH /answers/{id} → audit.emit("answer.update")

7. User clicks Export
   → frontend: fetch() with Authorization header → receive binary response
   → creates blob URL → programmatic anchor click → download
   → Note: direct <a href> links are NOT used — they bypass JS and can't include
     auth headers, so they returned 401 in production
```

---

## Auth Architecture

### Frontend
- `supabase.js` exports `null` — Supabase JS client is intentionally disabled
- `Auth.jsx` is a simple access-code entry form (not Supabase Magic Link)
- Code is stored in `localStorage` as `seques_auth_token`
- `getAuthToken()` in `api.js` reads this value and includes it in every request header

### Backend
- `_AUTH_ENABLED = False` in `main.py` (hardcoded default)
- Backend accepts any Bearer token without JWT validation
- JWT validation infrastructure exists and is correct; activate with:
  - Set `AUTH_ENABLED=true` env var on Railway
  - Set `SUPABASE_JWT_SECRET` env var on Railway

### Why these choices were made
- Supabase Magic Link returned "invalid api key" in production despite env vars being set
- EventSource (SSE) cannot send `Authorization` headers in any browser — polling is the correct workaround
- Direct `<a href>` export links bypass the JavaScript layer — fetch+blob is required for authenticated downloads

---

## Answer Generation — Draft-First Approach

`engine.py` is designed to always produce a usable draft, never a refusal.

### Dynamic Context Scaling (`build_doc_context`)

| Scenario | Per-doc char budget |
|---|---|
| 1 doc | min(40,000, 96,000) = 40,000 chars |
| 2 docs | min(40,000, 48,000) = 40,000 chars |
| 3 docs | min(40,000, 32,000) = 32,000 chars |
| 6+ docs | min(40,000, 16,000) = 16,000 chars |

Total context across all docs is capped at 96,000 chars to stay within LLM context windows.

### Prompt Design

- **System role**: "senior security compliance consultant" persona
- **User prompt**: includes SOC 2 and ISO 27001 framework knowledge so the model can reason about standard controls even when uploaded docs are sparse
- **max_tokens**: dynamic per format (yes_no: 512, multiple_choice: 768, short_text: 1024, long_text: 2048)

### answer_tone Values

| Value | Meaning |
|---|---|
| `"assertive"` | High doc coverage — answer drawn directly from uploaded material |
| `"hedged"` | Low/no coverage — answer drawn from domain knowledge; reviewer should verify |

`"cannot_answer"` is not a valid output — the engine always produces a draft.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | No | `groq` | Active LLM provider (`groq` or `anthropic`) |
| `GROQ_API_KEY` | If using Groq | — | Groq API key; also `GROQ_API_KEY_2` … `GROQ_API_KEY_19` |
| `ANTHROPIC_API_KEY` | If using Anthropic | — | Anthropic API key |
| `GOOGLE_API_KEY` | If using Google | — | Google AI Studio key (not configured in production) |
| `AUTH_ENABLED` | No | unset (off) | Set to `true` to activate JWT validation; requires `SUPABASE_JWT_SECRET` |
| `SUPABASE_URL` | No | — | Supabase project URL; enables DB persistence |
| `SUPABASE_SERVICE_KEY` | No | — | Supabase service role key |
| `SUPABASE_JWT_SECRET` | No | — | Required only when `AUTH_ENABLED=true` |
| `MIXPANEL_TOKEN` | No | — | Mixpanel project token |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `ENVIRONMENT` | No | `development` | Affects CSP/HSTS headers; set `production` on Railway |
| `APP_VERSION` | No | `1.0.0` | Emitted in every log line |
| `RATE_LIMIT_PER_MINUTE` | No | `30` | Requests/min per IP |
| `ANSWER_CONCURRENCY` | No | `1` | Max parallel LLM calls; sequential by default |
| `QUESTION_DELAY_S` | No | `1.5` | Pause between sequential LLM calls (TPM headroom) |
| `DOC_CHAR_BUDGET` | No | `32000` | Total chars across all uploaded docs |
| `DOC_CHAR_LIMIT` | No | `16000` | Max chars per individual doc |
| `AUDIT_LOG_PATH` | No | `audit.log` | Path to audit log file |

---

## LLM Provider Comparison

| Provider | Model | Cost/run est. | Context | Notes |
|---|---|---|---|---|
| Groq | llama-3.3-70b-versatile | Free tier | 128K | Fast, generous free tier; default |
| Anthropic | claude-haiku-4-5-20251001 | ~$0.11/run | 200K | Most reliable JSON output |
| Google | gemini-2.0-flash | Free tier | 1M | Not configured in production |

---

## Document Ingestion

`ingest.py` accepts compliance documents and extracts plain text for use in answer generation.

### Supported File Types

| Type | Handler | Notes |
|---|---|---|
| `.pdf` | `ingest_pdf()` | Uses PyMuPDF / pdfplumber |
| `.docx` | `ingest_docx()` | Uses `python-docx`; text boxes and complex tables not extracted |
| Pasted text | `ingest_manual()` | Plain text via API body |

Unsupported file types are not silently dropped — the `POST /api/sessions/{id}/docs` endpoint returns a `skipped` list in the response body identifying any files that could not be processed.

---

## Phase 3 Priorities

1. **RAG** — chunk compliance docs, embed with a small model, store vectors in Supabase pgvector. Retrieve top-k chunks per question. Removes 32KB ceiling.
2. **Parallel processing** — revisit `ANSWER_CONCURRENCY > 1` with async LLM clients and Redis rate-budget tracking. Goal: reliable 10× concurrency.
3. **Redis** — replace in-memory rate limiter for distributed deployments.
4. **Multi-user accounts** — invite-based auth, per-user JWT, session isolation.
5. **Session history** — list and re-open past sessions.
6. **Answer templates** — pre-load standard approved language per control domain.
