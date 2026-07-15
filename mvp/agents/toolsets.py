"""LangChain StructuredTools wrapping mvp/tools (and pipeline helpers).

Tool docstrings are the schema the LLM sees — keep them precise.
Defaults (config_path, dry_run, limit) come from ``agents.defaults``.
"""

from __future__ import annotations

import json
from typing import Any

from agents.defaults import get_defaults

# Domain tools
from tools.indexer_tools import build_search_docs, load_elasticsearch
from tools.preflight import list_sources, preflight_services
from tools.scribe_tools import (
    build_prov_preview,
    jsonld_to_nquads_tool,
    list_summoned_objects,
    load_oxigraph,
)
from tools.summoner_tools import (
    extract_jsonld_from_html,
    inspect_sitemap,
    object_key_for_page,
    parse_sitemap_text,
    summon_source,
)
from tools.verify_tools import verify_graph, verify_index


def _as_text(result: Any) -> str:
    """Serialize tool results for chat agents (stable string for LLM)."""
    return json.dumps(result, indent=2, default=str)


def _require_langchain_tool():
    try:
        from langchain_core.tools import tool
    except ImportError as exc:
        raise ImportError(
            "langchain-core is required for agent toolsets. "
            "pip install -r requirements-agents.txt"
        ) from exc
    return tool


def build_all_tools() -> list[Any]:
    """Build all LangChain tools (fresh closures over current defaults)."""
    tool = _require_langchain_tool()

    @tool
    def list_pipeline_sources() -> str:
        """List sources from mvp_config.yaml (name, active, headless, sitemap url)."""
        d = get_defaults()
        return _as_text(list_sources(d.config_path))

    @tool
    def preflight() -> str:
        """Ping object store, Oxigraph, Elasticsearch, and optional Browserless. Read-only."""
        d = get_defaults()
        return _as_text(preflight_services(d.config_path))

    @tool
    def inspect_source_sitemap(source: str = "", sitemap_url: str = "", limit: int = 20) -> str:
        """Fetch a sitemap and return sample page URLs. Provide source name and/or sitemap_url."""
        d = get_defaults()
        return _as_text(
            inspect_sitemap(
                sitemap_url or None,
                config_path=d.config_path,
                source=source or d.source,
                limit=limit,
            )
        )

    @tool
    def extract_jsonld(url: str, body: str, content_type: str = "text/html") -> str:
        """Pure: extract JSON-LD from an HTML or JSON body (no network)."""
        return _as_text(extract_jsonld_from_html(url, body, content_type=content_type))

    @tool
    def parse_sitemap_xml_text(content: str, base_url: str = "") -> str:
        """Pure: parse sitemap XML text and return URLs (no network)."""
        return _as_text(parse_sitemap_text(content, base_url=base_url))

    @tool
    def s3_object_key(source: str, page_url: str) -> str:
        """Pure: compute S3 key and sha1 for a harvest page URL."""
        return _as_text(object_key_for_page(source, page_url))

    @tool
    def run_summon(
        source: str = "",
        limit: int = -1,
        dry_run: bool = True,
        rude: bool = False,
    ) -> str:
        """Harvest sitemap → JSON-LD → S3 for one source. Default dry_run=True (no S3 writes).

        limit=-1 means use agent default limit. Set rude=True only if user allows ignoring robots.txt.
        """
        d = get_defaults()
        lim = d.limit if limit < 0 else limit
        return _as_text(
            summon_source(
                source or d.source,
                config_path=d.config_path,
                limit=lim,
                dry_run=dry_run if dry_run is not None else d.dry_run,
                rude=rude or d.rude,
            )
        )

    @tool
    def list_s3_summoned(source: str = "", limit: int = 50) -> str:
        """List JSON-LD object keys under summoned/<source>/ in the object store."""
        d = get_defaults()
        return _as_text(
            list_summoned_objects(
                source or d.source,
                config_path=d.config_path,
                limit=limit,
            )
        )

    @tool
    def convert_jsonld_to_nquads(body: str, source: str = "example") -> str:
        """Pure: convert JSON-LD text to N-Quads in urn:gleaner:<source>."""
        return _as_text(jsonld_to_nquads_tool(body, source=source))

    @tool
    def preview_prov(
        source: str,
        s3_key: str,
        harvest_url: str = "",
        body: str = "",
    ) -> str:
        """Pure: build PROV-O N-Quads preview for one summoned object."""
        return _as_text(
            build_prov_preview(
                source=source,
                s3_key=s3_key,
                harvest_url=harvest_url or None,
                body=body or None,
            )
        )

    @tool
    def run_scribe(source: str = "", limit: int = -1, dry_run: bool = True) -> str:
        """Load summoned JSON-LD into Oxigraph. Default dry_run=True.

        WARNING: dry_run=False CLEARS data + prov named graphs for the source, then reloads.
        """
        d = get_defaults()
        lim = d.limit if limit < 0 else limit
        return _as_text(
            load_oxigraph(
                source or d.source,
                config_path=d.config_path,
                limit=lim,
                dry_run=dry_run,
            )
        )

    @tool
    def build_es_docs(
        body: str,
        source: str = "example",
        s3_key: str = "summoned/example/sample.json",
        source_url: str = "",
    ) -> str:
        """Pure: build Elasticsearch search-facade documents from JSON-LD text."""
        return _as_text(
            build_search_docs(
                body,
                source=source,
                s3_key=s3_key,
                source_url=source_url or None,
            )
        )

    @tool
    def run_indexer(source: str = "", limit: int = -1, dry_run: bool = True) -> str:
        """Load summoned JSON-LD into Elasticsearch. Default dry_run=True.

        WARNING: dry_run=False replaces the entire per-source index.
        """
        d = get_defaults()
        lim = d.limit if limit < 0 else limit
        return _as_text(
            load_elasticsearch(
                source or d.source,
                config_path=d.config_path,
                limit=lim,
                dry_run=dry_run,
            )
        )

    @tool
    def check_graph(source: str = "") -> str:
        """Read-only: SPARQL COUNT on Oxigraph data + prov named graphs for a source."""
        d = get_defaults()
        return _as_text(verify_graph(source or d.source, config_path=d.config_path))

    @tool
    def check_index(source: str = "") -> str:
        """Read-only: Elasticsearch document count and sample names for gleaner-<source>."""
        d = get_defaults()
        return _as_text(verify_index(source or d.source, config_path=d.config_path))

    @tool
    def run_linear_pipeline(
        source: str = "",
        limit: int = -1,
        dry_run: bool = True,
        skip_summon: bool = False,
        skip_scribe: bool = False,
        skip_indexer: bool = False,
        skip_verify: bool = False,
    ) -> str:
        """Run deterministic pipeline: preflight → summon → scribe∥indexer → verify (no LLM).

        Prefer this for full end-to-end dry-runs. Default dry_run=True and small limit.
        """
        from graph.pipeline import run_pipeline
        from graph.state import initial_state

        d = get_defaults()
        lim = d.limit if limit < 0 else limit
        state = initial_state(
            source=source or d.source,
            config_path=d.config_path,
            limit=lim,
            dry_run=dry_run,
            rude=d.rude,
            skip_summon=skip_summon,
            skip_scribe=skip_scribe,
            skip_indexer=skip_indexer,
            skip_verify=skip_verify,
        )
        result = run_pipeline(state)
        # Shrink message history noise for the LLM
        slim = {
            "source": result.get("source"),
            "dry_run": result.get("dry_run"),
            "limit": result.get("limit"),
            "stages_done": result.get("stages_done"),
            "errors": result.get("errors"),
            "summon_summary": (result.get("summon_stats") or {}).get("summary")
            or (result.get("summon_stats") or {}).get("error"),
            "scribe_summary": (result.get("scribe_stats") or {}).get("summary")
            or (result.get("scribe_stats") or {}).get("error"),
            "indexer_summary": (result.get("indexer_stats") or {}).get("summary")
            or (result.get("indexer_stats") or {}).get("error"),
            "verify_graph": result.get("verify_graph_result"),
            "verify_index": result.get("verify_index_result"),
        }
        return _as_text(slim)

    return [
        list_pipeline_sources,
        preflight,
        inspect_source_sitemap,
        extract_jsonld,
        parse_sitemap_xml_text,
        s3_object_key,
        run_summon,
        list_s3_summoned,
        convert_jsonld_to_nquads,
        preview_prov,
        run_scribe,
        build_es_docs,
        run_indexer,
        check_graph,
        check_index,
        run_linear_pipeline,
    ]


