# GDPR Compliance Controls
**Product**: Seques — Security Questionnaire Co-Pilot
Last updated: 2026-03-08 | Owner: Engineering | Review cycle: Quarterly

---

## Article Map

| GDPR Article | Title | Status | Notes |
|---|---|---|---|
| Art 5 | Principles of processing | 🟡 Partial | Data minimization implemented; lawfulness basis documented |
| Art 6 | Lawfulness of processing | 🟢 Documented | See `data_inventory.md` §5 |
| Art 13/14 | Information to data subjects | 🔴 Gap | Privacy notice not yet published |
| Art 17 | Right to erasure | 🟡 Partial | Restart erases all data; Phase 2 adds explicit DELETE endpoint |
| Art 20 | Right to data portability | 🟡 Partial | Export endpoints provide data in Excel/PDF |
| Art 25 | Privacy by design | 🟢 Implemented | In-memory only, doc truncation, no PII in analytics |
| Art 28 | Processor agreements | 🔴 Gap | DPAs not yet executed with sub-processors |
| Art 30 | Records of processing | 🟢 Implemented | `data_inventory.md` |
| Art 32 | Security of processing | 🟡 Partial | TLS headers, rate limiting, audit trail; no encryption at rest (no DB yet) |
| Art 33 | Breach notification | 🔴 Gap | No breach notification procedure documented |

---

## Privacy by Design Measures (Art 25)

### Data Minimization
- Compliance docs truncated to 8,000 chars per doc before LLM call (`engine.py:52`)
- Questionnaire text truncated to 10,000 chars (`parser.py:32`)
- Mixpanel receives only: session ID, event name, counts, provider name — **zero document content**

### Purpose Limitation
- IP addresses are logged for rate limiting and security only — not shared with LLM or analytics

### Storage Limitation
- Phase 1: all data held exclusively in RAM; automatically purged on server restart
- Phase 2: set retention policy on Supabase rows (90-day auto-delete)

### Integrity and Confidentiality
- Security headers prevent clickjacking, MIME sniffing, framing
- HSTS enforced in production
- API keys stored only in `.env`, never in source code (enforced by `.gitignore`)

---

## Lawful Basis Register

| Processing | Legal Basis | Justification |
|---|---|---|
| Ingesting uploaded documents | Art 6(1)(b) | Necessary to perform the contracted service |
| Sending doc excerpts to LLM | Art 6(1)(b) | Core service cannot function without this |
| Logging IP for rate limiting | Art 6(1)(f) | Legitimate interest: protect service availability |
| Analytics (Mixpanel) | Art 6(1)(f) | Legitimate interest: product improvement; no personal data in events |

---

## Data Subject Request Procedures

### Right of Access (Art 15)
**Current**: No persistent storage — respond "all data is session-scoped and erased on server restart."
**Phase 2**: Add `GET /api/sessions/{id}/export` covering all stored data.

### Right to Erasure (Art 17)
**Current**: Server restart. Document this in privacy notice.
**Phase 2**: `DELETE /api/sessions/{id}` removes all Supabase rows and Mixpanel profile.

### Right to Portability (Art 20)
**Current**: Excel and PDF export endpoints already serve this purpose.

---

## Open Gaps

| Gap | Article | Risk Level | Remediation |
|---|---|---|---|
| No privacy notice / cookie banner | Art 13 | High | Write and publish before beta |
| No DPAs with Groq, Google, Anthropic, Mixpanel | Art 28 | High | Execute before processing real user data |
| No breach notification procedure | Art 33 | Medium | Document 72-hour notification procedure |
| No Data Protection Officer (DPO) | Art 37 | Low (not required at this stage) | Revisit at scale |
