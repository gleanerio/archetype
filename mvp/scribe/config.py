"""Load mvp_config.yaml for scribe (objectstore + triplestore)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ObjectStoreConfig:
    address: str
    port: int
    access_key: str
    secret_key: str
    ssl: bool
    bucket: str
    region: str = "us-east-1"

    @property
    def endpoint(self) -> str:
        return f"{self.address}:{self.port}"

    @property
    def base_url(self) -> str:
        scheme = "https" if self.ssl else "http"
        return f"{scheme}://{self.endpoint}"


@dataclass(frozen=True)
class TriplestoreConfig:
    type: str
    endpoint: str

    @property
    def base_endpoint(self) -> str:
        return self.endpoint.rstrip("/")


@dataclass(frozen=True)
class AppConfig:
    objectstore: ObjectStoreConfig
    triplestore: TriplestoreConfig


def graph_iri(source: str) -> str:
    """Named graph IRI for a source, e.g. urn:gleaner:medin."""
    name = source.strip()
    if not name:
        raise ValueError("source name must be non-empty")
    return f"urn:gleaner:{name}"


def _require(data: dict[str, Any], key: str, ctx: str) -> Any:
    if key not in data:
        raise ValueError(f"Missing required key '{key}' in {ctx}")
    return data[key]


def _parse_objectstore(raw: dict[str, Any]) -> ObjectStoreConfig:
    return ObjectStoreConfig(
        address=str(_require(raw, "address", "objectstore")),
        port=int(_require(raw, "port", "objectstore")),
        access_key=str(_require(raw, "accessKey", "objectstore")),
        secret_key=str(_require(raw, "secretKey", "objectstore")),
        ssl=bool(raw.get("ssl", False)),
        bucket=str(_require(raw, "bucket", "objectstore")),
        region=str(raw.get("region", "us-east-1")),
    )


def _parse_triplestore(raw: dict[str, Any]) -> TriplestoreConfig:
    store_type = str(_require(raw, "type", "triplestore")).lower()
    endpoint = str(_require(raw, "endpoint", "triplestore")).strip()
    if not endpoint:
        raise ValueError("triplestore.endpoint must be non-empty")
    if store_type != "oxigraph":
        raise ValueError(f"Unsupported triplestore type '{store_type}' (v1 supports oxigraph only)")
    return TriplestoreConfig(type=store_type, endpoint=endpoint)


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {config_path}")

    objectstore = _parse_objectstore(_require(data, "objectstore", "config"))
    triplestore = _parse_triplestore(_require(data, "triplestore", "config"))
    return AppConfig(objectstore=objectstore, triplestore=triplestore)
