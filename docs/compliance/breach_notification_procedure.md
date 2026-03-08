# Incident Response and Breach Notification Procedure — Seques

**Last updated:** 2026-03-08
**Owner:** Engineering Lead / CEO

---

## 1. Purpose

This document defines Seques' procedure for detecting, containing, assessing, and notifying relevant parties in the event of a personal data breach, in compliance with Article 33 and Article 34 of the GDPR.

A personal data breach includes any accidental or unlawful destruction, loss, alteration, unauthorised disclosure of, or access to, personal data transmitted, stored, or otherwise processed.

---

## 2. Escalation Chain

All incidents follow this escalation path:

```
Detection (any team member)
  → Engineering Lead (technical containment)
    → Legal / DPO (assessment + notification decision)
      → CEO (final sign-off on notification, public statement if needed)
```

Initial escalation must happen within **1 hour** of detection. The 72-hour GDPR clock starts from the moment Seques becomes aware of the breach.

---

## 3. Detection

### 3.1 Detection Sources

- **Audit log anomalies:** Unusual volumes of API requests, repeated failed authentications, unexpected IP addresses in the audit trail, or bulk data access events
- **Supabase alerts:** Database access alerts, RLS policy violations, unexpected query patterns
- **Infrastructure alerts:** Elevated error rates, unexpected service restarts, unauthorized configuration changes
- **External reports:** Third-party disclosure, responsible disclosure submissions to [security@seques.ai](mailto:security@seques.ai)
- **Sub-processor notifications:** Breach notifications from Supabase, Groq, Anthropic, Google, or Mixpanel

### 3.2 Initial Triage

Upon suspecting an incident:

1. Log the date and time you became aware
2. Do not attempt remediation before notifying Engineering Lead
3. Preserve all logs and evidence in their current state
4. Open a private incident channel (e.g., Slack #incident-YYYYMMDD)

---

## 4. Containment

Execute the following containment steps as appropriate to the nature of the incident. Engineering Lead authorizes all containment actions.

### 4.1 Immediate Actions (within 1 hour of detection)

- [ ] **Revoke compromised API keys** — rotate Supabase service role key, Groq API key, Anthropic API key, Google API key, Mixpanel token as applicable
- [ ] **Disable affected endpoints** — comment out or return 503 from affected FastAPI routes if active exploitation is suspected
- [ ] **Block source IPs** — add IP blocks at the infrastructure/firewall level if a specific attacker IP is identified
- [ ] **Suspend affected sessions** — invalidate all active session IDs if session compromise is suspected
- [ ] **Snapshot logs** — export and preserve audit logs from Supabase before any rollback or cleanup

### 4.2 Secondary Containment (within 4 hours)

- [ ] Rotate all secrets in environment variables (`.env`, CI/CD secrets)
- [ ] Re-deploy backend with patched configuration
- [ ] Enable enhanced audit logging (verbose mode) for ongoing monitoring
- [ ] Notify sub-processors if breach originated in or may have propagated to their systems

---

## 5. Assessment

After containment, Engineering Lead and Legal conduct a formal assessment to determine breach scope.

### 5.1 Assessment Questions

1. **What data was affected?**
   - IP addresses (logged in audit trail)
   - Session IDs
   - Uploaded document text (note: in Phase 1 this is in-memory only and not persisted)
   - Anonymous analytics events

2. **Who is affected?**
   - How many data subjects (identified by IP address or session)?
   - Are any affected individuals identifiable from the data exposed?

3. **What was the cause?**
   - Misconfiguration, software vulnerability, insider threat, sub-processor breach, other

4. **What is the severity?**
   - Low: No personal data exposed, or data is effectively anonymous
   - Medium: IP addresses or session IDs exposed with no linkage to identity
   - High: Document content exposed (may contain confidential business data even if not personal data)
   - Critical: PII exposed, or combination of data elements allows re-identification

5. **Is notification required?**
   - GDPR Article 33: Notify supervisory authority unless unlikely to result in risk to individuals
   - GDPR Article 34: Notify data subjects if likely to result in high risk

### 5.2 Assessment Output

Produce a written incident record containing:
- Timeline of events
- Data types affected
- Estimated number of affected individuals
- Risk assessment (low/medium/high/critical)
- Notification decision and rationale

---

## 6. Notification

### 6.1 Supervisory Authority (GDPR Article 33)

**Timeline: within 72 hours of becoming aware of the breach**

If the breach is likely to result in a risk to the rights and freedoms of natural persons, notify the competent supervisory authority. The notification must include:

- Nature of the breach (categories and approximate number of data subjects and records)
- Contact details of the DPO or privacy contact
- Likely consequences of the breach
- Measures taken or proposed to address the breach

**UK:** Information Commissioner's Office (ICO) — [https://ico.org.uk/for-organisations/report-a-breach/](https://ico.org.uk/for-organisations/report-a-breach/)
**EU:** Lead supervisory authority for the EU establishment (to be determined based on Seques legal entity)

If the 72-hour deadline cannot be met, notify with an explanation of the delay.

### 6.2 Affected Data Subjects (GDPR Article 34)

**Timeline: without undue delay**

Notify affected individuals if the breach is likely to result in a high risk to their rights and freedoms. Notification must be in plain language and include:

- What happened
- What personal data was involved
- Likely consequences
- Steps Seques has taken
- What the individual can do to protect themselves
- Contact information for further questions

See Section 7 for the notification email template.

### 6.3 Sub-processors

Notify relevant sub-processors immediately if:
- The breach originated in or may have propagated through their systems
- Data shared with them may have been compromised

---

## 7. Template: Data Subject Notification Email

```
Subject: Important Security Notice — Your Seques Account

Dear [Name / "Seques User"],

We are writing to inform you of a security incident that may have affected
your use of the Seques platform.

What happened:
[Brief, plain-language description of the incident and when it occurred.]

What information was involved:
[List the specific categories of data, e.g., "IP addresses logged during
your sessions between [DATE] and [DATE]."]

What we have done:
[Describe containment measures taken, e.g., "We have rotated all API keys,
invalidated affected sessions, and patched the vulnerability responsible
for this incident."]

What you can do:
[Any practical steps for the individual, e.g., "No action is required on
your part at this time." or "We recommend reviewing any documents you
uploaded during this period."]

If you have questions:
Please contact our privacy team at privacy@seques.ai. We are committed to
responding to all inquiries within 5 business days.

We take the security of your data seriously and sincerely apologise for
any concern or inconvenience this incident may cause.

Seques Team
privacy@seques.ai
```

---

## 8. Post-Incident Review

Within 14 days of resolution, Engineering Lead produces a post-incident review covering:

1. **Root cause analysis** — what went wrong and why
2. **Timeline reconstruction** — detection to resolution
3. **Effectiveness of response** — what worked, what did not
4. **Remediation actions** — specific technical and process changes implemented
5. **Preventive measures** — changes to reduce likelihood of recurrence
6. **Lessons learned** — recommendations for future incident response

The review is shared with the CEO and filed in `docs/compliance/incidents/`.

---

## 9. Record-Keeping

All incidents must be documented regardless of whether notification was required. Seques maintains an internal breach register containing:

- Date of breach (actual or estimated)
- Date Seques became aware
- Nature of the breach
- Data types and volume affected
- Notification decisions and rationale
- Actions taken

This register is available for inspection by supervisory authorities on request.

---

## 10. Testing and Review

This procedure is reviewed annually and after every significant incident. A tabletop exercise simulating a breach scenario should be conducted at least once per year.
