# QA Test Scenarios — Phase 1

## Smoke Tests (run after every deploy)

| # | Scenario | Steps | Expected |
|---|---|---|---|
| S1 | Health check | GET /health | `{"status":"ok"}` |
| S2 | Provider list | GET /api/providers | JSON with `providers` array |
| S3 | Create session (Groq) | POST /api/sessions `{"provider":"groq"}` | `{"session_id":"..."}` |
| S4 | Upload PDF | POST /api/sessions/{id}/docs multipart | `{"docs":[...]}` |
| S5 | Upload questionnaire | POST /api/sessions/{id}/questionnaire multipart | questions parsed |
| S6 | Process | POST /api/sessions/{id}/process | answers generated |
| S7 | Export | GET /api/sessions/{id}/export | downloadable file |

## Edge Cases

| # | Scenario | Expected |
|---|---|---|
| E1 | Upload non-PDF as doc | 400 error |
| E2 | Upload empty questionnaire | graceful error or empty questions |
| E3 | Process with no docs uploaded | LLM answers with "No evidence found" |
| E4 | Process with no questions uploaded | 400 or empty answers |
| E5 | Invalid session ID | 404 |
| E6 | Groq key missing, LLM_PROVIDER=groq | 500 with clear error message |
| E7 | Rapid fire 10 requests | rate limiter kicks in (when re-enabled) |

## Provider Scenarios

| Provider | Model | Test |
|---|---|---|
| groq | llama-3.3-70b-versatile | Full flow S1–S7 |
| anthropic | claude-haiku-4-5-20251001 | Full flow S1–S7 (requires key) |
| google | gemini-2.0-flash | Full flow S1–S7 (requires key) |

## Regression Checklist (after any backend change)
- [ ] ingest.py: upload a multi-page PDF — no `ValueError: document closed`
- [ ] CORS: frontend can reach all API endpoints
- [ ] Audit log: every action emitted to audit.log
- [ ] Analytics: Mixpanel events visible in dashboard
