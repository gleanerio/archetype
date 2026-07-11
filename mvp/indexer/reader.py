"""Read summoned JSON-LD objects from S3-compatible storage."""

from __future__ import annotations

import logging
from typing import Any, Iterator

from minio import Minio

from .config import ObjectStoreConfig

logger = logging.getLogger(__name__)


def build_minio_client(cfg: ObjectStoreConfig) -> Minio:
    return Minio(
        cfg.endpoint,
        access_key=cfg.access_key,
        secret_key=cfg.secret_key,
        secure=cfg.ssl,
        region=cfg.region,
    )


def source_prefix(source: str) -> str:
    return f"summoned/{source.strip()}/"


def list_jsonld_keys(client: Minio, bucket: str, source: str) -> list[str]:
    prefix = source_prefix(source)
    keys: list[str] = []
    for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
        name = obj.object_name
        if not name or name.endswith("/"):
            continue
        lower = name.lower()
        if lower.endswith(".json") or lower.endswith(".jsonld"):
            keys.append(name)
    keys.sort()
    logger.info("Found %d JSON-LD object(s) under s3://%s/%s", len(keys), bucket, prefix)
    return keys


def normalize_object_metadata(raw: Any) -> dict[str, str]:
    """Normalize MinIO/S3 metadata keys to simple names (e.g. source-url)."""
    if not raw:
        return {}
    out: dict[str, str] = {}
    items = raw.items() if hasattr(raw, "items") else []
    for key, value in items:
        if value is None:
            continue
        k = str(key).lower()
        # Strip common prefixes from HTTPHeaderDict / MinIO
        for prefix in ("x-amz-meta-", "x-amz-", "x-minio-meta-"):
            if k.startswith(prefix):
                k = k[len(prefix) :]
                break
        out[k] = str(value)
    return out


def harvest_url_from_metadata(meta: dict[str, str]) -> str | None:
    """Return harvest page URL stored by summoner, if present."""
    for key in ("source-url", "source_url", "page-url", "page_url"):
        val = meta.get(key)
        if val and val.strip():
            return val.strip()
    return None


def get_object_bytes(client: Minio, bucket: str, key: str) -> bytes:
    response = client.get_object(bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def get_object_with_metadata(
    client: Minio, bucket: str, key: str
) -> tuple[bytes, dict[str, str]]:
    """Fetch object body and normalized user metadata."""
    stat = client.stat_object(bucket, key)
    meta = normalize_object_metadata(stat.metadata)
    body = get_object_bytes(client, bucket, key)
    return body, meta


def iter_jsonld_objects(
    client: Minio,
    bucket: str,
    source: str,
    *,
    limit: int | None = None,
) -> Iterator[tuple[str, bytes, dict[str, str]]]:
    """Yield (key, body, metadata) for each JSON-LD object."""
    keys = list_jsonld_keys(client, bucket, source)
    if limit is not None and limit >= 0:
        keys = keys[:limit]
    for key in keys:
        logger.debug("Fetching s3://%s/%s", bucket, key)
        body, meta = get_object_with_metadata(client, bucket, key)
        yield key, body, meta
