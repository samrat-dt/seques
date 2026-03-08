# What We Learned Building a Multi-Provider LLM Abstraction

When we started building Seques, we made the obvious mistake: we hardcoded Anthropic everywhere.

`import anthropic`. `client.messages.create()`. Anthropic SDK in `engine.py`, in `parser.py`, in every file that needed to talk to an LLM. Three weeks later, we wanted to test with Groq's free tier before buying credits. The refactor took most of a day.

Here's what we'd do differently from the start.

## The Abstraction

We settled on a single function:

```python
def chat(system: str, user: str, max_tokens: int = 1024, provider: str | None = None) -> str:
```

That's it. Returns a string. All provider-specific code lives inside `llm.py`. The rest of the codebase never imports an AI SDK directly.

The provider is resolved in order:
1. The `provider` argument (passed per-session)
2. The `LLM_PROVIDER` environment variable
3. Default: `anthropic`

## Three Providers, One Interface

```python
PROVIDER_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "groq": "llama-3.3-70b-versatile",
    "google": "gemini-2.0-flash",
}
```

**Anthropic**: Native SDK, `client.messages.create()`. Straightforward.

**Groq**: Uses the OpenAI SDK with `base_url="https://api.groq.com/openai/v1"`. This is the cleanest integration — Groq's API is OpenAI-compatible, so you get streaming, function calling, the whole surface area, for free.

**Google**: `google-generativeai` SDK. The interface is slightly different — `model.generate_content([system_prompt, user_prompt])` — but trivial to wrap.

## What Surprised Us

**Groq is fast.** Embarrassingly fast. For our use case — answering 50 security questions from a document corpus — Groq's llama-3.3-70b returns answers roughly 5× faster than Anthropic's Claude Haiku. For an interactive product where the user is watching a progress bar, this matters.

**Quality differences are real but smaller than expected.** For structured compliance Q&A with evidence in context, all three models perform well. The differences show up on ambiguous questions and edge cases — things like "we don't have a formal process for X, but here's what we do informally." Claude tends to hedge more appropriately.

**Switching mid-product is painful.** We let users select the provider per session. This means the `provider` has to be stored on the session and threaded into every LLM call. If you're starting fresh, design this in from day one.

## The Pattern

If you're building any product that touches an LLM, wrap it on day one:

```python
# Don't do this in your business logic:
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(...)

# Do this instead:
from llm import chat
answer = chat(system=SYSTEM_PROMPT, user=question)
```

The abstraction costs you 30 minutes. The refactor costs you a day.
