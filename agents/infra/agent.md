# Infra Agent — Seques
> Last updated: 2026-03-09
> Phase: Phase 1 checkpoint — infra readiness review

---

## Responsibilities
- Supabase schema, migrations, RLS policies
- GitHub Actions CI/CD pipeline
- Environment variable management across dev/staging/prod
- Containerisation (Docker, docker-compose)
- Process supervision in production (gunicorn, systemd, or container orchestrator)
- HTTPS termination, reverse-proxy config
- Log shipping (audit.log → Supabase or external SIEM)
- Mixpanel dashboard setup

---

## Phase 1 Infra Readiness Report

### 1. Current Setup (as-is)

| Component | Current state |
|---|---|
| Runtime | FastAPI + `uvicorn --reload` (dev flag) |
| Session storage | In-memory Python dict (`sessions: Dict[str, Session]`) |
| Persistence | Supabase (live URL configured; **migration SQL not yet run**) |
| Reverse proxy | None |
| HTTPS | None (bare uvicorn on :8000) |
| Process supervisor | None (bare shell process) |
| CORS | `allow_origins=["*"]` — open wildcard |
| Auth | None (Phase 2) |
| Rate limiting | In-memory per-IP counter (middleware temporarily disabled; see main.py L69) |
| Container | None |

The app reads all credentials from `backend/.env` via `python-dotenv`.

Env vars of note confirmed present in `.env`:
- `LLM_PROVIDER`, `GROQ_API_KEY*` (5 keys for rotation), `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`
- `MIXPANEL_TOKEN`, `MIXPANEL_API_SECRET`
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- `ENVIRONMENT=development`, `LOG_LEVEL=INFO`, `APP_VERSION=1.0.0`
- `ANSWER_CONCURRENCY=1`, `QUESTION_DELAY_S=1.5`
- `DOC_CHAR_BUDGET=32000`, `DOC_CHAR_LIMIT=16000`
- `RATE_LIMIT_PER_MINUTE=30`

**No `.env` is committed** (gitignored). Confirmed acceptable for Phase 1; Phase 2 requires a secrets manager.

---

### 2. Production Blockers (must fix before any prod deploy)

#### 2.1 Remove `--reload` from uvicorn start command
`--reload` watches the filesystem and hot-restarts the process. It must never run in production:
- It spawns a file-watcher child process that consumes extra memory and CPU.
- It silently masks startup errors by restarting instead of crashing cleanly.
- Systemd/container health probes will behave unpredictably.

**Fix**: Switch to gunicorn with the uvicorn worker class:
```bash
gunicorn main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 2 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile -
```
Worker count rule of thumb: `2 * CPU_cores + 1`. Start with 2 for a single-core container.
`--timeout 120` is important — LLM calls can take 30-90s per question; the default 30s will kill in-flight requests.

#### 2.2 CORS wildcard must be tightened
`main.py` line 74–79:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```
In production, replace `["*"]` with an explicit allowlist driven by an env var:
```python
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5174").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, ...)
```
Set `ALLOWED_ORIGINS=https://app.seques.io` in the production env.

#### 2.3 HTTPS termination not documented
The app has no TLS. Production options (pick one):
- **Recommended for simplicity**: Caddy as reverse proxy — auto-renews Let's Encrypt certs, single binary, minimal config.
- **If on cloud**: Terminate at the load balancer (AWS ALB, GCP LB) and forward HTTP internally.
- **Nginx**: Standard choice; requires certbot for cert renewal.

Until HTTPS is in place, the app must not receive real customer data.

#### 2.4 No process supervisor
If the uvicorn/gunicorn process dies (OOM, panic), it does not restart. Options:
- **Docker with restart policy**: `restart: unless-stopped` in docker-compose (see docker-compose.yml created below).
- **systemd unit**: For bare-metal/VM deploys.
- **Cloud run / ECS / Fly.io**: Container orchestrators handle restarts natively.

#### 2.5 Health check endpoint — already exists, wire it up
`GET /health` returns `{"status": "ok", "version": "..."}` at line 195 of `main.py`. Good.
It must be registered with the process supervisor / load balancer for liveness probes. See Dockerfile HEALTHCHECK below.

#### 2.6 In-memory session store does not survive restarts
`sessions: Dict[str, Session]` is process-local. A process restart or second worker wipes all in-flight sessions. The Supabase restore path (`_restore_session`) is implemented but only recovers sessions for which the migration has been run.

