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
│    POST /api/sessions/{id}/docs        → ingest PDFs     │
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
| `engine.py` | `answer_question()` — builds prompt, calls LLM, parses JSON |
| `parser.py` | `parse_pdf/excel/text_questionnaire()` — extracts questions |
| `ingest.py` | `ingest_pdf/manual()` — extracts text, detects doc type |
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
1. User uploads SOC2.pdf
   → ingest_pdf() extracts text → ComplianceDoc in session.docs

2. User pastes/uploads questionnaire
   → parser.py calls llm.chat() → returns JSON array of Question objects
   → stored in session.questions

3. User clicks "Process"
   → POST /process → background task runs run_answer_engine()
   → For each question:
       a. engine.py builds a prompt (question + doc excerpts ≤8KB each)
       b. llm.chat() sends to chosen provider
       c. Provider returns JSON with draft_answer, certainty, coverage
       d. engine.py validates + creates Answer object
       e. session.answers[question.id] = answer
       f. audit.emit("processing.complete")
       g. analytics.processing_completed()

4. Frontend polls GET /status until processing=false
   → Renders QuestionCard for each answer

5. User edits or approves
   → PATCH /answers/{id} → audit.emit("answer.update")

6. User clicks Export
   → GET /export/excel or /export/pdf → download
```

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

## Phase 2 Priorities

1. **Authentication** — Supabase Auth (magic link or Google OAuth)
2. **Persistence** — Supabase Postgres for sessions, answers, audit events
3. **RAG** — vector embeddings for large compliance docs (>8KB)
4. **SIEM** — ship `audit.log` to Datadog / Logtail
5. **Redis** — replace in-memory rate limiter for distributed deployments
6. **Background jobs** — Celery/RQ instead of FastAPI background tasks for reliability
