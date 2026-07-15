"""Tools wrapping summoner library APIs."""

from __future__ import annotations

import json
from typing import Any

import httpx

from summoner.config import load_config
from summoner.crawl import run_crawl
from summoner.extract import extract_jsonld
from summoner.sitemap import collect_page_urls, parse_sitemap_xml
from summoner.store import object_key, sha1_key

from ._util import err_result, ok_result, resolve_config_path, stats_to_dict


def extract_jsonld_from_html(
    url: str,
    body: str,
    content_type: str = "text/html",
) -> dict[str, Any]:
    """Pure: extract JSON-LD from an HTML or JSON body (no network, no S3)."""
    result = extract_jsonld(url, body, content_type=content_type)
    if not result.ok:
        return err_result(
            result.error or "no JSON-LD found",
            url=url,
            source=result.source,
        )
    # Ensure JSON-serializable
    try:
        data = json.loads(json.dumps(result.data))
    except (TypeError, ValueError):
        data = result.data
    return ok_result(url=url, source=result.source, data=data)


def inspect_sitemap(
    sitemap_url: str | None = None,
    *,
    config_path: str | None = None,
    source: str | None = None,
    limit: int | None = 20,
    user_agent: str = "gleanerio-mvp-tools/0.1",
) -> dict[str, Any]:
    """Fetch a sitemap (or source url from config) and return page URL samples.

    Network read only. ``limit`` caps returned URLs (default 20).
    """
    try:
        if not sitemap_url:
            if not source:
                return err_result("provide sitemap_url or source")
            cfg = load_config(resolve_config_path(config_path))
            selected = cfg.select_sources(source)
            if not selected:
                return err_result(f"no active source named '{source}'")
            sitemap_url = selected[0].url
            user_agent = cfg.summoner.user_agent or user_agent

        assert sitemap_url is not None
        headers = {"User-Agent": user_agent}
        with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
            urls = collect_page_urls(client, sitemap_url)
        total = len(urls)
        sample = urls[: limit] if limit is not None else urls
        return ok_result(
            sitemap_url=sitemap_url,
            total_urls=total,
            sample_urls=sample,
            limited_to=len(sample),
        )
    except Exception as exc:  # noqa: BLE001 — tool boundary
        return err_result(str(exc), sitemap_url=sitemap_url)


def parse_sitemap_text(content: str, base_url: str = "") -> dict[str, Any]:
    """Pure: parse sitemap XML text without network."""
    try:
        kind, urls = parse_sitemap_xml(content, base_url=base_url)
        return ok_result(kind=kind, url_count=len(urls), urls=urls)
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc))


def object_key_for_page(source: str, page_url: str) -> dict[str, Any]:
    """Pure: S3 key + sha1 for a harvest page URL."""
    return ok_result(
        source=source,
        page_url=page_url,
        sha1=sha1_key(page_url),
        s3_key=object_key(source, page_url),
    )


def summon_source(
    source: str,
    *,
    config_path: str | None = None,
    limit: int | None = None,
    dry_run: bool = True,
    rude: bool = False,
) -> dict[str, Any]:
    """Run summoner crawl for one source. Default dry_run=True (no S3 writes)."""
    try:
        path = resolve_config_path(config_path)
        cfg = load_config(path)
        result = run_crawl(
            cfg,
            source_name=source,
            limit=limit,
            dry_run=dry_run,
            rude=rude,
        )
        sources = [stats_to_dict(s) for s in result.sources]
        total_stored = sum(s.get("stored", 0) for s in sources)
        total_extracted = sum(s.get("extracted", 0) for s in sources)
        total_errors = sum(s.get("errors", 0) for s in sources)
        return ok_result(
            config_path=str(path),
            dry_run=dry_run,
            limit=limit,
            rude=rude,
            sources=sources,
            totals={
                "stored": total_stored,
                "extracted": total_extracted,
                "errors": total_errors,
            },
            summary=[s.summary() for s in result.sources],
        )
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc), source=source, dry_run=dry_run)
