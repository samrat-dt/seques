# Building SOC 2 Controls Into Day One (Not After the First Incident)
*2026-03-08 · tag: decision*

Seques is a tool that helps vendors answer security questionnaires. If we get breached, the irony writes itself. I didn't want to be that founder.

## Context

The standard startup playbook on compliance is: move fast, skip the controls, bolt on security after you have customers. It works until it doesn't — and when it doesn't, you're retrofitting audit trails into a codebase that was never designed to produce them, re-architecting data flows to satisfy a lawyer's GDPR questions, and explaining to your first enterprise customer why their compliance docs transited through a system with no access logging.

The thing that changed my thinking: Seques handles vendor compliance documents. SOC 2 reports. ISO 27001 certifications. Internal security policies. These are exactly the documents a company would not want leaked. Building a security tool with no security posture is not a trade-off — it's a product defect.

## What We Did

Four concrete things went in during Phase 1, before any external user touched the product.

**Audit trail.** Every meaningful event — session creation, document upload, answer generation, export — writes to an append-only `audit.log` file and simultaneously to a Supabase `audit_events` table. The file is SIEM-ready. The Supabase table is queryable via `GET /api/audit/supabase`. This maps to SOC 2 CC7.2 (monitoring of system operations).

**Structured logging.** `backend/observability.py` wraps all application logging in JSON format with timestamps, session IDs, and event types. No free-text log lines that can't be parsed. This matters when you need to reconstruct what happened during an incident.

**Data minimization.** Document content never leaves the backend except to the LLM provider making the inference call. The frontend never receives raw document text. Mixpanel analytics events contain only session IDs and aggregate counts — no document content, no questionnaire text, no answer drafts.

**Security headers.** A custom `SecurityHeadersMiddleware` sets `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, and `Content-Security-Policy` on every response. This hit a Python 3.9 compatibility bug — `MutableHeaders` doesn't support `.pop()`, so we use `try/del` instead. Found it at runtime, fixed in the same session.

## The Gaps We Know About

No auth. Phase 1 has no authentication layer, which means no multi-tenancy, which means this cannot be a production system with multiple customers yet. We know this. It's the first thing Phase 2 adds. The in-memory session store also loses all data on server restart — Supabase persistence is designed and the schema is ready, but not wired up as the primary store yet.

On GDPR: we have no signed Data Processing Agreements with our sub-processors (Groq, Google, Supabase, Mixpanel). This is a pre-launch blocker. The architecture is GDPR-friendly by design — data minimization, no PII in analytics — but architecture alone doesn't satisfy the DPA requirement.

## Trade-offs

Two extra days of engineering in Phase 1. That's the real cost of what's described above. Audit trail, structured logging, data minimization, security headers — none of it is complicated, but all of it takes time that could have gone toward features.

The alternative is retrofitting. I've watched teams spend weeks adding audit logging to a system that was never designed to produce it. You end up with incomplete trails, inconsistent formats, and gaps that auditors notice. Building it in from the start means the schema is coherent, the coverage is complete, and the next engineer who touches this system has a pattern to follow.

## What I'd Do Differently

Sign the DPAs before writing any code that touches external APIs. I treated it as a "later" task and it's now a blocker. Later always costs more than now.

---
*Building Seques in public. Next: the CORS bug that took three server restarts to diagnose.*
