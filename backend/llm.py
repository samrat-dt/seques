from __future__ import annotations

import os
import threading
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


# ---------------------------------------------------------------------------
# Groq multi-key rotation with thread-local key assignment
#
# Each worker thread gets its own dedicated Groq key, eliminating key
# collisions between concurrent requests. On 429, the thread rotates to
# its next key rather than the global next key.
#
# Keys: GROQ_API_KEY, GROQ_API_KEY_2 ... GROQ_API_KEY_N (up to 20)
# ---------------------------------------------------------------------------

def _load_groq_keys() -> list[str]:
    keys = []
    for i in range(1, 20):
        name = "GROQ_API_KEY" if i == 1 else f"GROQ_API_KEY_{i}"
        k = os.getenv(name, "").strip()
        if k:
            keys.append(k)
    return keys


@lru_cache(maxsize=None)
def _groq_client_for_key(api_key: str):
    from openai import OpenAI
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=60.0,
        max_retries=0,  # rotation handles retries
    )


# Thread-local key assignment: each thread gets a stable starting key index
_thread_local = threading.local()
_thread_counter = 0
_thread_counter_lock = threading.Lock()


def _get_thread_groq_key() -> str:
    keys = _load_groq_keys()
    if not keys:
        raise ValueError("No GROQ_API_KEY configured.")
    if not hasattr(_thread_local, "key_index"):
        global _thread_counter
        with _thread_counter_lock:
            _thread_local.key_index = _thread_counter % len(keys)
            _thread_counter += 1
    return keys[_thread_local.key_index % len(keys)]


def _rotate_thread_groq_key() -> str:
    """Rotate this thread's key to the next one in the pool."""
    keys = _load_groq_keys()
    current = getattr(_thread_local, "key_index", 0)
    _thread_local.key_index = (current + 1) % len(keys)
    new_key = keys[_thread_local.key_index]
    logger.info("groq_key_rotated", extra={
        "thread_name": threading.current_thread().name,
        "key_index": _thread_local.key_index,
        "total_keys": len(keys),
    })
    return new_key


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
        key = _get_thread_groq_key()
        response = _groq_client_for_key(key).chat.completions.create(
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
    num_keys = len(_load_groq_keys()) if provider == "groq" else 1
    max_attempts = num_keys + 2  # try every key, then 2 backoff attempts

    for attempt in range(max_attempts):
        try:
            return _do_chat(system, user, max_tokens, provider)
        except Exception as e:
            is_rate_limit = (
                "rate_limit" in type(e).__name__.lower()
                or getattr(e, "status_code", None) in (429, 413)
                or "429" in str(e)
                or "413" in str(e)
            )
            if is_rate_limit and attempt < max_attempts - 1:
                if provider == "groq" and num_keys > 1:
                    _rotate_thread_groq_key()
                    logger.warning("groq_key_rotated_on_rate_limit", extra={
                        "attempt": attempt, "thread_name": threading.current_thread().name
                    })
                else:
                    wait = 2 ** min(attempt, 3)
                    logger.warning("rate_limit_backoff", extra={
                        "attempt": attempt, "wait_s": wait, "provider": provider
                    })
                    time.sleep(wait)
                continue
            raise
    raise RuntimeError("All Groq keys rate-limited. Try again shortly.")
