"""LLM config tests (no live OpenRouter calls)."""

from __future__ import annotations

import os

import pytest

from agents.llm import (
    DEFAULT_MODEL,
    LLMConfigError,
    describe_llm_config,
    get_chat_model,
    get_default_model,
    get_openrouter_api_key,
)


def test_default_model_is_grok_45() -> None:
    assert DEFAULT_MODEL == "x-ai/grok-4.5"


def test_get_default_model_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    assert get_default_model() == "x-ai/grok-4.5"
    monkeypatch.setenv("OPENROUTER_MODEL", "x-ai/grok-3")
    assert get_default_model() == "x-ai/grok-3"


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(LLMConfigError, match="OPENROUTER_API_KEY"):
        get_openrouter_api_key(required=True)


def test_describe_config_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    info = describe_llm_config(require_key=False)
    assert info["provider"] == "openrouter"
    assert info["model"] == "x-ai/grok-4.5"
    assert info["api_key_set"] is False
    assert "openrouter.ai" in info["base_url"]


def test_get_chat_model_constructs(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("langchain_openai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-not-real")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    llm = get_chat_model()
    # langchain-openai may store model as model or model_name depending on version
    model_id = getattr(llm, "model_name", None) or getattr(llm, "model", None)
    assert model_id == "x-ai/grok-4.5"
    base = getattr(llm, "openai_api_base", None) or getattr(llm, "base_url", None)
    assert base is None or "openrouter.ai" in str(base)
