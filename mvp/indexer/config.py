"""Load mvp_config.yaml for indexer (objectstore + search)."""

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


@dataclass(frozen=True)
class SearchConfig:
    type: str
    endpoint: str
    index_prefix: str = "gleaner"

    @property
    def base_endpoint(self) -> str:
        return self.endpoint.rstrip("/")


@dataclass(frozen=True)
class AppConfig:
    objectstore: ObjectStoreConfig
    search: SearchConfig


def index_name(source: str, prefix: str = "gleaner") -> str:
    """Elasticsearch index name for a source, e.g. gleaner-medin."""
    name = source.strip().lower()
    if not name:
        raise ValueError("source name must be non-empty")
    # ES index names: lowercase, no spaces
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in name)
    return f"{prefix.strip() or 'gleaner'}-{safe}"


def graph_iri(source: str) -> str:
    return f"urn:gleaner:{source.strip()}"


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


def _parse_search(raw: dict[str, Any]) -> SearchConfig:
    search_type = str(_require(raw, "type", "search")).lower()
    endpoint = str(_require(raw, "endpoint", "search")).strip()
    if not endpoint:
        raise ValueError("search.endpoint must be non-empty")
    if search_type != "elasticsearch":
        raise ValueError(
            f"Unsupported search type '{search_type}' (v1 supports elasticsearch only)"
        )
    prefix = str(raw.get("index_prefix", "gleaner") or "gleaner")
    return SearchConfig(type=search_type, endpoint=endpoint, index_prefix=prefix)


def load_config(path: str | Path, sources_path: str | Path | None = None) -> AppConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {config_path}")

    objectstore = _parse_objectstore(_require(data, "objectstore", "config"))
    search = _parse_search(_require(data, "search", "config"))
    return AppConfig(objectstore=objectstore, search=search)
