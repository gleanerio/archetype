"""Linear pipeline: preflight → summon → scribe ∥ indexer → verify.

Works without LangGraph via ``run_pipeline``. If ``langgraph`` is installed,
``build_langgraph_pipeline`` returns a compiled StateGraph with the same nodes.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from tools.indexer_tools import load_elasticsearch
from tools.preflight import preflight_services
from tools.scribe_tools import load_oxigraph
from tools.summoner_tools import summon_source
from tools.verify_tools import verify_graph, verify_index

from .state import PipelineState, initial_state

logger = logging.getLogger(__name__)


def node_preflight(state: PipelineState) -> dict[str, Any]:
    if state.get("abort"):
        return {}
    result = preflight_services(state.get("config_path"))
    updates: dict[str, Any] = {"preflight": result}
    stages = list(state.get("stages_done") or [])
    stages.append("preflight")
    updates["stages_done"] = stages
    if not result.get("ok"):
        updates["errors"] = list(state.get("errors") or []) + [
            f"preflight failed: {result.get('error', result)}"
        ]
        # Do not abort: dry-run pure paths may still work; write paths will fail later
    return updates


def node_summon(state: PipelineState) -> dict[str, Any]:
    if state.get("abort") or state.get("skip_summon"):
        return {}
    result = summon_source(
        state.get("source") or "medin",
        config_path=state.get("config_path"),
        limit=state.get("limit"),
        dry_run=bool(state.get("dry_run", True)),
        rude=bool(state.get("rude", False)),
    )
    updates: dict[str, Any] = {"summon_stats": result}
    stages = list(state.get("stages_done") or [])
    stages.append("summon")
    updates["stages_done"] = stages
    if not result.get("ok"):
        updates["errors"] = list(state.get("errors") or []) + [
            f"summon failed: {result.get('error', result)}"
        ]
        updates["abort"] = True
    return updates


def node_scribe(state: PipelineState) -> dict[str, Any]:
    if state.get("abort") or state.get("skip_scribe"):
        return {}
    result = load_oxigraph(
        state.get("source") or "medin",
        config_path=state.get("config_path"),
        limit=state.get("limit"),
        dry_run=bool(state.get("dry_run", True)),
    )
    updates: dict[str, Any] = {"scribe_stats": result}
    stages = list(state.get("stages_done") or [])
    stages.append("scribe")
    updates["stages_done"] = stages
    if not result.get("ok"):
        updates["errors"] = list(state.get("errors") or []) + [
            f"scribe failed: {result.get('error', result)}"
        ]
    return updates


def node_indexer(state: PipelineState) -> dict[str, Any]:
    if state.get("abort") or state.get("skip_indexer"):
        return {}
    result = load_elasticsearch(
        state.get("source") or "medin",
        config_path=state.get("config_path"),
        limit=state.get("limit"),
        dry_run=bool(state.get("dry_run", True)),
    )
    updates: dict[str, Any] = {"indexer_stats": result}
    stages = list(state.get("stages_done") or [])
    stages.append("indexer")
    updates["stages_done"] = stages
    if not result.get("ok"):
        updates["errors"] = list(state.get("errors") or []) + [
            f"indexer failed: {result.get('error', result)}"
        ]
    return updates


def node_load_parallel(state: PipelineState) -> dict[str, Any]:
    """Run scribe and indexer in parallel (both only need S3)."""
    if state.get("abort"):
        return {}

    do_scribe = not state.get("skip_scribe")
    do_indexer = not state.get("skip_indexer")

    if not do_scribe and not do_indexer:
        return {}

    if do_scribe and do_indexer:
        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_s = pool.submit(node_scribe, state)
            fut_i = pool.submit(node_indexer, state)
            s_up = fut_s.result()
            i_up = fut_i.result()

        stages = list(state.get("stages_done") or [])
        for name in ("scribe", "indexer"):
            if name not in stages:
                stages.append(name)

        errors = list(state.get("errors") or [])
        s_stats = s_up.get("scribe_stats") or {}
        i_stats = i_up.get("indexer_stats") or {}
        if s_stats and not s_stats.get("ok"):
            errors.append(f"scribe failed: {s_stats.get('error', s_stats)}")
        if i_stats and not i_stats.get("ok"):
            errors.append(f"indexer failed: {i_stats.get('error', i_stats)}")

        return {
            "scribe_stats": s_up.get("scribe_stats"),
            "indexer_stats": i_up.get("indexer_stats"),
            "stages_done": stages,
            "errors": errors,
        }

    if do_scribe:
        return node_scribe(state)
    return node_indexer(state)


def node_verify(state: PipelineState) -> dict[str, Any]:
    if state.get("abort") or state.get("skip_verify"):
        return {}
    # Skip live verify on dry_run unless caller wants it — still attempt read-only
    source = state.get("source") or "medin"
    config_path = state.get("config_path")
    g = verify_graph(source, config_path=config_path)
    i = verify_index(source, config_path=config_path)
    stages = list(state.get("stages_done") or [])
    stages.append("verify")
    artifacts = dict(state.get("artifacts") or {})
    artifacts["verify"] = {"graph": g, "index": i}
    return {
        "verify_graph_result": g,
        "verify_index_result": i,
        "stages_done": stages,
        "artifacts": artifacts,
    }


def _merge(state: PipelineState, updates: dict[str, Any]) -> PipelineState:
    merged: PipelineState = dict(state)  # type: ignore[assignment]
    for key, value in updates.items():
        merged[key] = value  # type: ignore[literal-required]
    return merged


def run_pipeline(state: PipelineState | None = None, **kwargs: Any) -> PipelineState:
    """Run the linear pipeline without LangGraph.

    Keyword args are passed to ``initial_state`` when ``state`` is omitted.
    """
    current: PipelineState = state if state is not None else initial_state(**kwargs)
    logger.info(
        "pipeline start source=%s dry_run=%s limit=%s",
        current.get("source"),
        current.get("dry_run"),
        current.get("limit"),
    )
    for node in (node_preflight, node_summon, node_load_parallel, node_verify):
        updates = node(current)
        current = _merge(current, updates)
        if current.get("abort") and node is node_summon:
            # still allow verify of existing data
            if not current.get("skip_verify"):
                current = _merge(current, node_verify(current))
            break
    logger.info("pipeline done stages=%s errors=%s", current.get("stages_done"), current.get("errors"))
    return current


def build_langgraph_pipeline():
    """Compile a LangGraph StateGraph with the same node functions.

    Requires ``langgraph`` (see requirements-agents.txt).
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise ImportError(
            "langgraph is not installed; pip install -r requirements-agents.txt"
        ) from exc

    builder = StateGraph(PipelineState)
    builder.add_node("preflight", node_preflight)
    builder.add_node("summon", node_summon)
    builder.add_node("load", node_load_parallel)
    builder.add_node("verify", node_verify)

    builder.add_edge(START, "preflight")
    builder.add_edge("preflight", "summon")
    builder.add_edge("summon", "load")
    builder.add_edge("load", "verify")
    builder.add_edge("verify", END)

    return builder.compile()


def run_langgraph_pipeline(state: PipelineState | None = None, **kwargs: Any) -> PipelineState:
    """Invoke the LangGraph-compiled pipeline (requires langgraph)."""
    graph = build_langgraph_pipeline()
    current: PipelineState = state if state is not None else initial_state(**kwargs)
    result = graph.invoke(current)
    return result  # type: ignore[return-value]
