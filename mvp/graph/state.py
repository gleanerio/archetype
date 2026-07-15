"""Shared pipeline state for deterministic and LangGraph runners."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    """JSON-friendly state shared across pipeline nodes."""

    config_path: str
    source: str
    limit: int | None
    dry_run: bool
    rude: bool
    goal: str
    stages_done: list[str]
    errors: list[str]
    preflight: dict[str, Any]
    summon_stats: dict[str, Any]
    scribe_stats: dict[str, Any]
    indexer_stats: dict[str, Any]
    verify_graph_result: dict[str, Any]
    verify_index_result: dict[str, Any]
    artifacts: dict[str, Any]
    # Control: skip stages (set by caller)
    skip_summon: bool
    skip_scribe: bool
    skip_indexer: bool
    skip_verify: bool
    abort: bool


def default_config_path() -> str:
    mvp_dir = Path(__file__).resolve().parent.parent
    candidate = mvp_dir / "mvp_config.yaml"
    if candidate.is_file():
        return str(candidate)
    return "mvp_config.yaml"


def initial_state(
    *,
    source: str = "medin",
    config_path: str | None = None,
    limit: int | None = 5,
    dry_run: bool = True,
    rude: bool = False,
    goal: str = "",
    skip_summon: bool = False,
    skip_scribe: bool = False,
    skip_indexer: bool = False,
    skip_verify: bool = False,
) -> PipelineState:
    """Safe defaults: dry_run=True, small limit, demo source medin."""
    return PipelineState(
        config_path=config_path or default_config_path(),
        source=source,
        limit=limit,
        dry_run=dry_run,
        rude=rude,
        goal=goal,
        stages_done=[],
        errors=[],
        artifacts={},
        skip_summon=skip_summon,
        skip_scribe=skip_scribe,
        skip_indexer=skip_indexer,
        skip_verify=skip_verify,
        abort=False,
    )


def append_error(state: PipelineState, message: str) -> None:
    errors = list(state.get("errors") or [])
    errors.append(message)
    state["errors"] = errors


def mark_stage(state: PipelineState, name: str) -> None:
    done = list(state.get("stages_done") or [])
    if name not in done:
        done.append(name)
    state["stages_done"] = done
