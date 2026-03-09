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
# Groq multi-key pool with TPD-aware exhaustion tracking
#
# TPM 429 (tokens per minute) → rotate to next available key, retry now
# TPD 429 (tokens per day)    → permanently blacklist key for this process
#                               lifetime, rotate to next available key
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
        max_retries=0,
    )


@lru_cache(maxsize=1)
def _anthropic_client():
    import anthropic
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# Keys exhausted for the day (TPD) — never retry these until process restart
_exhausted_keys: set[str] = set()
_exhausted_lock = threading.Lock()

# Round-robin index across available keys
_key_index = 0
_key_lock = threading.Lock()


def _available_keys() -> list[str]:
    all_keys = _load_groq_keys()
    with _exhausted_lock:
        return [k for k in all_keys if k not in _exhausted_keys]


def _mark_exhausted(key: str) -> None:
    with _exhausted_lock:
        _exhausted_keys.add(key)
    logger.warning("groq_key_tpd_exhausted", extra={
        "key_suffix": key[-6:],
        "remaining": len(_available_keys()),
    })


def _next_available_key(after_key: str | None = None) -> str | None:
    global _key_index
    keys = _available_keys()
    if not keys:
        return None
    with _key_lock:
        _key_index = (_key_index + 1) % len(keys)
        return keys[_key_index % len(keys)]


def _current_key() -> str | None:
    keys = _available_keys()
    if not keys:
        return None
    with _key_lock:
        return keys[_key_index % len(keys)]


def _is_tpd_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "tokens per day" in msg or "per day" in msg


def _is_tpm_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return ("429" in msg or "rate_limit" in type(exc).__name__.lower() or
            getattr(exc, "status_code", None) == 429) and not _is_tpd_error(exc)


def _is_too_large(exc: Exception) -> bool:
    msg = str(exc)
    return getattr(exc, "status_code", None) == 413 or "413" in msg


def _do_chat(system: str, user: str, max_tokens: int, provider: str, groq_key: str | None = None) -> str:
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
        key = groq_key or _current_key()
        if not key:
            raise RuntimeError("All Groq keys are exhausted for today. Try again tomorrow or add more keys.")
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

    if provider != "groq":
        for attempt in range(3):
            try:
                return _do_chat(system, user, max_tokens, provider)
            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError("Max retries exceeded")

    # Groq: try every available key before giving up
    tried: set[str] = set()
    current_key = _current_key()

    while True:
        if current_key is None:
            raise RuntimeError("All Groq keys are exhausted for today. Try again tomorrow or add more keys.")
        if current_key in tried:
            raise RuntimeError("All Groq keys rate-limited. Try again shortly.")

        tried.add(current_key)
        try:
            return _do_chat(system, user, max_tokens, provider, groq_key=current_key)
        except Exception:
            if _is_tpd_error(e):
                # Daily limit — blacklist this key permanently for today
                _mark_exhausted(current_key)
                current_key = _next_available_key()
            elif _is_tpm_error(e) or _is_too_large(e):
                # Per-minute limit or request too large — rotate and try next key
                logger.warning("groq_tpm_rotate", extra={
                    "key_suffix": current_key[-6:], "error": str(e)[:120]
                })
                current_key = _next_available_key()
                if current_key in tried:
                    # All keys hit TPM, wait a bit then retry the least-used
                    time.sleep(12)
                    tried.clear()
                    current_key = _current_key()
            else:
                raise
