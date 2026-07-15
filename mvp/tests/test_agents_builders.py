"""Agent factory construction (no live OpenRouter calls)."""

from __future__ import annotations

import pytest

from agents.defaults import set_defaults
from agents.llm import get_chat_model


def test_build_specialists(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("langgraph")
    pytest.importorskip("langchain_openai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-not-real")
    from agents.builders import build_specialist

    llm = get_chat_model()
    for name in ("summoner", "scribe", "indexer", "diagnoser"):
        agent = build_specialist(name, model=llm)  # type: ignore[arg-type]
        assert agent is not None


def test_build_supervisor(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("langgraph")
    pytest.importorskip("langchain_openai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-not-real")
    from agents.builders import build_supervisor_agent

    set_defaults(source="medin", limit=2, dry_run=True)
    agent = build_supervisor_agent(model=get_chat_model())
    assert agent is not None
    assert hasattr(agent, "invoke")
