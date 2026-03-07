# Data Inventory & Processing Register
**GDPR Art 30 — Records of Processing Activities**
**ISO 27001 A.8 — Asset Management**
**SOC 2 CC6.1 — Logical Access**

Last updated: 2026-03-08
Owner: Engineering
Review cycle: Quarterly

---

## 1. System Overview

**Product**: Seques — Security Questionnaire Co-Pilot
**Purpose**: Automates drafting of security questionnaire responses using vendor-supplied compliance documents and a large language model.
**Deployment**: Single-tenant MVP; in-memory session store (no database in Phase 1).

---

## 2. Data Elements Processed

| Data Element | Classification | Source | Purpose | Retention | Storage Location |
|---|---|---|---|---|---|
| Compliance document text (SOC 2, ISO, policies) | Confidential / Business | Uploaded by user | Evidence context for LLM | In-memory only; cleared on server restart | RAM |
| Questionnaire questions | Confidential / Business | Uploaded by user | Input to LLM | In-memory only | RAM |
| AI-generated answers | Confidential / Business | LLM output | Delivered to user | In-memory only | RAM |
| Session ID | Internal | Server-generated UUID | Session correlation | In-memory only | RAM |
| Client IP address | Personal (GDPR) | HTTP request | Rate limiting, audit trail | Audit log (disk) | `audit.log` |
| HTTP User-Agent | Personal (GDPR) | HTTP request | Observability | Structured log (stdout) | Log stream |
| Request ID (UUID) | Internal | Server-generated | Request tracing | Structured log | Log stream |
| LLM API key | Secret | Environment variable | LLM authentication | Never logged | `.env` file only |
| Mixpanel token | Secret | Environment variable | Analytics | Never logged | `.env` file only |

---

## 3. Third-Party Sub-Processors

| Vendor | Purpose | Data Sent | Region | DPA Link |
|---|---|---|---|---|
| Groq Inc. | LLM inference (llama-3.3-70b) | Question text + compliance doc excerpts (up to 8 KB per doc) | USA | https://groq.com/privacy |
| Google LLC | LLM inference (gemini-2.0-flash) | Same as above | USA | https://ai.google.dev/terms |
| Anthropic PBC | LLM inference (claude-haiku) | Same as above | USA | https://www.anthropic.com/legal/privacy |
| Mixpanel Inc. | Product analytics | Session ID, event names, provider used, question counts — **no document content** | USA | https://mixpanel.com/legal/privacy-policy |
| Supabase Inc. (Phase 2) | Persistent session storage | Session metadata, question/answer records | USA/EU (selectable) | https://supabase.com/privacy |

**Action required before production**: Execute Data Processing Agreements with each sub-processor.

---

## 4. Data Flows

```
User Browser
  │
  ├─► POST /api/sessions/{id}/docs         → PDF text extracted → RAM
  ├─► POST /api/sessions/{id}/questionnaire → questions parsed  → RAM
  └─► POST /api/sessions/{id}/process
          │
          ├─► LLM Provider (Groq/Google/Anthropic)
          │       Input:  system prompt + question + doc excerpts
          │       Output: JSON answer object
          │       Retention at provider: per their privacy policy
          │
          └─► Mixpanel (session_id + event metadata only — NO doc content)

All above ← IP address → audit.log (append-only, local disk)
```

---

## 5. Legal Basis for Processing (GDPR)

| Processing Activity | Legal Basis | Notes |
|---|---|---|
| Processing uploaded compliance docs | Art 6(1)(b) — Contract performance | User uploads to receive the service |
| Sending excerpts to LLM providers | Art 6(1)(b) — Contract performance | Core service function |
| Logging IP addresses | Art 6(1)(f) — Legitimate interest | Security monitoring, rate limiting |
| Analytics events | Art 6(1)(f) — Legitimate interest | No personal data in events |

---

## 6. Data Subject Rights (GDPR Art 17 — Right to Erasure)

**Current implementation**: All user data is in-memory. Restarting the server erases all sessions.

**Phase 2 (Supabase)**: Implement `DELETE /api/sessions/{id}` that purges all session data from Supabase.

User-facing privacy notice: **TODO** — add `/privacy` route and link in UI before public launch.

---

## 7. Data Minimization Measures (GDPR Art 5, ISO 27001 A.8.2)

- Compliance docs are truncated to 8,000 chars per doc before sending to LLM (`engine.py:52`)
- Questionnaire text truncated to 10,000 chars (`parser.py:32`)
- IP addresses are logged but never returned in API responses
- No PII fields are collected beyond what HTTP transport provides

---

## 8. Open Gaps / Remediation Plan

| Gap | Risk | Target Date |
|---|---|---|
| No persistent storage — all data lost on restart | Availability | Phase 2 (Supabase) |
| No authentication/authorization | High — any IP can access any session | Phase 2 |
| No DPAs signed with sub-processors | GDPR Art 28 non-compliance | Before beta launch |
| No privacy notice / ToS | GDPR Art 13 non-compliance | Before beta launch |
| Audit log is local file — not shipped to SIEM | SOC 2 gap | Phase 2 |
| Rate limiter uses in-memory store (not Redis) | Distributed deployment risk | Phase 2 |
