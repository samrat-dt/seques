# Privacy Notice — Seques

**Last updated:** 2026-03-08

---

## 1. Who We Are

Seques ("we", "us", "our") is the data controller for personal data processed through this platform. Seques is a B2B SaaS product that provides an AI-powered security questionnaire co-pilot for business professionals.

Contact: [privacy@seques.ai](mailto:privacy@seques.ai)

---

## 2. What Data We Collect

### 2.1 Data We Process

| Data Type | Description | Retention |
|---|---|---|
| IP Address | Logged as part of the audit trail for security and fraud prevention | 90 days |
| Session ID | A randomly generated identifier for your browser session; not linked to your identity in the current version | Duration of session |
| Usage Events | Anonymous interaction events (e.g., "questionnaire uploaded", "answer generated") sent to analytics | Per sub-processor policy |
| Uploaded Document Text | Text extracted from vendor compliance documents you upload; processed in-memory only and not persisted to disk | Not stored; discarded after processing |

### 2.2 Data We Do Not Collect

- We do not collect names, email addresses, or other personally identifiable information (PII) beyond what is described above.
- We do not use cookies beyond a single session cookie required for platform functionality.
- We do not send marketing emails.
- Uploaded vendor compliance documents are B2B in nature and are not expected to contain personal data. If you believe personal data is present in a document you are uploading, do not upload that document.
- No PII is sent to analytics services (see Section 4 below).

---

## 3. Legal Basis for Processing

We process personal data on the following legal bases under Article 6 of the UK/EU GDPR:

| Processing Activity | Legal Basis |
|---|---|
| IP address logging in audit trail | Legitimate interest (Article 6(1)(f)) — security monitoring, fraud prevention, and audit integrity |
| Session management | Legitimate interest (Article 6(1)(f)) — platform functionality and security |
| Document text processing via LLM | Contract performance (Article 6(1)(b)) — necessary to deliver the questionnaire co-pilot service you have engaged us to provide |

---

## 4. How We Share Your Data

We share data with the following sub-processors to deliver our service:

| Sub-processor | Role | Data Transferred | Location |
|---|---|---|---|
| Supabase | Database and backend infrastructure | IP addresses, session metadata, audit events | EU data residency configurable; default: EU |
| Groq | LLM inference | Uploaded document text (for answer generation) | United States |
| Anthropic | LLM inference | Uploaded document text (for answer generation) | United States |
| Google (Gemini) | LLM inference | Uploaded document text (for answer generation) | United States |
| Mixpanel | Product analytics | Anonymous usage events only; no PII | United States |

For US-based processors, transfers are governed by Standard Contractual Clauses (SCCs) as required by Chapter V of the GDPR.

We do not sell your data. We do not share data with any other third parties except as required by law.

---

## 5. Data Retention

- **IP addresses:** Retained in the audit log for 90 days, then deleted.
- **Session IDs:** Discarded at session end; not persisted.
- **Uploaded document text:** Processed in-memory only; never written to disk or stored in any database. Discarded immediately after the LLM response is returned.
- **Anonymous analytics events:** Retained per Mixpanel's standard data retention policy.

---

## 6. Your Rights

Under the GDPR and applicable data protection law, you have the following rights:

- **Right of access:** You may request a copy of the personal data we hold about you.
- **Right to erasure:** You may request deletion of your personal data where we have no lawful basis to continue processing it.
- **Right to data portability:** You may request your personal data in a structured, machine-readable format.
- **Right to object:** You may object to processing based on legitimate interest.
- **Right to lodge a complaint:** You have the right to lodge a complaint with a supervisory authority. In the EU, this is your national data protection authority. In the UK, this is the Information Commissioner's Office (ICO).

To exercise any of these rights, contact us at [privacy@seques.ai](mailto:privacy@seques.ai). We will respond within 30 days.

---

## 7. Security

We implement appropriate technical and organisational measures to protect personal data, including:

- Audit logging of all API access events
- Rate limiting and security headers on all endpoints
- In-memory-only handling of uploaded document content
- Access control to backend infrastructure via Supabase Row-Level Security (RLS)

---

## 8. Changes to This Notice

We may update this Privacy Notice from time to time. The "Last updated" date at the top of this page reflects the most recent revision. Continued use of the platform after changes are posted constitutes acceptance of those changes.

---

## 9. Contact

For any privacy-related questions or to exercise your rights:

**Email:** [privacy@seques.ai](mailto:privacy@seques.ai)
