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
| S8 | Upload .docx compliance doc | POST /api/sessions/{id}/docs multipart with a .docx file | 200 response; file appears in `docs` list, not in `skipped` |
| S9 | Upload unsupported type (.txt) as compliance doc | POST /api/sessions/{id}/docs multipart with a .txt file | 200 response; file appears in `skipped` list, not in `docs` |

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

## Provider Scenarios

| Provider | Model | Test |
|---|---|---|
| groq | llama-3.3-70b-versatile | Full flow S1–S7 |
| anthropic | claude-haiku-4-5-20251001 | Full flow S1–S7 (requires key) |
| google | gemini-2.0-flash | Full flow S1–S7 (requires key) |

## Draft-First Behavior Scenarios

| # | Scenario | Steps | Expected |
|---|---|---|---|
| D1 | Process with SOC 2 PDF uploaded | Upload a SOC 2 PDF as compliance doc, upload questionnaire, POST /process | NO answer in the response contains the text "cannot answer"; all `draft_answer` fields contain substantive text |
| D2 | Process with no docs uploaded (empty doc list) | Create session, skip doc upload, upload questionnaire, POST /process | All answers have `answer_tone: "hedged"`, `evidence_coverage: "none"`, and `draft_answer` begins with "As a SOC 2" or equivalent professional framing (not a refusal) |
| D3 | Context scaling — 3 docs uploaded | Upload SOC 2 PDF + 2 policy PDFs/docx, upload questionnaire, POST /process | Processing completes without crash or timeout; all questions receive a `draft_answer` |
| D4 | 30-question XLSX questionnaire | Upload `docs/sample_questionnaire.xlsx` as questionnaire, POST /process | Exactly 30 questions parsed; all 30 receive a `draft_answer` |

## Regression Checklist (after any backend change)
- [ ] ingest.py: upload a multi-page PDF — no `ValueError: document closed`
- [ ] CORS: frontend can reach all API endpoints
- [ ] Audit log: every action emitted to audit.log
- [ ] Analytics: Mixpanel events visible in dashboard
- [ ] engine.py: no answer has `draft_answer` containing "cannot answer", "not available", or "evidence not found"
- [ ] engine.py: hedged answers start with "As a SOC 2" or equivalent professional framing (no refusal language)
- [ ] ingest.py: .docx upload extracts text correctly (paragraphs joined with double newline)
- [ ] main.py: uploading a .txt file returns `{"docs": [], "skipped": ["filename.txt"]}`
