# Operations Runbook
**Product**: Seques — Security Questionnaire Co-Pilot
Last updated: 2026-03-09

---

## Start / Stop

```bash
# Start backend
cd backend && uvicorn main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Health check
curl http://localhost:8000/health
```

---

## Changing LLM Provider

1. Edit `backend/.env`:
   ```
   LLM_PROVIDER=groq   # or: anthropic | google
   GROQ_API_KEY=gsk_...
   ```
2. Restart uvicorn. No code change needed.
3. Verify: `curl http://localhost:8000/api/providers` — check `"configured": true` for chosen provider.

---

## Incident Response (SOC 2 CC7.4)

### API key compromised
1. Immediately rotate the key at the provider's console
2. Update `.env` with new key
3. Restart backend
4. Audit: check `audit.log` for any unexpected `session.create` events from unknown IPs
5. Notify affected users if any session data was accessed

### LLM provider outage
1. Check provider status page (Groq: https://status.groq.com / Google: https://status.cloud.google.com)
2. Switch `LLM_PROVIDER` to a working provider and restart
3. Groq → Google: `LLM_PROVIDER=google` + ensure `GOOGLE_API_KEY` is set
4. Log incident in this file under "Incident Log"

### Rate limit abuse
1. Check `audit.log` for `"msg": "rate_limit_exceeded"` entries and offending IP
2. Block IP at reverse proxy/firewall level
3. If distributed attack, reduce `RATE_LIMIT_PER_MINUTE` temporarily

### Processing too slow / high LLM latency
1. Check `audit.log` for `"action": "processing.complete"` events — inspect `duration_ms`
2. Increase parallel workers: set `ANSWER_CONCURRENCY` (default: `10`) in `backend/.env` and restart
3. Reduce if hitting LLM provider rate limits — lower concurrency means fewer simultaneous API calls
4. Switch to a faster provider: Groq is typically fastest on free tier

---

## Reading the Audit Log

```bash
# Last 50 events
tail -50 backend/audit.log | jq .

# All session creation events
grep '"action": "session.create"' backend/audit.log | jq .

# All events from a specific session
grep '"resource_id": "SESSION_UUID"' backend/audit.log | jq .

# All failure events
grep '"outcome": "failure"' backend/audit.log | jq .

# Events from last 1 hour
# (requires jq + ts field parsing)
cat backend/audit.log | jq 'select(.ts > "2026-03-08T10:00:00")'
```

Or use the API:
```
GET http://localhost:8000/api/audit?limit=100
```

---

## Checking Logs

```bash
# Structured JSON — pipe through jq for readability
uvicorn main:app 2>&1 | jq .

# Filter for errors only
uvicorn main:app 2>&1 | jq 'select(.level == "ERROR")'

# Filter by request ID (trace a specific request)
uvicorn main:app 2>&1 | jq 'select(.request_id == "YOUR-REQUEST-ID")'
```

---

## Testing New Features (2026-03-08)

### Standard Test Questionnaire

`docs/sample_questionnaire.xlsx` is the go-to test file. It contains 30 questions across 8 categories (access control, encryption, incident response, etc.) and is designed to exercise the full answer-generation pipeline. Use it whenever verifying a new LLM provider, prompt change, or ingestion change.

---

### Uploading a .docx Compliance Document

`.docx` is now supported alongside `.pdf`. To verify:

```bash
# Upload a .docx file to an existing session
curl -X POST http://localhost:8000/api/sessions/{SESSION_ID}/docs \
  -F "files=@/path/to/your-policy.docx"
```

Expected response shape:
```json
{
  "ingested": ["your-policy.docx"],
  "skipped": []
}
```

If a file type is not supported, it appears in `"skipped"` rather than causing an error. Check `"skipped"` in the response to confirm all files were accepted.

---

### Verifying Draft-First Answer Generation

After processing, the engine must always produce a draft — `"cannot_answer"` must never appear in output.

```bash
# Fetch answers for a session
curl http://localhost:8000/api/sessions/{SESSION_ID}/answers | jq .

# Confirm no "cannot_answer" tone values
curl http://localhost:8000/api/sessions/{SESSION_ID}/answers \
  | jq '[.[] | select(.answer_tone == "cannot_answer")]'
# Expected output: []

# Confirm all answers have a non-empty draft_answer
curl http://localhost:8000/api/sessions/{SESSION_ID}/answers \
  | jq '[.[] | select(.draft_answer == "" or .draft_answer == null)]'
# Expected output: []
```

Valid `answer_tone` values are `"assertive"` (answer backed by uploaded docs) and `"hedged"` (answer drawn from domain knowledge — reviewer should verify). Both are acceptable; `"cannot_answer"` is a bug.

---

### End-to-End Smoke Test (new feature path)

1. Start backend and frontend (see Start/Stop above).
2. Create a session: `POST /api/sessions`
3. Upload a `.docx` policy doc and confirm it appears in `"ingested"`.
4. Upload `docs/sample_questionnaire.xlsx` via the frontend or `POST /api/sessions/{id}/questionnaire`.
5. Trigger processing: `POST /api/sessions/{id}/process`
6. Stream answers in real time via SSE: `GET /api/sessions/{id}/stream` (preferred), or poll `GET /api/sessions/{id}/status` until `"processing": false`.
7. Fetch answers and run the `"cannot_answer"` check above.
8. Spot-check several `"hedged"` answers — they should contain substantive draft text, not a refusal.

---

### Streaming Answers via SSE (2026-03-09)

The `GET /api/sessions/{id}/stream` endpoint streams answers as Server-Sent Events while processing is running. Each event carries the full JSON payload of one answer. A final `data: [DONE]` sentinel is sent when all answers are complete.

```bash
# Consume the SSE stream from a terminal
curl -N http://localhost:8000/api/sessions/{SESSION_ID}/stream

# Each event looks like:
# data: {"question_id": "...", "draft_answer": "...", "answer_tone": "assertive", ...}
#
# Final event:
# data: [DONE]
```

Headers returned by the endpoint:
- `Content-Type: text/event-stream`
- `Cache-Control: no-cache`
- `X-Accel-Buffering: no` — disables nginx proxy buffering so events reach the client immediately

Use the SSE stream when you want answers to appear incrementally (e.g., in the Review screen). Use the polling endpoint (`GET /status`) when you only need a completion signal.

---

## Updating Dependencies

```bash
cd backend
pip install --upgrade -r requirements.txt
# Test locally before deploying
# Check for breaking changes in: anthropic, fastapi, pydantic
```

---

## Incident Log

| Date | Incident | Resolution | Duration |
|---|---|---|---|
| — | — | — | — |

---

## Monitoring Checklist (Weekly)

- [ ] Check `audit.log` size — rotate if > 100MB
- [ ] Check `GET /api/audit?limit=500` for anomalies (unexpected actors, failure outcomes)
- [ ] Verify Mixpanel is receiving events (Live View)
- [ ] Check LLM provider billing dashboards
- [ ] Review any rate limit events for abuse patterns
