# ISO 27001:2022 Controls Assessment
**Product**: Seques — Security Questionnaire Co-Pilot
Last updated: 2026-03-08 | Owner: Engineering | Review cycle: Quarterly

---

## Annex A Controls

### A.5 — Organizational Controls

| Control | Title | Status | Implementation |
|---|---|---|---|
| A.5.1 | Policies for information security | 🔴 Gap | Draft security policy needed |
| A.5.2 | Information security roles | 🔴 Gap | Assign CISO/security lead |
| A.5.9 | Inventory of information assets | 🟢 Implemented | `data_inventory.md` |
| A.5.10 | Acceptable use | 🔴 Gap | ToS not yet drafted |
| A.5.15 | Access control | 🔴 Gap | No auth in Phase 1 |
| A.5.23 | Information security for cloud services | 🟡 Partial | Sub-processors listed; DPAs pending |

### A.6 — People Controls

| Control | Title | Status | Implementation |
|---|---|---|---|
| A.6.1 | Screening | 🔴 Gap | No HR process yet |
| A.6.2 | Terms and conditions of employment | 🔴 Gap | — |
| A.6.3 | Information security awareness | 🔴 Gap | No training program yet |

### A.7 — Physical Controls

| Control | Title | Status | Implementation |
|---|---|---|---|
| A.7.1 | Physical security perimeters | 🟢 N/A | Cloud-hosted; provider responsibility |
| A.7.8 | Equipment siting and protection | 🟢 N/A | Cloud-hosted |

### A.8 — Technological Controls

| Control | Title | Status | Implementation |
|---|---|---|---|
| A.8.1 | User endpoint devices | 🟡 Partial | Dev machines — enforce FDE (FileVault/BitLocker) |
| A.8.2 | Privileged access rights | 🔴 Gap | No auth system yet |
| A.8.3 | Information access restriction | 🟡 Partial | Rate limiting, session isolation |
| A.8.4 | Access to source code | 🟡 Partial | Git — restrict to named collaborators |
| A.8.5 | Secure authentication | 🔴 Gap | No auth |
| A.8.9 | Configuration management | 🟡 Partial | `.env.example` documents all config; secrets in `.env` (gitignored) |
| A.8.12 | Data leakage prevention | 🟡 Partial | No document content in analytics or audit logs |
| A.8.15 | Logging | 🟢 Implemented | Structured JSON logging (`observability.py`), audit trail (`audit.py`) |
| A.8.16 | Monitoring activities | 🟡 Partial | Logs emitted; no SIEM yet |
| A.8.20 | Network security | 🟢 Implemented | Security headers, HSTS (prod), CORS restricted |
| A.8.21 | Security of network services | 🟡 Partial | TLS via hosting provider; verify in prod |
| A.8.24 | Use of cryptography | 🟡 Partial | TLS for data in transit; no encryption at rest (no DB yet) |
| A.8.25 | Secure development lifecycle | 🟡 Partial | Code review process TBD |
| A.8.28 | Secure coding | 🟢 Implemented | No SQL (no DB), no template injection, parameterized prompts |
| A.8.29 | Security testing | 🔴 Gap | No automated security scanning |
| A.8.30 | Outsourced development | 🟢 N/A | Internal only |
| A.8.34 | Protection of information systems during audit testing | 🟡 Partial | Audit log is read-only endpoint |

---

## Risk Register

| Risk ID | Asset | Threat | Likelihood | Impact | Control | Residual Risk |
|---|---|---|---|---|---|---|
| R001 | Compliance docs in RAM | Server compromise | Low | High | TLS, no persistence | Medium |
| R002 | LLM API keys | Key leakage via env | Medium | High | `.env` gitignored, never logged | Low |
| R003 | LLM provider availability | Groq/Google outage | Medium | Medium | Multi-provider fallback | Low |
| R004 | Session data loss | Server restart | High | Medium | Acceptable in Phase 1; Supabase in Phase 2 | Low (by design) |
| R005 | Rate limit bypass | Distributed attack | Medium | Medium | In-memory limiter (Phase 2: Redis) | Medium |
| R006 | Prompt injection via questionnaire | Malicious PDF | Low | Medium | System prompt isolation, output validated as JSON | Low |
| R007 | Data sent to wrong LLM | Misconfigured provider | Low | High | Provider validated from env; clear error messages | Low |

---

## Statement of Applicability (SoA) Summary

- **Applicable controls**: A.5.9, A.8.3, A.8.9, A.8.15, A.8.16, A.8.20, A.8.24, A.8.28
- **Not applicable**: A.7 (physical — cloud hosted), A.6 (people — pre-team)
- **Gap controls** (implement Phase 2): A.5.1, A.5.2, A.5.15, A.8.2, A.8.5, A.8.29
