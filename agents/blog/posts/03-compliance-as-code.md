# Compliance as Code: How We Document SOC 2, GDPR, and ISO 27001 for a Day-1 Startup

Most compliance documentation is written by lawyers, for auditors, after the fact.

We wanted to try something different: write it as part of the build, treat it like code, and keep it in the repo.

Here's what we built and why.

## The Problem with Traditional Compliance Docs

Compliance docs have a few failure modes:

**They're in the wrong place.** A Google Doc that lives in a shared folder that only the CEO and the compliance consultant can find isn't helping the engineer who's adding a new data field.

**They're written after the fact.** Most startups write their SOC 2 narrative 3 months before an audit, in a panic. The controls described don't match the system as built.

**They drift.** The doc says "access is reviewed quarterly" but the quarterly review stopped happening in 2023.

## Compliance in the Repo

We keep all compliance documentation in `docs/compliance/`:

```
docs/compliance/
  SOC2_controls.md
  GDPR_controls.md
  ISO27001_controls.md
  data_inventory.md
  privacy_notice.md (pending)
  DPA_checklist.md (pending)
```

Every control maps to three things: **what the requirement says**, **what we've implemented**, and **what the gap is**.

Example from `SOC2_controls.md`:

```
### CC6.1 — Logical Access Controls
Requirement: The entity implements logical access security software,
infrastructure, and architectures to protect against threats from
sources outside its system boundaries.

Implemented:
- CORS restricts origins (dev: wildcard; prod: explicit list)
- Rate limiting middleware (currently disabled, Phase 2)
- All API routes will require auth in Phase 2

Gap: No auth in Phase 1. All endpoints publicly accessible.
Accepted risk: Dev/internal use only until Phase 2.
```

This is honest. It doesn't pretend the gaps don't exist. It documents the accepted risk and the plan to close it.

## The Audit Log as Evidence

Every action in Seques emits an audit event:

```json
{"timestamp": "2026-03-08T14:22:01Z", "event": "processing_completed",
 "session_id": "abc123", "question_count": 47, "provider": "groq",
 "ip": "127.0.0.1", "request_id": "req_8f2a1b"}
```

These are written append-only to `audit.log` and dual-written to Supabase. For a SOC 2 audit, this is evidence of CC7.2 (monitoring) and CC9.2 (incident response capability).

Building the audit trail as part of the product — not as a bolt-on — means it actually captures what the system does, not a sanitized summary.

## Data Inventory First

Before writing any privacy notice, we wrote `data_inventory.md`:

| Data Element | Source | Stored | Retention | GDPR Basis |
|---|---|---|---|---|
| Session ID | Generated | In-memory + Supabase | Session lifetime | Legitimate interest |
| Compliance doc text | User upload | In-memory only | Session lifetime | Contract |
| Questionnaire text | User upload | In-memory only | Session lifetime | Contract |
| IP address | Request | Audit log | 90 days | Legitimate interest |

No PII in the compliance docs or questionnaire text (it's B2B vendor documentation). No PII sent to Mixpanel. The data footprint is deliberately small.

## Why This Approach Works

Keeping compliance docs in the repo means:
- They're versioned — you can see what the controls looked like at any point in time
- They're PR-reviewable — a control change is a code change
- They're honest — gaps are documented, not hidden
- They're findable — engineers see them in the same place they see architecture docs

The auditor gets a Git history. The engineer gets a spec. The CEO gets a dashboard.

Compliance isn't a project you complete. It's a practice you build into how you ship.