**Immediate action required**: Run `backend/migrations/001_initial_schema.sql` in Supabase dashboard before any production use.

#### 2.7 Security middleware disabled
`main.py` lines 39-41 and 69-72 confirm `SecurityHeadersMiddleware`, `RateLimitMiddleware`, and `RequestTracingMiddleware` are commented out due to a CORS interaction bug. Before production:
- Fix the middleware ordering (CORS middleware must be outermost).
- Re-enable security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options).
- Re-enable in-memory rate limiter as a stopgap until Redis is available.

This is tracked in `agents/security/agent.md`.

#### 2.8 Audit log is a flat file
`audit.log` is written to the working directory. On a container restart the file is lost. Before production:
- Mount a persistent volume for the audit log, OR
- Ship logs to Supabase `audit_events` table (already partially implemented via `audit.emit()`), OR
- Stream to an external SIEM (Datadog, Papertrail, Logtail).

#### 2.9 `/api/audit` endpoint is unauthenticated
`main.py` line 720 — the audit trail is readable by anyone who can reach the API. This leaks session IDs and IP addresses. Gate behind auth before prod.

---

### 3. Docker Artifacts

A `backend/Dockerfile` and a `docker-compose.yml` at the repo root have been created (see those files). They provide:
- Reproducible Python 3.9 environment matching the development stack.
- Gunicorn + uvicorn workers (no `--reload`).
- Environment variables passed via `.env` file (never baked into the image).
- Health check wired to `GET /health`.
- Frontend served via Vite dev server in the compose stack (development parity only).

---

### 4. Phase 2 Infra Priorities (ordered)

| Priority | Task | Rationale |
|---|---|---|
| 1 | Run Supabase migration `001_initial_schema.sql` | Nothing persists without this; restarts lose all sessions |
| 2 | Fix + re-enable security middleware | CORS bug blocks security headers and rate limiting |
| 3 | Tighten CORS `allow_origins` | Wildcard is a pre-launch security gap |
| 4 | Switch to gunicorn in all non-dev environments | `--reload` in prod is a reliability and security risk |
| 5 | Add HTTPS termination (Caddy or ALB) | No customer data before TLS |
| 6 | Add process supervisor / container restart policy | Unattended restarts on crash |
| 7 | Persist audit log (volume mount or ship to Supabase) | Compliance requires durable audit trail |
| 8 | Gate `/api/audit` behind auth | Leaks session metadata |
| 9 | Replace in-memory rate limiter with Redis | In-memory limiter is per-process; breaks with multiple workers |
| 10 | Secrets manager (AWS SSM / Doppler / Vault) | `.env` files don't scale across environments |
| 11 | Supabase Auth integration | Multi-tenancy, per-user RLS policies |
| 12 | RAG pipeline for large docs | Current 32k char budget truncates large compliance libraries |
| 13 | CDN + static asset hosting for frontend | Vite dev server is not production-grade |
| 14 | Observability stack (structured logs → Datadog/Logtail, traces → OTEL) | `RequestTracingMiddleware` is already written, just needs a sink |
| 15 | Staging environment | Dev → Staging → Prod promotion path before any customer traffic |

---

### 5. GitHub Actions CI (existing template, confirmed)

`.github/workflows/ci.yml` is set up (CI/CD marked complete in project-state.md).
Verify the workflow runs `pytest tests/` against the backend on every push.

---

### 6. Supabase Setup Steps (immediate — blocking Phase 2)

1. Open: https://supabase.com/dashboard/project/deekxushpzcxmzdcvfxq/sql/new
2. Paste and run: `backend/migrations/001_initial_schema.sql`
3. Verify tables exist: `sessions`, `questions`, `answers`, `audit_events`
4. RLS is enabled on all tables; service role key (in `.env`) bypasses it for Phase 1.
5. Phase 2: add per-user row-level security policies once Supabase Auth is wired up.

---

### 7. Mixpanel Dashboards to Create

1. **Activation Funnel** — `session_created` → `questionnaire_uploaded` → `processing_started` → `export_downloaded`
2. **Provider A/B** — `processing_completed` grouped by `provider`, chart `duration_ms` avg
3. **Quality** — avg `ai_certainty`, `needs_review` rate per session
4. **Errors** — `api_error` events grouped by `path` + `status_code`
5. **Session volume** — daily/weekly `session_created` count (growth signal)