def tools_by_name() -> dict[str, Any]:
    return {t.name: t for t in build_all_tools()}


# Specialist subsets (tool names)
SUMMONER_TOOL_NAMES = frozenset(
    {
        "list_pipeline_sources",
        "preflight",
        "inspect_source_sitemap",
        "extract_jsonld",
        "parse_sitemap_xml_text",
        "s3_object_key",
        "run_summon",
    }
)

SCRIBE_TOOL_NAMES = frozenset(
    {
        "list_s3_summoned",
        "convert_jsonld_to_nquads",
        "preview_prov",
        "run_scribe",
        "check_graph",
        "preflight",
    }
)

INDEXER_TOOL_NAMES = frozenset(
    {
        "list_s3_summoned",
        "build_es_docs",
        "run_indexer",
        "check_index",
        "preflight",
    }
)

DIAGNOSER_TOOL_NAMES = frozenset(
    {
        "list_pipeline_sources",
        "preflight",
        "inspect_source_sitemap",
        "extract_jsonld",
        "parse_sitemap_xml_text",
        "convert_jsonld_to_nquads",
        "build_es_docs",
        "preview_prov",
        "list_s3_summoned",
        "check_graph",
        "check_index",
        "s3_object_key",
    }
)

SUPERVISOR_TOOL_NAMES = frozenset(
    {
        "list_pipeline_sources",
        "preflight",
        "run_linear_pipeline",
        "check_graph",
        "check_index",
        # specialists get handoff tools separately
    }
)


def select_tools(names: frozenset[str] | set[str], all_tools: list[Any] | None = None) -> list[Any]:
    tools = all_tools if all_tools is not None else build_all_tools()
    return [t for t in tools if t.name in names]
