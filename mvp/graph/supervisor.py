"""Multi-agent supervisor graph entrypoints (LangGraph + OpenRouter)."""

from __future__ import annotations

import logging
from typing import Any

from agents.builders import build_supervisor_agent, invoke_agent, last_message_text
from agents.defaults import AgentDefaults, set_defaults
from agents.llm import describe_llm_config

logger = logging.getLogger(__name__)


def build_supervisor_graph(
    *,
    model: Any | None = None,
    defaults: AgentDefaults | None = None,
) -> Any:
    """Return compiled supervisor agent (ReAct + specialist handoffs)."""
    return build_supervisor_agent(model=model, defaults=defaults)


def run_supervisor(
    goal: str,
    *,
    source: str = "medin",
    config_path: str | None = None,
    limit: int | None = 5,
    dry_run: bool = True,
    rude: bool = False,
    model: Any | None = None,
    recursion_limit: int = 40,
) -> dict[str, Any]:
    """Configure defaults, build supervisor, run one goal, return structured result."""
    set_defaults(
        config_path=config_path,
        source=source,
        limit=limit,
        dry_run=dry_run,
        rude=rude,
    )
    llm_info = describe_llm_config(require_key=False)
    logger.info(
        "supervisor start model=%s source=%s dry_run=%s limit=%s goal=%r",
        llm_info.get("model"),
        source,
        dry_run,
        limit,
        goal[:120],
    )
    agent = build_supervisor_graph(model=model)
    raw = invoke_agent(agent, goal, recursion_limit=recursion_limit)
    text = last_message_text(raw)
    return {
        "ok": True,
        "goal": goal,
        "reply": text,
        "llm": llm_info,
        "defaults": {
            "source": source,
            "limit": limit,
            "dry_run": dry_run,
            "rude": rude,
        },
        "messages": raw.get("messages"),
    }
