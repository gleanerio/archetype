"""Build LangGraph create_react_agent specialists and supervisor.

LLM: OpenRouter, default model x-ai/grok-4.5 (see agents.llm).
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from agents import load_prompt
from agents.defaults import AgentDefaults, get_defaults, set_defaults
from agents.llm import get_chat_model
from agents.toolsets import (
    DIAGNOSER_TOOL_NAMES,
    INDEXER_TOOL_NAMES,
    SCRIBE_TOOL_NAMES,
    SUMMONER_TOOL_NAMES,
    SUPERVISOR_TOOL_NAMES,
    build_all_tools,
    select_tools,
)

logger = logging.getLogger(__name__)

AgentName = Literal["summoner", "scribe", "indexer", "diagnoser", "supervisor"]

SPECIALIST_PROMPTS: dict[str, str] = {
    "summoner": "summoner",
    "scribe": "scribe",
    "indexer": "indexer",
    "diagnoser": "diagnoser",
    "supervisor": "supervisor",
}

SPECIALIST_TOOLS: dict[str, frozenset[str]] = {
    "summoner": SUMMONER_TOOL_NAMES,
    "scribe": SCRIBE_TOOL_NAMES,
    "indexer": INDEXER_TOOL_NAMES,
    "diagnoser": DIAGNOSER_TOOL_NAMES,
}


def _create_agent(model: Any, tools: list[Any], *, prompt: str, name: str) -> Any:
    """Prefer langchain.agents.create_agent; fall back to langgraph create_react_agent."""
    try:
        from langchain.agents import create_agent

        return create_agent(model, tools=tools, system_prompt=prompt, name=name)
    except ImportError:
        pass
    try:
        from langgraph.prebuilt import create_react_agent
    except ImportError as exc:
        raise ImportError(
            "langgraph/langchain agents are required. "
            "pip install -r requirements-agents.txt"
        ) from exc
    return create_react_agent(model, tools=tools, prompt=prompt, name=name)


def _context_preamble(defaults: AgentDefaults | None = None) -> str:
    d = defaults or get_defaults()
    return (
        "\n\n## Runtime context (injected)\n"
        f"- config_path: `{d.config_path}`\n"
        f"- default source: `{d.source}`\n"
        f"- default limit: `{d.limit}`\n"
        f"- default dry_run: `{d.dry_run}`\n"
        f"- rude (ignore robots): `{d.rude}`\n"
        "Prefer these defaults unless the user overrides them.\n"
        "When calling write tools, keep dry_run=true unless the user clearly wants real writes.\n"
    )


def build_specialist(
    name: AgentName,
    *,
    model: Any | None = None,
    defaults: AgentDefaults | None = None,
) -> Any:
    """Build a create_react_agent for one specialist (or a tool-only supervisor shell)."""
    if defaults is not None:
        set_defaults(
            config_path=defaults.config_path,
            source=defaults.source,
            limit=defaults.limit,
            dry_run=defaults.dry_run,
            rude=defaults.rude,
        )

    llm = model or get_chat_model()
    all_tools = build_all_tools()

    if name == "supervisor":
        # Supervisor without handoffs — use build_supervisor_graph for full multi-agent
        prompt = load_prompt("supervisor") + _context_preamble()
        tools = select_tools(SUPERVISOR_TOOL_NAMES, all_tools)
        return _create_agent(llm, tools, prompt=prompt, name="supervisor")

    prompt_name = SPECIALIST_PROMPTS[name]
    prompt = load_prompt(prompt_name) + _context_preamble()
    tools = select_tools(SPECIALIST_TOOLS[name], all_tools)
    logger.info("Built agent %s with %d tools: %s", name, len(tools), [t.name for t in tools])
    return _create_agent(llm, tools, prompt=prompt, name=name)


def last_message_text(result: dict[str, Any]) -> str:
    """Extract the final assistant text from a create_react_agent invoke result."""
    messages = result.get("messages") or []
    if not messages:
        return "(no messages)"
    last = messages[-1]
    content = getattr(last, "content", None)
    if content is None and isinstance(last, dict):
        content = last.get("content")
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return str(content) if content is not None else str(last)


# Back-compat alias
_last_message_text = last_message_text


def build_supervisor_agent(
    *,
    model: Any | None = None,
    defaults: AgentDefaults | None = None,
) -> Any:
    """Supervisor ReAct agent with handoff tools that invoke specialist subgraphs.

    The supervisor can also run the linear pipeline or verify stores directly.
    """
    tool = __import__("langchain_core.tools", fromlist=["tool"]).tool

    if defaults is not None:
        set_defaults(
            config_path=defaults.config_path,
            source=defaults.source,
            limit=defaults.limit,
            dry_run=defaults.dry_run,
            rude=defaults.rude,
        )

    llm = model or get_chat_model()
    # Specialists share the same model by default (routing + capable workers)
    specialists = {
        "summoner": build_specialist("summoner", model=llm),
        "scribe": build_specialist("scribe", model=llm),
        "indexer": build_specialist("indexer", model=llm),
        "diagnoser": build_specialist("diagnoser", model=llm),
    }

    def _make_handoff(agent_name: str, description: str):
        @tool(f"transfer_to_{agent_name}", description=description)
        def handoff(task: str) -> str:
            agent = specialists[agent_name]
            result = agent.invoke({"messages": [{"role": "user", "content": task}]})
            return last_message_text(result)

        return handoff

    handoffs = [
        _make_handoff(
            "summoner",
            "Delegate harvest tasks: sitemap crawl, JSON-LD extract, dry-run summon, headless policy.",
        ),
        _make_handoff(
            "scribe",
            "Delegate graph load tasks: S3→Oxigraph, N-Quads, PROV, verify named graphs.",
        ),
        _make_handoff(
            "indexer",
            "Delegate search load tasks: S3→Elasticsearch, facade docs, verify index.",
        ),
        _make_handoff(
            "diagnoser",
            "Delegate read-only diagnosis: empty stores, HTML JSON-LD checks, convert failures.",
        ),
    ]

    direct = select_tools(SUPERVISOR_TOOL_NAMES, build_all_tools())
    tools = direct + handoffs

    prompt = (
        load_prompt("supervisor")
        + _context_preamble()
        + "\n## Handoffs\n"
        "Use transfer_to_summoner / transfer_to_scribe / transfer_to_indexer / transfer_to_diagnoser "
        "with a clear task string (include source, limit, dry_run intent).\n"
        "Use run_linear_pipeline for a full end-to-end dry-run without micro-managing stages.\n"
        "Use preflight / check_graph / check_index yourself for quick status.\n"
        "When the goal is satisfied, answer the user with a concise summary — do not loop forever.\n"
    )

    return _create_agent(llm, tools, prompt=prompt, name="supervisor")


def invoke_agent(
    agent: Any,
    message: str,
    *,
    recursion_limit: int = 40,
) -> dict[str, Any]:
    """Invoke a compiled react agent with a user message."""
    return agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config={"recursion_limit": recursion_limit},
    )
