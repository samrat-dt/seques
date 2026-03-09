"""
Tests for backend/llm.py

Covers:
- Provider routing (groq, anthropic, google)
- Missing API key raises ValueError
- Unknown provider raises ValueError
- Response text is stripped of whitespace
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure backend is on the path (conftest.py does this, but be explicit)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import llm  # noqa: E402


# ---------------------------------------------------------------------------
# Groq (OpenAI-compatible) routing
# ---------------------------------------------------------------------------

class TestGroqProvider:
    def test_groq_happy_path(self):
        """chat() returns stripped text from Groq API response."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "  Yes, we use AES-256.  "

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("llm.os.getenv", side_effect=lambda k, d="": "test_key" if k == "GROQ_API_KEY" else d):
            with patch("openai.OpenAI", return_value=mock_client):
                result = llm.chat(system="sys", user="usr", provider="groq")

        assert result == "Yes, we use AES-256."

    def test_groq_missing_api_key(self, monkeypatch):
        """Raises RuntimeError when no Groq keys are available."""
        with patch("llm._available_keys", return_value=[]):
            with pytest.raises(RuntimeError, match="exhausted"):
                llm.chat(system="sys", user="usr", provider="groq")

    def test_groq_uses_correct_model(self):
        """chat() calls Groq with the expected model name."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "answer"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("llm._available_keys", return_value=["test_key"]):
            with patch("llm._groq_client_for_key", return_value=mock_client):
                llm.chat(system="sys", user="usr", provider="groq")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "llama-3.3-70b-versatile"

    def test_groq_passes_system_and_user_messages(self):
        """System and user text are passed in the messages list."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "ok"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("llm._available_keys", return_value=["test_key"]):
            with patch("llm._groq_client_for_key", return_value=mock_client):
                llm.chat(system="my system prompt", user="my user prompt", provider="groq")

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        assert any(m["role"] == "system" and "my system prompt" in m["content"] for m in messages)
        assert any(m["role"] == "user" and "my user prompt" in m["content"] for m in messages)


# ---------------------------------------------------------------------------
# Anthropic routing
# ---------------------------------------------------------------------------

class TestAnthropicProvider:
    def test_anthropic_happy_path(self):
        """chat() returns stripped text from Anthropic API response."""
        mock_content = MagicMock()
        mock_content.text = "  Encrypted at rest.  "

        mock_response = MagicMock()
        mock_response.content = [mock_content]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("llm.os.getenv", side_effect=lambda k, d="": "test_key" if k == "ANTHROPIC_API_KEY" else d):
            with patch("anthropic.Anthropic", return_value=mock_client):
                result = llm.chat(system="sys", user="usr", provider="anthropic")

        assert result == "Encrypted at rest."

    def test_anthropic_missing_api_key(self, monkeypatch):
        """Raises ValueError when ANTHROPIC_API_KEY is not set."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            llm.chat(system="sys", user="usr", provider="anthropic")

    def test_anthropic_uses_correct_model(self):
        """chat() calls Anthropic with the correct model identifier."""
        mock_content = MagicMock()
        mock_content.text = "answer"
        mock_response = MagicMock()
        mock_response.content = [mock_content]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("llm.os.getenv", side_effect=lambda k, d="": "test_key" if "ANTHROPIC" in k else d):
            with patch("llm._anthropic_client", return_value=mock_client):
                llm.chat(system="sys", user="usr", provider="anthropic")

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# Google routing
# ---------------------------------------------------------------------------

class TestGoogleProvider:
    def test_google_happy_path(self):
        """chat() returns stripped text from Google GenerativeAI response."""
        mock_response = MagicMock()
        mock_response.text = "  Yes, SOC 2 certified.  "

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        with patch("llm.os.getenv", side_effect=lambda k, d="": "test_key" if k == "GOOGLE_API_KEY" else d):
            with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
                result = llm.chat(system="sys", user="usr", provider="google")

        assert result == "Yes, SOC 2 certified."

    def test_google_missing_api_key(self, monkeypatch):
        """Raises ValueError when GOOGLE_API_KEY is not set."""
        monkeypatch.setenv("GOOGLE_API_KEY", "")
        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            llm.chat(system="sys", user="usr", provider="google")


# ---------------------------------------------------------------------------
# Unknown provider
# ---------------------------------------------------------------------------

class TestUnknownProvider:
    def test_unknown_provider_raises(self):
        """Raises ValueError for an unrecognised provider string."""
        with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
            llm.chat(system="sys", user="usr", provider="openai_direct")

    def test_unknown_provider_message_contains_provider_name(self):
        """Error message includes the bad provider name."""
        with pytest.raises(ValueError, match="bad_provider"):
            llm.chat(system="sys", user="usr", provider="bad_provider")


# ---------------------------------------------------------------------------
# Provider constants
# ---------------------------------------------------------------------------

class TestProviderConstants:
    def test_provider_models_keys(self):
        assert set(llm.PROVIDER_MODELS.keys()) == {"anthropic", "groq", "google"}

    def test_provider_keys_keys(self):
        assert set(llm.PROVIDER_KEYS.keys()) == {"anthropic", "groq", "google"}

    def test_groq_model_name(self):
        assert llm.PROVIDER_MODELS["groq"] == "llama-3.3-70b-versatile"

    def test_anthropic_model_name(self):
        assert llm.PROVIDER_MODELS["anthropic"] == "claude-haiku-4-5-20251001"

    def test_google_model_name(self):
        assert llm.PROVIDER_MODELS["google"] == "gemini-2.0-flash"
