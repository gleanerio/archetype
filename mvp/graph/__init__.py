"""Pipeline orchestration (deterministic graph; optional LangGraph multi-agent)."""

from .pipeline import build_langgraph_pipeline, run_pipeline
from .state import PipelineState, initial_state

__all__ = [
    "PipelineState",
    "initial_state",
    "run_pipeline",
    "build_langgraph_pipeline",
]


def build_supervisor_graph(**kwargs):
    """Lazy import so core pipeline works without agent LLM deps at import time."""
    from .supervisor import build_supervisor_graph as _build

    return _build(**kwargs)


def run_supervisor(goal: str, **kwargs):
    from .supervisor import run_supervisor as _run

    return _run(goal, **kwargs)
