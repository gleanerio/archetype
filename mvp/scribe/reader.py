"""Read summoned JSON-LD objects from S3-compatible storage."""

from __future__ import annotations

import logging
from typing import Iterator

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
    """List object keys under summoned/<source>/ ending in .json."""
    prefix = source_prefix(source)
    keys: list[str] = []
    for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
        name = obj.object_name
        if not name or name.endswith("/"):
            continue
        if name.lower().endswith(".json") or name.lower().endswith(".jsonld"):
            keys.append(name)
    keys.sort()
    logger.info("Found %d JSON-LD object(s) under s3://%s/%s", len(keys), bucket, prefix)
    return keys


def get_object_bytes(client: Minio, bucket: str, key: str) -> bytes:
    response = client.get_object(bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def iter_jsonld_objects(
    client: Minio,
    bucket: str,
    source: str,
    *,
    limit: int | None = None,
) -> Iterator[tuple[str, bytes]]:
    keys = list_jsonld_keys(client, bucket, source)
    if limit is not None and limit >= 0:
        keys = keys[:limit]
    for key in keys:
        logger.debug("Fetching s3://%s/%s", bucket, key)
        yield key, get_object_bytes(client, bucket, key)
