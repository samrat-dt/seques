# Seques — Architecture Reference
Last updated: 2026-03-08

---

## System Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    User Browser                          │
│  React + Vite + Tailwind  (localhost:5173)               │
│                                                          │
│  Screens: Upload → Processing (poll) → Review → Export   │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTP (CORS)
                          ▼
┌──────────────────────────────────────────────────────────┐
│              FastAPI Backend  (localhost:8000)            │
│                                                          │
│  Middleware stack (outermost → innermost):               │
│    RequestTracingMiddleware  — X-Request-ID header       │
│    SecurityHeadersMiddleware — HSTS, CSP, X-Frame etc.   │
│    RateLimitMiddleware       — 30 req/min per IP         │
│    CORSMiddleware            — localhost:5173/3000        │
│                                                          │
│  Routes:                                                 │
│    GET  /health                                          │
│    GET  /api/providers                                   │
│    POST /api/sessions                  → create session  │
│    POST /api/sessions/{id}/docs        → ingest PDFs/DOCX │
│    POST /api/sessions/{id}/manual-doc  → ingest text     │
│    POST /api/sessions/{id}/questionnaire → parse Q's     │
│    POST /api/sessions/{id}/process     → kick off AI     │
│    GET  /api/sessions/{id}/status      → poll progress   │
│    GET  /api/sessions/{id}/answers     → fetch results   │
│    PATCH /api/sessions/{id}/answers/{qid} → edit/approve │
│    GET  /api/sessions/{id}/export/excel                  │
│    GET  /api/sessions/{id}/export/pdf                    │
│    GET  /api/audit                     → audit log read  │
│                                                          │
│  Swagger UI:  /docs                                      │
│  ReDoc:       /redoc                                     │
│  OpenAPI JSON: /openapi.json                             │
└──────┬──────────────┬───────────────┬────────────────────┘
       │              │               │
       ▼              ▼               ▼
  LLM Provider   Mixpanel        audit.log (disk)
  (Groq/Google/  (analytics      append-only JSON
   Anthropic)     events)        one line per event
```

---

## Module Map

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, all routes, middleware wiring |
| `engine.py` | `answer_question()` — draft-first answer generation; dynamic context scaling; domain knowledge fallback |
| `parser.py` | `parse_pdf/excel/text_questionnaire()` — extracts questions |
| `ingest.py` | `ingest_pdf/ingest_docx/manual()` — extracts text from PDF and DOCX, detects doc type |
| `llm.py` | `chat()` — unified LLM wrapper (Anthropic / Groq / Google) |
| `models.py` | Pydantic data models |
| `export.py` | Excel and PDF export |
| `observability.py` | JSON logging, `RequestTracingMiddleware` |
| `audit.py` | Immutable audit event writer |
| `analytics.py` | Mixpanel wrapper (typed event helpers) |
| `security.py` | `SecurityHeadersMiddleware`, `RateLimitMiddleware` |

---

## Data Flow — Single Question Answered

```
1. User uploads SOC2.pdf and/or Policy.docx
   → ingest_pdf() / ingest_docx() extracts text → ComplianceDoc in session.docs
   → Unsupported file types are returned in the "skipped" list

2. User pastes/uploads questionnaire
   → parser.py calls llm.chat() → returns JSON array of Question objects
   → stored in session.questions

3. User clicks "Process"
   → POST /process → background task runs run_answer_engine()
   → For each question:
       a. engine.py calls build_doc_context():
            - Per-doc budget: min(40k, 96k ÷ n) chars, where n = number of docs
            - Total context cap: 96k chars across all docs
       b. engine.py builds a prompt using a "senior security compliance consultant"
          system persona with embedded SOC 2 / ISO 27001 framework knowledge
       c. If uploaded docs lack relevant text, engine falls back to domain
          knowledge — answer_tone is always "assertive" or "hedged";
          "cannot_answer" is never emitted
       d. llm.chat() sends to chosen provider (max_tokens: 2048)
       e. Provider returns JSON with draft_answer, certainty, coverage
       f. engine.py validates + creates Answer object
       g. session.answers[question.id] = answer
       h. audit.emit("processing.complete")
       i. analytics.processing_completed()

4. Frontend polls GET /status until processing=false
   → Renders QuestionCard for each answer

5. User edits or approves
   → PATCH /answers/{id} → audit.emit("answer.update")

6. User clicks Export
   → GET /export/excel or /export/pdf → download
```

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
- **max_tokens**: 2,048 (doubled from original 1,024)

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
| `LLM_PROVIDER` | No | `anthropic` | Active LLM provider |
| `ANTHROPIC_API_KEY` | If using Anthropic | — | Anthropic API key |
| `GROQ_API_KEY` | If using Groq | — | Groq API key |
| `GOOGLE_API_KEY` | If using Google | — | Google AI Studio key |
| `MIXPANEL_TOKEN` | No | — | Mixpanel project token |
| `SUPABASE_URL` | No (Phase 2) | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | No (Phase 2) | — | Supabase service role key |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `ENVIRONMENT` | No | `development` | Affects CSP/HSTS headers |
| `APP_VERSION` | No | `1.0.0` | Emitted in every log line |
| `RATE_LIMIT_PER_MINUTE` | No | `30` | Requests/min per IP (mutations) |
| `AUDIT_LOG_PATH` | No | `audit.log` | Path to audit log file |

---

## LLM Provider Comparison

| Provider | Model | Cost/run est. | Context | Notes |
|---|---|---|---|---|
| Groq | llama-3.3-70b-versatile | Free tier | 128K | Fast, generous free tier |
| Google | gemini-2.0-flash | Free tier | 1M | Largest context window |
| Anthropic | claude-haiku-4-5 | ~$0.11/run | 200K | Most reliable JSON output |

---

## Document Ingestion

`ingest.py` accepts compliance documents and extracts plain text for use in answer generation.

### Supported File Types

| Type | Handler | Notes |
|---|---|---|
| `.pdf` | `ingest_pdf()` | Uses PyMuPDF / pdfplumber |
| `.docx` | `ingest_docx()` | Uses `python-docx`; added 2026-03-08 |
| Pasted text | `ingest_manual()` | Plain text via API body |

Unsupported file types are not silently dropped — the `POST /api/sessions/{id}/docs` endpoint returns a `skipped` list in the response body identifying any files that could not be processed.

---

## Phase 2 Priorities

1. **Authentication** — Supabase Auth (magic link or Google OAuth)
2. **Persistence** — Supabase Postgres for sessions, answers, audit events
3. **RAG** — vector embeddings for large compliance docs; current approach scales to ~40k chars/doc / 96k total without RAG
4. **SIEM** — ship `audit.log` to Datadog / Logtail
5. **Redis** — replace in-memory rate limiter for distributed deployments
6. **Background jobs** — Celery/RQ instead of FastAPI background tasks for reliability
