# From 120 Seconds to 15: How We Made Security Questionnaires Feel Instant

**Published:** 2026-03-09
**Author:** Seques Team

---

Last week we shipped a change that made our product feel completely different. Processing a 30-question security questionnaire went from ~120 seconds to ~15-20 seconds. That's a 6-8x speedup — and the first answer now appears in about 5 seconds.

Here's what was wrong, how we fixed it, and why it matters.

---

## The Problem: We Were Doing This the Dumb Way

The original engine was straightforward: loop over every question, call the LLM, wait for the response, move to the next question. Classic sequential for-loop.

```python
for question in questions:
    answer = llm.generate(question, context)
    answers.append(answer)
```

For a 30-question questionnaire, that means 30 LLM calls, one after another. Each Groq API call takes roughly 3-4 seconds. Do the math: 30 × 4s = 120 seconds. Every. Single. Time.

Users were staring at a spinner for two minutes. That's not a product — that's a loading screen with branding.

---

## The Insight: LLM Calls Are I/O-Bound

Here's the thing that's obvious in hindsight: LLM API calls are HTTP requests. You send a payload, you wait for the network and the model to respond, you get bytes back. Your Python process is doing essentially nothing while that's happening — it's just waiting on I/O.

This is the textbook case for concurrency. You don't need multiple CPU cores. You don't need async rewrite. You need threads, and Python's `ThreadPoolExecutor` handles this cleanly.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=ANSWER_CONCURRENCY) as executor:
    futures = {executor.submit(generate_answer, q, context): q for q in questions}
    for future in as_completed(futures):
        yield future.result()
```

With `ANSWER_CONCURRENCY=10`, all 30 questions fire off nearly simultaneously. Instead of waiting 120 seconds in series, we're waiting for the slowest of the parallel batch — which lands around 15-20 seconds total. The I/O happens in parallel, not in sequence.

---

## Four Other Things We Fixed Along the Way

**1. Doc context built once, not N times.** Previously, we were re-parsing and re-chunking the vendor's compliance documents for every single question. Now that work happens once per session and gets passed down. For large SOC 2 reports, this alone shaved seconds off.

**2. Dynamic `max_tokens` per answer format.** A yes/no question doesn't need 500 tokens. A policy explanation might need 400. We now set `max_tokens` based on the expected answer format, which makes each LLM call faster and cheaper.

**3. LLM client singletons via `lru_cache`.** We were instantiating a new LLM client object on every request. Now the clients are cached — one instance per provider, reused across all calls.

**4. Exponential backoff on 429 rate limits.** At high concurrency, you will hit rate limits. We added retry logic with jitter so bursts don't cascade into failures.

---

## SSE: The UX Improvement That Makes It Feel Like Magic

Raw throughput is one thing. Perceived speed is another.

We use Server-Sent Events (SSE) to stream answers back to the frontend as they complete. As soon as the first LLM call finishes — usually around 5 seconds in — that answer appears in the UI. Then another. Then another. Users see the questionnaire filling up progressively, answer by answer.

That experience — watching your questionnaire get answered in real time — is a different product than "please wait 2 minutes." The technical improvement is 6-8x. The perceived improvement is much larger than that.

---

## What's Next

This was a Phase 1 performance fix. Phase 2 is where things get more interesting.

We're building RAG (retrieval-augmented generation) so we can handle large compliance document sets without truncating at 8KB. Right now, long SOC 2 reports get cut off — RAG will let us retrieve only the relevant sections per question, improving both speed and answer quality.

We're also adding Supabase-backed auth and session persistence, so questionnaire progress survives a page refresh and teams can collaborate on reviews.

The goal: a tool that handles enterprise-grade questionnaire loads — 100+ questions, multiple compliance frameworks, team review workflows — without breaking a sweat.

---

*Seques is an AI-powered security questionnaire co-pilot. Vendors upload their compliance docs and a prospect's questionnaire. The AI drafts every answer. Teams review, edit, and export. We're in early access — [reach out](https://seques.ai) if you're spending hours filling out security questionnaires manually.*
