# Why We Built Seques: The Hidden Tax on Every B2B Sale

If you've ever sold software to an enterprise, you know the questionnaire.

It arrives as a 400-row Excel file, usually at the worst possible moment — when the deal is almost closed. The security team on the buyer's side needs to know: Do you encrypt data at rest? What's your incident response SLA? Are you SOC 2 certified?

These are good questions. They protect the buyer. But answering them manually is a brutal process.

## The Problem

At most startups, filling out a security questionnaire looks like this:

1. Someone forwards the Excel to the head of engineering
2. The engineer forwards it to whoever wrote the security policy
3. That person fills in half of it from memory, gets stuck on 30 questions, and emails the compliance folder
4. Three days later, a half-filled spreadsheet goes back to the customer
5. The customer's security team asks follow-up questions
6. Repeat

For a 400-question questionnaire, this can take 8–12 hours of senior engineering and compliance time. For a company fielding 10 of these a quarter, that's a part-time job that doesn't exist yet.

## What We Built

Seques is an AI co-pilot for security questionnaire responses.

You upload your compliance documents — SOC 2 reports, ISO 27001 certificates, internal policies. You paste in the questionnaire. The AI reads your evidence and drafts answers, question by question, citing the source.

You review. You edit. You export.

The average questionnaire that used to take a day now takes an hour.

## Why Now

Three things converged to make this possible:

**1. LLMs are good enough at document Q&A.** Modern models can read a 60-page SOC 2 report and answer "Do you have a formal change management process?" with a specific citation. That wasn't reliable two years ago.

**2. The compliance document stack is standardizing.** Most companies now have a SOC 2 Type II report, an ISO 27001 certificate, or at least a security policy deck. The evidence exists — it just isn't connected to the questions.

**3. Security questionnaires are exploding.** Every enterprise software vendor is now required to complete one. The questionnaire burden on startups has grown faster than teams have.

## What's Next

Phase 1 is the core loop: upload → AI drafts → human reviews → export.

Phase 2 adds a knowledge base — your past answers, deduplicated and indexed. So question 47 of your next questionnaire gets answered instantly because you answered the same question last quarter.

We're building for the security-conscious startup that's serious about compliance but doesn't have a full-time GRC team yet.

If that's you, [join the waitlist](#).
