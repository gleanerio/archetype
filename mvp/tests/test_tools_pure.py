"""Unit tests for pure tools (no S3 / ES / Oxigraph required)."""

from __future__ import annotations

from pathlib import Path

from agents import list_prompts, load_prompt
from tools.indexer_tools import build_search_docs
from tools.preflight import list_sources
from tools.scribe_tools import build_prov_preview, jsonld_to_nquads_tool
from tools.summoner_tools import extract_jsonld_from_html, object_key_for_page, parse_sitemap_text


FIXTURES = Path(__file__).parent / "fixtures"
MVP_CONFIG = Path(__file__).resolve().parent.parent / "mvp_config.yaml"


def test_extract_jsonld_from_html_fixture() -> None:
    html = (FIXTURES / "page_single.html").read_text(encoding="utf-8")
    result = extract_jsonld_from_html("https://example.org/dataset/1", html)
    assert result["ok"] is True
    assert result["data"]["@type"] == "Dataset"
    assert result["data"]["name"] == "Dataset One"


def test_extract_jsonld_multi() -> None:
    html = (FIXTURES / "page_multi.html").read_text(encoding="utf-8")
    result = extract_jsonld_from_html("https://example.org/", html)
    assert result["ok"] is True
    assert isinstance(result["data"], list)
    assert len(result["data"]) == 2


def test_jsonld_to_nquads_tool() -> None:
    body = (FIXTURES / "direct.jsonld").read_text(encoding="utf-8")
    result = jsonld_to_nquads_tool(body, source="testdemo")
    assert result["ok"] is True
    assert result["graph"] == "urn:gleaner:testdemo"
    assert result["quad_lines"] >= 1
    assert "Dataset" in result["nquads"] or "Direct" in result["nquads"]


def test_build_search_docs() -> None:
    body = (FIXTURES / "direct.jsonld").read_text(encoding="utf-8")
    result = build_search_docs(body, source="testdemo", s3_key="summoned/testdemo/abc.json")
    assert result["ok"] is True
    assert result["document_count"] == 1
    doc = result["documents"][0]
    assert doc["name"] == "Direct JSON-LD"
    assert doc["s3_key"] == "summoned/testdemo/abc.json"
    assert "Dataset" in (doc.get("type") or [])


def test_build_prov_preview() -> None:
    body = (FIXTURES / "direct.jsonld").read_text(encoding="utf-8")
    result = build_prov_preview(
        source="testdemo",
        s3_key="summoned/testdemo/deadbeef.json",
        harvest_url="https://example.org/page",
        body=body,
    )
    assert result["ok"] is True
    assert result["prov_graph"] == "urn:gleaner:prov:testdemo"
    assert result["quad_lines"] >= 1
    assert "https://example.org/jsonld/3.json" in result.get("entity_ids", [])


def test_object_key_for_page() -> None:
    result = object_key_for_page("medin", "https://example.org/a")
    assert result["ok"] is True
    assert result["s3_key"].startswith("summoned/medin/")
    assert result["s3_key"].endswith(".json")
    assert len(result["sha1"]) == 40


def test_parse_sitemap_text() -> None:
    xml = (FIXTURES / "urlset.xml").read_text(encoding="utf-8")
    result = parse_sitemap_text(xml, base_url="https://example.org/")
    assert result["ok"] is True
    assert result["url_count"] >= 1


def test_list_sources_config() -> None:
    if not MVP_CONFIG.is_file():
        return
    result = list_sources(str(MVP_CONFIG))
    assert result["ok"] is True
    assert result["count"] >= 1
    assert "medin" in result["active_names"]


def test_agent_prompts_loadable() -> None:
    names = list_prompts()
    assert "supervisor" in names
    assert "summoner" in names
    assert "scribe" in names
    assert "indexer" in names
    assert "diagnoser" in names
    text = load_prompt("supervisor")
    assert "dry_run" in text or "dry-run" in text.lower() or "dry_run" in text
