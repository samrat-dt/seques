# Data Processing Agreement (DPA) Checklist — Seques

**Last updated:** 2026-03-08

This checklist tracks the status of Data Processing Agreements with all sub-processors used by Seques. A signed DPA is required with every sub-processor before production launch.

---

## Sub-processor Status

| Sub-processor | Type | Data Transferred | DPA Status | SCCs Required | Action |
|---|---|---|---|---|---|
| Supabase | Sub-processor | IP addresses, session metadata, audit events | Pending signature | No (EU residency) | Sign via Supabase DPA portal |
| Groq | Sub-processor | Uploaded document text (LLM inference) | Pending | Yes (US-based) | Contact Groq legal/sales for DPA |
| Anthropic | Sub-processor | Uploaded document text (LLM inference) | Pending | Yes (US-based) | Contact Anthropic legal for DPA |
| Google (Gemini) | Sub-processor | Uploaded document text (LLM inference) | Pending | Yes (US-based) | Sign via Google Cloud DPA |
| Mixpanel | Sub-processor | Anonymous usage events (no PII) | Pending | Yes (US-based) | Sign via Mixpanel DPA portal |

---

## Standard Contractual Clauses (SCCs)

SCCs are required for all US-based sub-processors under Chapter V GDPR and the EU-US data transfer framework. The applicable module is **Module 2 (Controller to Processor)** or **Module 3 (Processor to Processor)** depending on the processing relationship.

- **Groq:** Module 2 SCCs required
- **Anthropic:** Module 2 SCCs required
- **Google:** Module 2 SCCs required (Google Cloud standard DPA includes SCCs)
- **Mixpanel:** Module 2 SCCs required

---

## Action Items

### Supabase
- [ ] Navigate to: [https://supabase.com/dpa](https://supabase.com/dpa)
- [ ] Complete and sign the DPA for the Seques organization account
- [ ] Confirm EU data residency is selected for the project region
- [ ] File signed copy in `docs/compliance/signed/`

### Groq
- [ ] Contact Groq via their sales/legal portal or email legal@groq.com
- [ ] Request their standard sub-processor DPA
- [ ] Review data retention terms for inference requests (document text)
- [ ] Confirm SCCs are included or attached separately
- [ ] File signed copy in `docs/compliance/signed/`

### Anthropic
- [ ] Navigate to: [https://www.anthropic.com/legal/data-processing](https://www.anthropic.com/legal/data-processing)
- [ ] Review and sign Anthropic's standard DPA
- [ ] Confirm inference data is not used for model training (check API terms)
- [ ] File signed copy in `docs/compliance/signed/`

### Google (Gemini)
- [ ] Navigate to: [https://cloud.google.com/terms/data-processing-addendum](https://cloud.google.com/terms/data-processing-addendum)
- [ ] Accept Google Cloud Data Processing Addendum for the relevant GCP/Gemini project
- [ ] Confirm SCCs are accepted as part of the addendum
- [ ] File signed copy in `docs/compliance/signed/`

### Mixpanel
- [ ] Navigate to: [https://mixpanel.com/legal/dpa/](https://mixpanel.com/legal/dpa/)
- [ ] Complete the Mixpanel DPA request form
- [ ] Verify that only anonymous, non-PII data is sent (confirm in code)
- [ ] File signed copy in `docs/compliance/signed/`

---

## Overall DPA Readiness

- [ ] All DPAs signed
- [ ] All signed copies filed in `docs/compliance/signed/`
- [ ] DPA register updated with effective dates
- [ ] SCCs verified for all US-based processors
- [ ] Privacy notice updated to reflect final sub-processor list
- [ ] Legal review completed before production launch

---

## Notes

- No DPA is required if a processor is not yet in use. Remove from list if decommissioned.
- Review all DPAs annually and upon any material change to processing activities.
- If a sub-processor changes their terms materially, reassess legal basis and update this checklist.
