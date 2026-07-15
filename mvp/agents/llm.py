"""LLM provider for MVP agents: OpenRouter (OpenAI-compatible).

Default model: x-ai/grok-4.5 (Grok 4.5 on OpenRouter).

Environment:
  OPENROUTER_API_KEY   required for live calls
  OPENROUTER_MODEL     override model id (default x-ai/grok-4.5)
  OPENROUTER_BASE_URL  default https://openrouter.ai/api/v1
  OPENROUTER_HTTP_REFERER / OPENROUTER_APP_TITLE  optional OpenRouter rankings headers
"""

from __future__ import annotations

import os
from typing import Any

# OpenRouter model slug for Grok 4.5
DEFAULT_MODEL = "x-ai/grok-4.5"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_REFERER = "https://github.com/gleanerio/archetype"
DEFAULT_APP_TITLE = "gleanerio-mvp-agents"


class LLMConfigError(RuntimeError):
    """Raised when the LLM cannot be configured (missing key, bad deps)."""


def get_openrouter_api_key(*, required: bool = True) -> str | None:
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not key and required:
        raise LLMConfigError(
            "OPENROUTER_API_KEY is not set. Export your OpenRouter key, e.g.\n"
            "  export OPENROUTER_API_KEY=sk-or-...\n"
            "Get a key at https://openrouter.ai/keys"
        )
    return key or None


def get_default_model() -> str:
    return (os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL


def get_base_url() -> str:
    return (os.environ.get("OPENROUTER_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def openrouter_headers() -> dict[str, str]:
    return {
        "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER") or DEFAULT_REFERER,
        "X-Title": os.environ.get("OPENROUTER_APP_TITLE") or DEFAULT_APP_TITLE,
    }


def get_chat_model(
    *,
    model: str | None = None,
    temperature: float = 0.1,
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs: Any,
):
    """Return a ChatOpenAI client pointed at OpenRouter.

    Parameters mirror OpenAI-compatible settings; ``model`` defaults to Grok 4.5
    (``x-ai/grok-4.5``) unless ``OPENROUTER_MODEL`` is set.
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise LLMConfigError(
            "langchain-openai is not installed. "
            "pip install -r requirements-agents.txt"
        ) from exc

    key = api_key if api_key is not None else get_openrouter_api_key(required=True)
    return ChatOpenAI(
        model=model or get_default_model(),
        api_key=key,
        base_url=base_url or get_base_url(),
        temperature=temperature,
        default_headers=openrouter_headers(),
        **kwargs,
    )


def describe_llm_config(*, require_key: bool = False) -> dict[str, Any]:
    """Non-secret config snapshot (for diagnostics / CLI)."""
    key = get_openrouter_api_key(required=require_key)
    return {
        "provider": "openrouter",
        "base_url": get_base_url(),
        "model": get_default_model(),
        "api_key_set": bool(key),
        "default_model_constant": DEFAULT_MODEL,
    }
