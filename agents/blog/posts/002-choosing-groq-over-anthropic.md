# Choosing Free LLMs Over Anthropic to Validate Before Spending
*2026-03-08 · tag: decision*

I built Seques to use Claude. Then I looked at my runway and changed my mind.

## Context

When I started building, the plan was straightforward: use Anthropic's Claude API for everything. Claude is excellent at structured JSON output, which matters when you're asking an LLM to return a confidence score, a cited source, and a drafted answer for each questionnaire row. The quality ceiling is high.

Then I opened a spreadsheet and did the math. A typical security questionnaire has 150–200 questions. Each question needs the model to read several uploaded compliance documents — potentially thousands of tokens of context — and return a structured response. At Anthropic's pricing, a single questionnaire run could cost $2–5 in API credits. That's fine once the product is validated and customers are paying. It's a problem when you're running dozens of test sessions with no revenue to offset it.

The trap I wanted to avoid: spending $300–500 on API credits to test a product that might have the wrong core assumptions, before a single user has confirmed the workflow is actually useful.

## What We Did

I built `backend/llm.py` as a thin multi-provider wrapper from the start. The `chat()` function takes a system prompt and user message, and routes to whichever provider is set via the `LLM_PROVIDER` environment variable. Three providers supported: Groq (default), Google, Anthropic. Switching the entire backend from Groq to Anthropic is one env var change — no code changes required.

```
LLM_PROVIDER=groq    # free, llama-3.3-70b
LLM_PROVIDER=google  # free tier, gemini-2.0-flash
LLM_PROVIDER=anthropic  # paid, claude-3-5-sonnet
```

Groq's free tier gives access to `llama-3.3-70b-versatile` with generous rate limits. Google's free tier gives `gemini-2.0-flash`. Both are capable enough to test whether the core workflow — upload docs, draft answers, review, export — is sound. Neither is as reliable as Claude for structured JSON output, but "reliable enough for validation" is a different bar than "reliable enough for production."

The abstraction also means individual sessions can override the default. If a user hits a question where Groq's output is malformed JSON, we can retry with a different provider without touching the session state.

## Trade-offs

The quality gap is real. Anthropic's Claude produces cleaner structured JSON, hallucinates less when citing source documents, and handles edge cases in questionnaire formatting more gracefully. Groq's LLaMA output occasionally drifts from the expected schema in ways that require defensive parsing on the backend.

What I gained: the ability to run hundreds of test sessions at zero marginal cost while validating that the workflow is worth building. The abstraction means I'm not throwing away any code when I flip to Anthropic — I'm just changing an environment variable.

The trigger for switching back: first paying customer. Once someone has put money down, the economics change. A $2 API cost per questionnaire run is trivially recoverable if the customer is paying $99/month. Until then, Groq and Google carry the validation load.

## What I'd Do Differently

I'd build the multi-provider abstraction even if I planned to only ever use one provider. Vendor lock-in in LLM infrastructure is a real risk — model deprecations, pricing changes, rate limit surprises. The abstraction layer costs one afternoon and pays off every time the LLM landscape shifts.

---
*Building Seques in public. Next: why I built SOC 2 controls into day one instead of waiting until a customer asked for them.*
