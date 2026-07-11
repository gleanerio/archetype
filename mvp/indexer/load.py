"""Orchestrate S3 read → facade extract → Elasticsearch bulk load."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .config import AppConfig, graph_iri, index_name
from .elasticsearch_client import build_client, bulk_index, replace_index
from .extract import documents_from_jsonld_bytes
from .reader import build_minio_client, harvest_url_from_metadata, iter_jsonld_objects

logger = logging.getLogger(__name__)


@dataclass
class LoadStats:
    source: str
    index: str
    objects_seen: int = 0
    documents: int = 0
    indexed: int = 0
    bulk_errors: int = 0
    dry_run: bool = False
    errors: int = 0
    messages: list[str] = field(default_factory=list)

    def summary(self) -> str:
        state = "dry-run" if self.dry_run else ("indexed" if self.indexed else "not-indexed")
        return (
            f"source={self.source} index={self.index} objects={self.objects_seen} "
            f"documents={self.documents} indexed={self.indexed} "
            f"status={state} errors={self.errors} bulk_errors={self.bulk_errors}"
        )


def run_load(
    cfg: AppConfig,
    source: str,
    *,
    limit: int | None = None,
    dry_run: bool = False,
) -> LoadStats:
    source = source.strip()
    idx = index_name(source, cfg.search.index_prefix)
    g_iri = graph_iri(source)
    stats = LoadStats(source=source, index=idx, dry_run=dry_run)

    s3 = build_minio_client(cfg.objectstore)
    bucket = cfg.objectstore.bucket

    docs: list[dict] = []
    for key, body, meta in iter_jsonld_objects(s3, bucket, source, limit=limit):
        stats.objects_seen += 1
        source_url = harvest_url_from_metadata(meta)
        extracted = documents_from_jsonld_bytes(
            body,
            source=source,
            s3_key=key,
            graph=g_iri,
            source_url=source_url,
        )
        if not extracted:
            stats.errors += 1
            logger.warning("No documents from %s", key)
            continue
        docs.extend(extracted)
        logger.info(
            "Extracted %d document(s) from %s (source_url=%s)",
            len(extracted),
            key,
            source_url or "—",
        )

    stats.documents = len(docs)

    if stats.objects_seen == 0:
        stats.messages.append(f"no objects under summoned/{source}/")
        logger.warning(stats.messages[-1])
        return stats

    if dry_run:
        logger.info(
            "[dry-run] would replace index %s and bulk %d document(s)",
            idx,
            stats.documents,
        )
        for d in docs[:3]:
            logger.info(
                "[dry-run] sample id=%s name=%s type=%s",
                d.get("_id"),
                d.get("name"),
                d.get("type"),
            )
        return stats

    if not docs:
        stats.messages.append("nothing to index after extraction")
        logger.error(stats.messages[-1])
        return stats

    es = build_client(cfg.search.base_endpoint)
    # shallow copy docs so bulk can pop _id without mutating if re-run in process
    payload = [dict(d) for d in docs]
    replace_index(es, idx)
    success, err_count = bulk_index(es, idx, payload)
    stats.indexed = success
    stats.bulk_errors = err_count
    # refresh for immediate searchability in demos
    es.indices.refresh(index=idx)
    logger.info("Indexed %s documents into %s", success, idx)
    return stats
