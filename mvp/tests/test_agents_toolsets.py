"""Agent toolset binding tests (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.defaults import set_defaults
from agents.toolsets import (
    SUMMONER_TOOL_NAMES,
    build_all_tools,
    select_tools,
    tools_by_name,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_build_all_tools() -> None:
    pytest.importorskip("langchain_core")
    tools = build_all_tools()
    names = {t.name for t in tools}
    assert "run_summon" in names
    assert "run_scribe" in names
    assert "run_indexer" in names
    assert "run_linear_pipeline" in names
    assert "extract_jsonld" in names


def test_select_summoner_tools() -> None:
    pytest.importorskip("langchain_core")
    tools = select_tools(SUMMONER_TOOL_NAMES)
    names = {t.name for t in tools}
    assert names == set(SUMMONER_TOOL_NAMES)
    assert "run_scribe" not in names


def test_extract_jsonld_tool_invoke() -> None:
    pytest.importorskip("langchain_core")
    by_name = tools_by_name()
    html = (FIXTURES / "page_single.html").read_text(encoding="utf-8")
    out = by_name["extract_jsonld"].invoke(
        {"url": "https://example.org/d", "body": html, "content_type": "text/html"}
    )
    assert "Dataset One" in out
    assert '"ok": true' in out.lower() or '"ok": true' in out


def test_convert_nquads_tool() -> None:
    pytest.importorskip("langchain_core")
    by_name = tools_by_name()
    body = (FIXTURES / "direct.jsonld").read_text(encoding="utf-8")
    out = by_name["convert_jsonld_to_nquads"].invoke({"body": body, "source": "testdemo"})
    assert "urn:gleaner:testdemo" in out
    assert "ok" in out


def test_defaults_injected(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("langchain_core")
    cfg = Path(__file__).resolve().parent.parent / "mvp_config.yaml"
    set_defaults(config_path=str(cfg), source="medin", limit=2, dry_run=True)
    by_name = tools_by_name()
    out = by_name["list_pipeline_sources"].invoke({})
    assert "medin" in out
