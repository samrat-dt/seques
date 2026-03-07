# Operations Runbook
**Product**: Seques — Security Questionnaire Co-Pilot
Last updated: 2026-03-08

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
