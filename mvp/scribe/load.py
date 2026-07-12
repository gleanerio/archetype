"""Orchestrate S3 read → N-Quads convert + PROV → Oxigraph load."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

from .config import AppConfig, graph_iri, prov_graph_iri
from .convert import count_quad_lines, jsonld_to_nquads_safe, merge_nquads
from .oxigraph import replace_graphs_with_nquads
from .prov import build_prov_nquads, collect_entity_ids
from .reader import build_minio_client, harvest_url_from_metadata, iter_jsonld_objects

logger = logging.getLogger(__name__)


@dataclass
class LoadStats:
    source: str
    graph: str
    prov_graph: str
    objects_seen: int = 0
    converted: int = 0
    quad_lines: int = 0
    prov_objects: int = 0
    prov_quad_lines: int = 0
    missing_harvest_url: int = 0
    loaded: bool = False
    dry_run: bool = False
    errors: int = 0
    messages: list[str] = field(default_factory=list)

    def summary(self) -> str:
        state = "dry-run" if self.dry_run else ("loaded" if self.loaded else "not-loaded")
        return (
            f"source={self.source} graph={self.graph} prov={self.prov_graph} "
            f"objects={self.objects_seen} converted={self.converted} "
            f"quads={self.quad_lines} prov_objects={self.prov_objects} "
            f"prov_quads={self.prov_quad_lines} missing_source_url={self.missing_harvest_url} "
            f"status={state} errors={self.errors}"
        )


def run_load(
    cfg: AppConfig,
    source: str,
    *,
    limit: int | None = None,
    dry_run: bool = False,
) -> LoadStats:
    source = source.strip()
    g_iri = graph_iri(source)
    p_iri = prov_graph_iri(source)
    stats = LoadStats(source=source, graph=g_iri, prov_graph=p_iri, dry_run=dry_run)

    client = build_minio_client(cfg.objectstore)
    bucket = cfg.objectstore.bucket
    when = datetime.now(timezone.utc)

    data_fragments: list[str] = []
    prov_fragments: list[str] = []

    for key, body, meta in iter_jsonld_objects(client, bucket, source, limit=limit):
        stats.objects_seen += 1
        nq = jsonld_to_nquads_safe(body, g_iri, key=key)
        if nq is None:
            stats.errors += 1
            continue
        lines = count_quad_lines(nq)
        if lines == 0:
            logger.info("No triples from %s", key)
            stats.errors += 1
            continue
        data_fragments.append(nq)
        stats.converted += 1
        stats.quad_lines += lines
        logger.info("Converted %s → %d data quad line(s)", key, lines)

        harvest_url = harvest_url_from_metadata(meta)
        if not harvest_url:
            stats.missing_harvest_url += 1
            logger.info("No source-url metadata for %s", key)

        entity_ids = collect_entity_ids(body)
        prov_nq = build_prov_nquads(
            source=source,
            s3_key=key,
            data_graph=g_iri,
            prov_graph=p_iri,
            harvest_url=harvest_url,
            entity_ids=entity_ids,
            when=when,
        )
        if prov_nq and count_quad_lines(prov_nq) > 0:
            prov_fragments.append(prov_nq)
            stats.prov_objects += 1
            stats.prov_quad_lines += count_quad_lines(prov_nq)

    data_merged = merge_nquads(data_fragments)
    prov_merged = merge_nquads(prov_fragments)
    stats.quad_lines = count_quad_lines(data_merged) if data_merged else 0
    stats.prov_quad_lines = count_quad_lines(prov_merged) if prov_merged else 0
    all_merged = merge_nquads([data_merged, prov_merged])

    if stats.objects_seen == 0:
        stats.messages.append(f"no objects under summoned/{source}/")
        logger.warning(stats.messages[-1])
        return stats

    if dry_run:
        logger.info(
            "[dry-run] would CLEAR <%s> and <%s>, load %d data + %d prov quad line(s) "
            "from %d object(s) (%d missing harvest URL)",
            g_iri,
            p_iri,
            stats.quad_lines,
            stats.prov_quad_lines,
            stats.converted,
            stats.missing_harvest_url,
        )
        return stats

    if not data_merged:
        stats.messages.append("nothing to load after conversion errors")
        logger.error(stats.messages[-1])
        return stats

    with httpx.Client(timeout=120.0) as http:
        replace_graphs_with_nquads(
            cfg.triplestore.base_endpoint,
            [g_iri, p_iri],
            all_merged,
            client=http,
        )
    stats.loaded = True
    logger.info(
        "Loaded data <%s> (%d quads) and prov <%s> (%d quads)",
        g_iri,
        stats.quad_lines,
        p_iri,
        stats.prov_quad_lines,
    )
    return stats
