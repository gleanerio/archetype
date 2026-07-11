"""S3-compatible object store writer (MinIO / LocalStack / AWS)."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Protocol
from urllib.parse import quote

from minio import Minio
from minio.error import S3Error

from .config import ObjectStoreConfig
from .extract import dumps_jsonld

logger = logging.getLogger(__name__)


class ObjectWriter(Protocol):
    def put_jsonld(
        self,
        source_name: str,
        page_url: str,
        data: Any,
        *,
        metadata: dict[str, str] | None = None,
    ) -> str: ...


def sha1_key(page_url: str) -> str:
    return hashlib.sha1(page_url.encode("utf-8")).hexdigest()


def object_key(source_name: str, page_url: str) -> str:
    return f"summoned/{source_name}/{sha1_key(page_url)}.json"


def build_minio_client(cfg: ObjectStoreConfig) -> Minio:
    """Create a MinIO client for HTTP or HTTPS endpoints."""
    return Minio(
        cfg.endpoint,
        access_key=cfg.access_key,
        secret_key=cfg.secret_key,
        secure=cfg.ssl,
        region=cfg.region,
    )


@dataclass
class S3Store:
    """Write JSON-LD objects under summoned/<source>/<sha1>.json."""

    client: Minio
    bucket: str
    create_bucket: bool = True

    def ensure_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                if not self.create_bucket:
                    raise RuntimeError(f"Bucket does not exist: {self.bucket}")
                self.client.make_bucket(self.bucket)
                logger.info("Created bucket %s", self.bucket)
        except S3Error as exc:
            raise RuntimeError(f"Object store bucket error for '{self.bucket}': {exc}") from exc

    def put_jsonld(
        self,
        source_name: str,
        page_url: str,
        data: Any,
        *,
        metadata: dict[str, str] | None = None,
    ) -> str:
        key = object_key(source_name, page_url)
        payload = dumps_jsonld(data)
        meta = {
            "source-url": _safe_meta(page_url),
            "source-name": _safe_meta(source_name),
        }
        if metadata:
            meta.update({k: _safe_meta(v) for k, v in metadata.items()})

        self.client.put_object(
            self.bucket,
            key,
            BytesIO(payload),
            length=len(payload),
            content_type="application/ld+json",
            metadata=meta,
        )
        logger.debug("Stored s3://%s/%s (%d bytes)", self.bucket, key, len(payload))
        return key


class DryRunStore:
    """No-op store that only reports keys that would be written."""

    def put_jsonld(
        self,
        source_name: str,
        page_url: str,
        data: Any,
        *,
        metadata: dict[str, str] | None = None,
    ) -> str:
        key = object_key(source_name, page_url)
        logger.info("[dry-run] would store %s from %s", key, page_url)
        return key


def _safe_meta(value: str) -> str:
    """MinIO metadata values should be ASCII-friendly; percent-encode if needed."""
    try:
        value.encode("ascii")
        return value
    except UnicodeEncodeError:
        return quote(value, safe=":/?&=%+~.-_")


def store_from_config(cfg: ObjectStoreConfig, *, dry_run: bool = False) -> ObjectWriter:
    if dry_run:
        return DryRunStore()
    client = build_minio_client(cfg)
    store = S3Store(client=client, bucket=cfg.bucket)
    store.ensure_bucket()
    return store
