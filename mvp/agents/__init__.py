"""Agent policy prompts and LangGraph agent factories (OpenRouter / Grok 4.5)."""

from pathlib import Path

from agents.llm import (
    DEFAULT_MODEL,
    LLMConfigError,
    describe_llm_config,
    get_chat_model,
    get_default_model,
)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    """Load an agent system prompt by stem name (e.g. 'summoner', 'supervisor')."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Agent prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def list_prompts() -> list[str]:
    return sorted(p.stem for p in PROMPTS_DIR.glob("*.md"))


__all__ = [
    "PROMPTS_DIR",
    "DEFAULT_MODEL",
    "LLMConfigError",
    "load_prompt",
    "list_prompts",
    "get_chat_model",
    "get_default_model",
    "describe_llm_config",
]
