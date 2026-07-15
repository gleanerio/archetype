"""Tests for pipeline state + pure path (skips network-heavy stages)."""

from __future__ import annotations

from graph.pipeline import _merge, node_verify, run_pipeline
from graph.state import initial_state


def test_initial_state_safe_defaults() -> None:
    s = initial_state()
    assert s["source"] == "medin"
    assert s["dry_run"] is True
    assert s["limit"] == 5
    assert s["rude"] is False
    assert s["stages_done"] == []


def test_merge_updates() -> None:
    s = initial_state(source="x")
    out = _merge(s, {"stages_done": ["preflight"], "abort": False})
    assert out["source"] == "x"
    assert out["stages_done"] == ["preflight"]


def test_run_pipeline_skip_all_network_stages() -> None:
    """With all stages skipped, pipeline only no-ops through nodes."""
    state = initial_state(
        source="medin",
        dry_run=True,
        skip_summon=True,
        skip_scribe=True,
        skip_indexer=True,
        skip_verify=True,
    )
    # Still runs preflight (network ping) — skip by marking abort after empty custom path
    # Instead call run_pipeline with skip verify and mock-free: only preflight hits network.
    # For unit isolation, invoke _merge path with skip all including preflight via direct stages.
    result = run_pipeline(state)
    # preflight always runs; summon/scribe/indexer/verify skipped
    assert "preflight" in (result.get("stages_done") or [])
    assert "summon" not in (result.get("stages_done") or [])
    assert "scribe" not in (result.get("stages_done") or [])
    assert "indexer" not in (result.get("stages_done") or [])
    assert "verify" not in (result.get("stages_done") or [])
    assert result.get("summon_stats") is None or "summon_stats" not in result


def test_node_verify_handles_down_services() -> None:
    """verify tools should not raise if services are down — return structured error/ok."""
    state = initial_state(source="medin", skip_verify=False)
    # Point at unlikely endpoint via env-less config (uses real config if present).
    # Just ensure node_verify returns dict updates without exception.
    updates = node_verify(state)
    assert "stages_done" in updates
    assert "verify" in updates["stages_done"]
    assert "verify_graph_result" in updates
    assert "verify_index_result" in updates
