# Why I Built a Security Questionnaire Tool
*2026-03-08 · tag: decision*

Every SaaS deal I've watched stall out has had the same culprit: a 200-row security questionnaire sitting in someone's inbox, waiting for a vendor's security team to find three hours they don't have.

## Context

Security questionnaires are one of those problems that everyone in B2B SaaS knows is broken but nobody has fixed properly. A prospect's procurement or InfoSec team sends over a spreadsheet — sometimes an Excel file, sometimes a Google Sheet, occasionally a PDF — with anywhere from 50 to 400 questions about encryption, access controls, incident response, and GDPR. The vendor has to answer every single one before the deal moves forward.

The painful part isn't that the questions are hard. Most vendors have already answered them — in their SOC 2 report, their ISO 27001 certification, their internal security policies, their privacy notices. The answers exist. They're just buried in documents that nobody cross-references against the questionnaire.

So what actually happens? A junior person on the security or compliance team spends two days manually reading through a 60-page SOC 2 report and copy-pasting sentences into a spreadsheet. The same sentences they copy-pasted last quarter for a different customer's questionnaire. It's busywork dressed up as due diligence.

The insight that pushed me to build this: the vendor already has the answers. They're in their compliance docs. The only missing piece is something that can read those docs and the questionnaire simultaneously, match questions to evidence, and draft the answers.

## What We Did

Seques is an AI-powered security questionnaire co-pilot. Vendors upload their compliance docs — SOC 2 reports, ISO 27001 certs, internal policies — and the prospect's questionnaire. The AI reads both, drafts an answer for every question, cites the source document, and gives each answer a confidence score. The human reviews, edits, approves, and exports. That's it.

The workflow respects that humans need to stay in the loop. An AI-drafted answer that gets human approval is defensible. A fully automated response is a liability.

## Trade-offs

I looked at buying rather than building. There are players in this space — Vanta, Secureframe, Drata — but they're primarily compliance automation platforms. The questionnaire response feature is a bolt-on, not the core product, and the pricing reflects that (five-figure annual contracts aimed at companies that already have a compliance program).

Building meant I could focus the entire product on the questionnaire workflow, keep the pricing accessible for mid-market vendors, and own the LLM integration decisions. The downside: I'm building something in a space with well-funded incumbents. The bet is that a focused, affordable tool beats a Swiss Army knife from a compliance platform that treats questionnaire response as a checkbox feature.

## What I'd Do Differently

I'd talk to more sales engineers before writing a line of code. They live inside this problem daily. I talked to three — I should have talked to thirty.

---
*Building Seques in public. Next: why I chose free LLMs over Anthropic to validate before spending.*
