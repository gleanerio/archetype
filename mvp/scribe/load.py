"""Orchestrate S3 read → N-Quads convert → Oxigraph load."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

from .config import AppConfig, graph_iri
from .convert import count_quad_lines, jsonld_to_nquads_safe, merge_nquads
from .oxigraph import replace_graph_with_nquads
from .reader import build_minio_client, iter_jsonld_objects

logger = logging.getLogger(__name__)


@dataclass
class LoadStats:
    source: str
    graph: str
    objects_seen: int = 0
    converted: int = 0
    quad_lines: int = 0
    loaded: bool = False
    dry_run: bool = False
    errors: int = 0
    messages: list[str] = field(default_factory=list)

    def summary(self) -> str:
        state = "dry-run" if self.dry_run else ("loaded" if self.loaded else "not-loaded")
        return (
            f"source={self.source} graph={self.graph} objects={self.objects_seen} "
            f"converted={self.converted} quads={self.quad_lines} "
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
    stats = LoadStats(source=source, graph=g_iri, dry_run=dry_run)

    client = build_minio_client(cfg.objectstore)
    bucket = cfg.objectstore.bucket

    fragments: list[str] = []
    for key, body in iter_jsonld_objects(client, bucket, source, limit=limit):
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
        fragments.append(nq)
        stats.converted += 1
        stats.quad_lines += lines
        logger.info("Converted %s → %d quad line(s)", key, lines)

    merged = merge_nquads(fragments)
    stats.quad_lines = count_quad_lines(merged) if merged else 0

    if stats.objects_seen == 0:
        stats.messages.append(f"no objects under summoned/{source}/")
        logger.warning(stats.messages[-1])
        return stats

    if dry_run:
        logger.info(
            "[dry-run] would CLEAR <%s> and load %d quad line(s) from %d object(s)",
            g_iri,
            stats.quad_lines,
            stats.converted,
        )
        return stats

    if not merged:
        stats.messages.append("nothing to load after conversion errors")
        logger.error(stats.messages[-1])
        return stats

    with httpx.Client(timeout=120.0) as http:
        replace_graph_with_nquads(
            cfg.triplestore.base_endpoint,
            g_iri,
            merged,
            client=http,
        )
    stats.loaded = True
    logger.info("Loaded graph <%s> with %d quad line(s)", g_iri, stats.quad_lines)
    return stats
