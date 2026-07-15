"""Tools wrapping indexer library APIs."""

from __future__ import annotations

from typing import Any

from indexer.config import graph_iri, index_name, load_config
from indexer.extract import documents_from_jsonld_bytes
from indexer.load import run_load

from ._util import err_result, ok_result, resolve_config_path, stats_to_dict


def build_search_docs(
    body: str,
    *,
    source: str = "example",
    s3_key: str = "summoned/example/sample.json",
    source_url: str | None = None,
    graph: str | None = None,
) -> dict[str, Any]:
    """Pure: build Elasticsearch document facades from JSON-LD bytes/text."""
    g_iri = graph or graph_iri(source)
    try:
        docs = documents_from_jsonld_bytes(
            body,
            source=source,
            s3_key=s3_key,
            graph=g_iri,
            source_url=source_url,
        )
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc), source=source)

    # Strip bulky jsonld from summary view; keep full in optional field
    facades: list[dict[str, Any]] = []
    for d in docs:
        facades.append(
            {
                "_id": d.get("_id"),
                "name": d.get("name"),
                "type": d.get("type"),
                "url": d.get("url"),
                "source_url": d.get("source_url"),
                "keywords": d.get("keywords"),
                "description": (d.get("description") or "")[:200] or None,
                "s3_key": d.get("s3_key"),
                "graph": d.get("graph"),
                "id": d.get("id"),
            }
        )
    return ok_result(
        source=source,
        graph=g_iri,
        document_count=len(docs),
        documents=facades,
        # full docs for callers that need them (graph may drop this later)
        full_documents=docs,
    )


def load_elasticsearch(
    source: str,
    *,
    config_path: str | None = None,
    limit: int | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Load summoned JSON-LD into Elasticsearch. Default dry_run=True (no index write).

    Warning: non-dry_run replaces the per-source index entirely.
    """
    try:
        path = resolve_config_path(config_path)
        cfg = load_config(path)
        stats = run_load(cfg, source, limit=limit, dry_run=dry_run)
        return ok_result(
            config_path=str(path),
            dry_run=dry_run,
            limit=limit,
            stats=stats_to_dict(stats),
            summary=stats.summary(),
            identity={
                "index": stats.index,
                "graph": graph_iri(source),
                "index_name_helper": index_name(source, cfg.search.index_prefix),
            },
        )
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc), source=source, dry_run=dry_run)
