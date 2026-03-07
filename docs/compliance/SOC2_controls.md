# SOC 2 Type II Controls Assessment
**Product**: Seques — Security Questionnaire Co-Pilot
**Trust Service Criteria**: Security (CC), Availability (A)
Last updated: 2026-03-08 | Review cycle: Quarterly | Owner: Engineering

---

## Common Criteria (CC) — Security

### CC1 — Control Environment

| Control | Requirement | Status | Implementation | Evidence |
|---|---|---|---|---|
| CC1.1 | COSO principle — integrity & ethical values | 🟡 Partial | Code of conduct TBD | — |
| CC1.2 | Board oversight of internal controls | 🔴 Not implemented | N/A (pre-company) | — |
| CC1.3 | Organizational structure & reporting | 🔴 Not implemented | Document org chart | — |

### CC2 — Communication & Information

| Control | Requirement | Status | Implementation | Evidence |
|---|---|---|---|---|
| CC2.1 | COSO principle — quality information | 🟡 Partial | Structured logging in `observability.py` | Log output |
| CC2.2 | Internal communication | 🟡 Partial | Swagger docs at `/docs`, handover doc | `docs/handover.md` |
| CC2.3 | External communication | 🔴 Gap | Privacy notice not yet published | — |

### CC6 — Logical and Physical Access Controls

| Control | Requirement | Status | Implementation | Evidence |
|---|---|---|---|---|
| CC6.1 | Logical access — restrict to authorized users | 🔴 Gap | **No auth in Phase 1** — Phase 2 priority | `docs/compliance/data_inventory.md` §8 |
| CC6.2 | Authentication mechanisms | 🔴 Gap | No login flow yet | — |
| CC6.3 | Authorization — role-based access | 🔴 Gap | Single-tenant, no roles | — |
| CC6.6 | Logical access to external systems | 🟢 Implemented | API keys in `.env`, never in code | `.env.example`, `llm.py` |
| CC6.7 | Restrict transmission of confidential info | 🟢 Implemented | TLS enforced in prod (HSTS header), doc text not sent to analytics | `security.py` |

### CC7 — System Operations

| Control | Requirement | Status | Implementation | Evidence |
|---|---|---|---|---|
| CC7.1 | Vulnerability detection | 🟡 Partial | No automated scanning yet (add Dependabot) | — |
| CC7.2 | Monitor for anomalies | 🟢 Implemented | Audit trail (`audit.py`), structured logs, rate limiting | `audit.log`, `observability.py` |
| CC7.3 | Evaluate security events | 🟡 Partial | Logs emitted; no SIEM ingestion yet | — |
| CC7.4 | Incident response | 🟡 Partial | See runbook | `docs/runbook.md` |

### CC8 — Change Management

| Control | Requirement | Status | Implementation | Evidence |
|---|---|---|---|---|
| CC8.1 | Authorize, design, develop, test changes | 🟡 Partial | Git history, PR reviews (to be enforced) | Git log |

### CC9 — Risk Mitigation

| Control | Requirement | Status | Implementation | Evidence |
|---|---|---|---|---|
| CC9.2 | Vendor risk management | 🟡 Partial | Sub-processor list documented | `data_inventory.md` §3 |

---

## Availability (A)

| Control | Requirement | Status | Implementation | Evidence |
|---|---|---|---|---|
| A1.1 | Current processing capacity | 🟡 Partial | Single uvicorn worker; no horizontal scale | — |
| A1.2 | Environmental protections | 🟡 Partial | `/health` endpoint for liveness probes | `main.py` |
| A1.3 | Recovery from disruption | 🔴 Gap | No data persistence; session loss on restart | Phase 2 (Supabase) |

---

## Remediation Roadmap

| Priority | Control Gap | Action | Phase |
|---|---|---|---|
| P0 | CC6.1/6.2 — No authentication | Add JWT auth (Supabase Auth) | Phase 2 |
| P0 | A1.3 — No persistence | Supabase session storage | Phase 2 |
| P1 | CC7.3 — No SIEM | Ship audit.log to Datadog/Logtail | Phase 2 |
| P1 | CC9.2 — DPAs | Execute DPAs with all sub-processors | Pre-launch |
| P2 | CC7.1 — Vulnerability scanning | Enable GitHub Dependabot | This sprint |
| P2 | CC8.1 — Branch protection | Require PR reviews on `main` | This sprint |
