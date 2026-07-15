"""Service preflight and source listing tools."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx
import yaml

from summoner.config import load_config as load_summoner_config

from ._util import err_result, ok_result, resolve_config_path


def list_sources(config_path: str | None = None) -> dict[str, Any]:
    """List sources from mvp_config.yaml (active and inactive)."""
    try:
        path = resolve_config_path(config_path)
        cfg = load_summoner_config(path)
        sources = [
            {
                "name": s.name,
                "url": s.url,
                "active": s.active,
                "headless": s.headless,
                "sourcetype": s.sourcetype,
                "propername": s.propername,
            }
            for s in cfg.sources
        ]
        active = [s["name"] for s in sources if s["active"]]
        return ok_result(
            config_path=str(path),
            sources=sources,
            active_names=active,
            count=len(sources),
        )
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc))


def _ping_http(url: str, *, timeout: float = 3.0) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(url)
        return {
            "url": url,
            "reachable": True,
            "status_code": r.status_code,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "url": url,
            "reachable": False,
            "error": str(exc),
        }


def _ping_s3(address: str, port: int, access_key: str, secret_key: str, ssl: bool) -> dict[str, Any]:
    """Fast reachability check — prefer HTTP probe over MinIO client (avoids long retries)."""
    scheme = "https" if ssl else "http"
    endpoint = f"{address}:{port}"
    # S3-compatible stores answer something on /; connection refused → unreachable
    probe = _ping_http(f"{scheme}://{endpoint}/", timeout=2.0)
    if not probe.get("reachable"):
        return {
            "endpoint": endpoint,
            "reachable": False,
            "error": probe.get("error", "unreachable"),
        }
    # Optional: list buckets only when host answers (short path)
    try:
        from minio import Minio
        from urllib3 import Timeout
        from urllib3.util.retry import Retry
        import urllib3

        http = urllib3.PoolManager(
            timeout=Timeout(connect=2.0, read=2.0),
            retries=Retry(total=0, connect=0, read=0, redirect=0),
        )
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=ssl,
            http_client=http,
        )
        buckets = [b.name for b in client.list_buckets()]
        return {
            "endpoint": endpoint,
            "reachable": True,
            "status_code": probe.get("status_code"),
            "buckets": buckets,
        }
    except Exception as exc:  # noqa: BLE001
        # Host up but auth/API failed — still "reachable" for preflight purposes
        return {
            "endpoint": endpoint,
            "reachable": True,
            "status_code": probe.get("status_code"),
            "buckets": None,
            "list_error": str(exc),
        }


def preflight_services(config_path: str | None = None) -> dict[str, Any]:
    """Ping object store, Oxigraph, Elasticsearch, and optional Browserless.

    Read-only checks; does not create resources.
    """
    try:
        path = resolve_config_path(config_path)
        with path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        if not isinstance(raw, dict):
            return err_result("config root must be a mapping")

        services: dict[str, Any] = {}

        os_cfg = raw.get("objectstore") or {}
        if os_cfg:
            services["objectstore"] = _ping_s3(
                str(os_cfg.get("address", "localhost")),
                int(os_cfg.get("port", 4566)),
                str(os_cfg.get("accessKey", "")),
                str(os_cfg.get("secretKey", "")),
                bool(os_cfg.get("ssl", False)),
            )
            services["objectstore"]["bucket"] = os_cfg.get("bucket")

        ts = raw.get("triplestore") or {}
        if ts.get("endpoint"):
            endpoint = str(ts["endpoint"]).rstrip("/")
            # Oxigraph root may 404; query endpoint is more reliable
            services["triplestore"] = _ping_http(f"{endpoint}/query")
            services["triplestore"]["type"] = ts.get("type")
            services["triplestore"]["endpoint"] = endpoint

        search = raw.get("search") or {}
        if search.get("endpoint"):
            ep = str(search["endpoint"]).rstrip("/")
            services["search"] = _ping_http(ep)
            services["search"]["type"] = search.get("type")
            services["search"]["index_prefix"] = search.get("index_prefix", "gleaner")

        summoner = raw.get("summoner") or {}
        headless = str(summoner.get("headless") or "").strip()
        if headless:
            token = str(summoner.get("headless_token") or "")
            parsed = urlparse(headless if "://" in headless else f"http://{headless}")
            base = f"{parsed.scheme}://{parsed.netloc}"
            active_url = f"{base}/active"
            if token:
                active_url = f"{active_url}?token={token}"
            services["browserless"] = _ping_http(active_url)
            services["browserless"]["configured"] = True
        else:
            services["browserless"] = {"configured": False, "reachable": None}

        all_ok = True
        for name, info in services.items():
            if name == "browserless" and not info.get("configured"):
                continue
            if info.get("reachable") is False:
                all_ok = False

        return ok_result(
            config_path=str(path),
            services=services,
            all_required_reachable=all_ok,
        )
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc))
