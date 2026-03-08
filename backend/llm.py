from __future__ import annotations

import os
import time
from functools import lru_cache

from observability import logger

PROVIDER_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "groq": "llama-3.3-70b-versatile",
    "google": "gemini-2.0-flash",
}

PROVIDER_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
    "google": "GOOGLE_API_KEY",
}


@lru_cache(maxsize=1)
def _groq_client():
    from openai import OpenAI
    return OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        timeout=60.0,
        max_retries=2,
    )


@lru_cache(maxsize=1)
def _anthropic_client():
    import anthropic
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _do_chat(system: str, user: str, max_tokens: int, provider: str) -> str:
    if provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not set.")
        response = _anthropic_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text.strip()

    elif provider == "groq":
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY not set.")
        response = _groq_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content.strip()

    elif provider == "google":
        import google.generativeai as genai
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not set.")
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(model_name="gemini-2.0-flash", system_instruction=system)
        return model.generate_content(user).text.strip()

    else:
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Must be: anthropic, groq, google.")


def chat(system: str, user: str, max_tokens: int = 1024, provider: str | None = None) -> str:
    provider = (provider or os.getenv("LLM_PROVIDER", "anthropic")).lower()
    for attempt in range(3):
        try:
            return _do_chat(system, user, max_tokens, provider)
        except Exception as e:
            is_rate_limit = (
                "rate_limit" in type(e).__name__.lower()
                or getattr(e, "status_code", None) == 429
                or "429" in str(e)
            )
            if is_rate_limit and attempt < 2:
                wait = 2 ** attempt
                logger.warning("rate_limit_backoff", extra={"attempt": attempt, "wait_s": wait, "provider": provider})
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("Max retries exceeded due to rate limiting")
