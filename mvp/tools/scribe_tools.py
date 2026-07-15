"""Tools wrapping scribe library APIs."""

from __future__ import annotations

from typing import Any

from scribe.config import graph_iri, load_config, prov_graph_iri
from scribe.convert import count_quad_lines, jsonld_to_nquads, jsonld_to_nquads_safe
from scribe.load import run_load
from scribe.prov import build_prov_nquads, collect_entity_ids
from scribe.reader import build_minio_client, list_jsonld_keys

from ._util import err_result, ok_result, resolve_config_path, stats_to_dict


def jsonld_to_nquads_tool(
    body: str,
    source: str = "example",
    *,
    graph: str | None = None,
) -> dict[str, Any]:
    """Pure: convert JSON-LD text to N-Quads in a named graph."""
    g_iri = graph or graph_iri(source)
    nq = jsonld_to_nquads_safe(body, g_iri, key="inline")
    if nq is None:
        return err_result("JSON-LD conversion failed", graph=g_iri)
    lines = count_quad_lines(nq)
    # Cap returned payload for agent contexts
    preview = nq if len(nq) <= 4000 else nq[:4000] + "\n# ... truncated ...\n"
    return ok_result(
        graph=g_iri,
        quad_lines=lines,
        nquads=preview,
        truncated=len(nq) > 4000,
    )


def build_prov_preview(
    *,
    source: str,
    s3_key: str,
    harvest_url: str | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    """Pure: build PROV-O N-Quads preview for one summoned object."""
    g_iri = graph_iri(source)
    p_iri = prov_graph_iri(source)
    entity_ids = collect_entity_ids(body) if body else []
    nq = build_prov_nquads(
        source=source,
        s3_key=s3_key,
        data_graph=g_iri,
        prov_graph=p_iri,
        harvest_url=harvest_url,
        entity_ids=entity_ids,
    )
    return ok_result(
        data_graph=g_iri,
        prov_graph=p_iri,
        entity_ids=entity_ids,
        quad_lines=count_quad_lines(nq),
        nquads=nq,
    )


def list_summoned_objects(
    source: str,
    *,
    config_path: str | None = None,
    limit: int | None = 50,
) -> dict[str, Any]:
    """List S3 keys under summoned/<source>/ (network to object store)."""
    try:
        path = resolve_config_path(config_path)
        cfg = load_config(path)
        client = build_minio_client(cfg.objectstore)
        keys = list_jsonld_keys(client, cfg.objectstore.bucket, source)
        total = len(keys)
        sample = keys[: limit] if limit is not None else keys
        return ok_result(
            source=source,
            bucket=cfg.objectstore.bucket,
            prefix=f"summoned/{source}/",
            total=total,
            keys=sample,
            limited_to=len(sample),
        )
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc), source=source)


def load_oxigraph(
    source: str,
    *,
    config_path: str | None = None,
    limit: int | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Load summoned JSON-LD into Oxigraph. Default dry_run=True (no CLEAR/POST).

    Warning: non-dry_run CLEARs data + prov named graphs for the source, then reloads.
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
                "data_graph": stats.graph,
                "prov_graph": stats.prov_graph,
            },
        )
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc), source=source, dry_run=dry_run)


def convert_jsonld_strict(body: str, graph: str) -> dict[str, Any]:
    """Pure: convert or raise-style error via jsonld_to_nquads (for tests)."""
    try:
        nq = jsonld_to_nquads(body, graph)
        return ok_result(graph=graph, quad_lines=count_quad_lines(nq), nquads=nq)
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc), graph=graph)
