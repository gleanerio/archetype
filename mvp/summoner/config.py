"""Load and validate mvp_config.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_USER_AGENT = "gleanerio-mvp-summoner/0.1"
DEFAULT_THREADS = 5
DEFAULT_DELAY_MS = 250
DEFAULT_HEADLESS_TIMEOUT_MS = 60_000
DEFAULT_HEADLESS_CONCURRENT = 2
DEFAULT_HEADLESS_WAIT_MS = 5_000


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
        """Host:port for the MinIO client."""
        return f"{self.address}:{self.port}"

    @property
    def base_url(self) -> str:
        scheme = "https" if self.ssl else "http"
        return f"{scheme}://{self.endpoint}"


@dataclass(frozen=True)
class SummonerConfig:
    """Crawl settings including optional Browserless headless endpoint."""

    headless: str = ""
    headless_token: str = ""
    headless_timeout_ms: int = DEFAULT_HEADLESS_TIMEOUT_MS
    headless_concurrent: int = DEFAULT_HEADLESS_CONCURRENT
    headless_wait_ms: int = DEFAULT_HEADLESS_WAIT_MS
    headless_wait_for_ldjson: bool = True
    headless_block_assets: bool = True
    # hybrid: try static first even when source.headless=true; fall back to Browserless
    headless_hybrid: bool = True
    threads: int = DEFAULT_THREADS
    delay: int = DEFAULT_DELAY_MS  # milliseconds
    user_agent: str = DEFAULT_USER_AGENT

    @property
    def headless_configured(self) -> bool:
        return bool(self.headless and self.headless.strip())


@dataclass(frozen=True)
class SourceConfig:
    name: str
    url: str
    sourcetype: str = "sitemap"
    active: bool = True
    headless: bool = False
    propername: str = ""
    # Extra fields from YAML are ignored at construction time.


@dataclass(frozen=True)
class AppConfig:
    objectstore: ObjectStoreConfig
    summoner: SummonerConfig
    sources: list[SourceConfig] = field(default_factory=list)

    def select_sources(self, name: str | None = None) -> list[SourceConfig]:
        """Return active sources, optionally filtered by name."""
        selected = [s for s in self.sources if s.active]
        if name is not None:
            selected = [s for s in selected if s.name == name]
        return selected


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


def _parse_summoner(raw: dict[str, Any] | None) -> SummonerConfig:
    if not raw:
        return SummonerConfig()
    token = str(raw.get("headless_token", "") or raw.get("headlessToken", "") or "")
    if not token:
        token = os.environ.get("BROWSERLESS_TOKEN", "") or ""
    wait_ms = raw.get("headless_wait_ms", raw.get("headlessWaitMs", DEFAULT_HEADLESS_WAIT_MS))
    return SummonerConfig(
        headless=str(raw.get("headless", "") or ""),
        headless_token=token,
        headless_timeout_ms=int(
            raw.get("headless_timeout_ms", raw.get("headlessTimeoutMs", DEFAULT_HEADLESS_TIMEOUT_MS))
            or DEFAULT_HEADLESS_TIMEOUT_MS
        ),
        headless_concurrent=int(
            raw.get("headless_concurrent", raw.get("headlessConcurrent", DEFAULT_HEADLESS_CONCURRENT))
            or DEFAULT_HEADLESS_CONCURRENT
        ),
        headless_wait_ms=int(wait_ms if wait_ms is not None else DEFAULT_HEADLESS_WAIT_MS),
        headless_wait_for_ldjson=bool(
            raw.get("headless_wait_for_ldjson", raw.get("headlessWaitForLdjson", True))
        ),
        headless_block_assets=bool(
            raw.get("headless_block_assets", raw.get("headlessBlockAssets", True))
        ),
        headless_hybrid=bool(raw.get("headless_hybrid", raw.get("headlessHybrid", True))),
        threads=int(raw.get("threads", DEFAULT_THREADS)),
        delay=int(raw.get("delay", DEFAULT_DELAY_MS) or 0),
        user_agent=str(raw.get("user_agent", DEFAULT_USER_AGENT) or DEFAULT_USER_AGENT),
    )


def _parse_source(raw: dict[str, Any]) -> SourceConfig:
    name = str(_require(raw, "name", "sources[]"))
    url = str(_require(raw, "url", f"sources[{name}]"))
    return SourceConfig(
        name=name,
        url=url,
        sourcetype=str(raw.get("sourcetype", "sitemap") or "sitemap"),
        active=bool(raw.get("active", True)),
        headless=bool(raw.get("headless", False)),
        propername=str(raw.get("propername", "") or ""),
    )


def load_config(path: str | Path) -> AppConfig:
    """Load and validate configuration from a YAML file."""
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {config_path}")

    objectstore = _parse_objectstore(_require(data, "objectstore", "config"))
    summoner = _parse_summoner(data.get("summoner"))
    raw_sources = data.get("sources") or []
    if not isinstance(raw_sources, list):
        raise ValueError("'sources' must be a list")

    sources = [_parse_source(item) for item in raw_sources if isinstance(item, dict)]
    return AppConfig(objectstore=objectstore, summoner=summoner, sources=sources)
