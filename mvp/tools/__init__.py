"""Thin tool adapters over summoner / scribe / indexer for agent + LangGraph use.

These functions return JSON-serializable dicts and call library APIs (not CLIs).
Core packages are untouched; import tools only from orchestration code.
"""

from .indexer_tools import build_search_docs, load_elasticsearch
from .preflight import list_sources, preflight_services
from .scribe_tools import jsonld_to_nquads_tool, list_summoned_objects, load_oxigraph
from .summoner_tools import extract_jsonld_from_html, inspect_sitemap, summon_source
from .verify_tools import verify_graph, verify_index

__all__ = [
    "list_sources",
    "preflight_services",
    "inspect_sitemap",
    "extract_jsonld_from_html",
    "summon_source",
    "list_summoned_objects",
    "jsonld_to_nquads_tool",
    "load_oxigraph",
    "build_search_docs",
    "load_elasticsearch",
    "verify_graph",
    "verify_index",
]
