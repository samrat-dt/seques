from __future__ import annotations

import os

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


def chat(system: str, user: str, max_tokens: int = 1024, provider: str | None = None) -> str:
    provider = (provider or os.getenv("LLM_PROVIDER", "anthropic")).lower()

    if provider == "anthropic":
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Set it in backend/.env.")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text.strip()

    elif provider == "groq":
        from openai import OpenAI

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set. Set it in backend/.env.")
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
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

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set. Set it in backend/.env.")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system,
        )
        response = model.generate_content(user)
        return response.text.strip()

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Must be one of: anthropic, groq, google."
        )
