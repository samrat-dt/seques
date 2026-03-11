# v1.0.0-stable: What We Shipped, What We Learned

**2026-03-11**

---

We tagged v1.0.0-stable today. First fully working end-to-end production deployment. Felt worth writing down what actually happened — not the polished version, the real one.

## What Seques Does

You're a security engineer. A prospect sends you a 150-question security questionnaire. You have compliance docs — SOC 2 report, ISO 27001 certificate, a handful of policy Word documents. What follows is usually a week of copy-pasting between PDFs, writing the same answers you wrote last quarter, and hoping you didn't miss a question.

Seques compresses that to under 90 seconds. Upload your docs. Upload their questionnaire. The AI reads the evidence and drafts every answer. You review, edit what needs editing, approve what's good, and export. Done.

The draft quality is high enough that most assertive answers (ones backed by your actual docs) go out with minor edits. Hedged answers — where your docs didn't cover the question — come flagged with a note on exactly what to verify. No blank fields, no "cannot answer" dead ends.

## What We Actually Shipped

The feature list is straightforward: PDF and DOCX ingestion, Excel and PDF questionnaire parsing, Groq and Anthropic LLM support, a review UI with per-answer approve/edit/un-approve, and Excel/PDF export. Sessions persist to Supabase. Security headers and rate limiting are active.

What's less obvious is how much of the work went into making auth and transport work correctly in production.

We built Supabase Magic Link auth. It worked locally. In production it returned "invalid api key" errors we couldn't diagnose quickly. Rather than debug a third-party auth SDK under time pressure, we replaced it with a simple access-code gate — enter the code, it lives in localStorage, every API request carries it as a Bearer token. Trivially overridable per deployment via an env var. It unblocked everything.

The SSE streaming endpoint still exists in the backend. But `EventSource` — the browser API for consuming SSE — cannot send custom request headers. Since our backend requires an Authorization header, the SSE connection returned 401 immediately. There's no workaround within the EventSource spec. So we switched Processing to poll the status endpoint every second. Less elegant, works completely.

Export downloads had the same problem. A plain `<a href>` link causes the browser to make the GET request without any JavaScript involvement — no headers, no auth. 401. Fixed by using `fetch()` with headers, receiving the binary response as a blob, creating an object URL, and triggering a programmatic click. Object URL revoked after use.

## What We Learned

Production is where assumptions break. Three separate systems failed for the same reason: auth headers aren't magic and not every browser API supports them.

The draft-first engine design held up well. The decision to never return "cannot answer" — always produce a professional draft, even if hedged — was the right call. Hedged answers with explicit verification notes are useful. Blanks are not.

Sequential processing (one question at a time) at ANSWER_CONCURRENCY=1 is slower but predictable. A dropped or silently-failed answer in a 30-question session is a worse outcome than waiting 90 seconds. We'll fix the speed problem with proper parallel processing and Redis rate budget tracking in Phase 3.

## What's Next

Phase 3 has a clear priority order. RAG first — the 32KB document limit is the biggest quality ceiling. Most SOC 2 reports are 50-120KB; we're currently ingesting the first 7 or so pages and relying on the model's domain knowledge for the rest. With pgvector we can retrieve only the sections relevant to each question and handle arbitrarily large docs.

Then parallel processing done right, Redis, and multi-user accounts. In that order.

---

The product works. The foundation is honest. On to Phase 3.
