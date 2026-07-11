"""Orchestrate sitemap walk → extract JSON-LD → object store."""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import httpx

from .config import AppConfig, SourceConfig
from .extract import extract_jsonld
from .robots import RobotsCache
from .sitemap import collect_page_urls
from .store import ObjectWriter, store_from_config

logger = logging.getLogger(__name__)


@dataclass
class SourceStats:
    name: str
    pages_seen: int = 0
    extracted: int = 0
    stored: int = 0
    skipped_robots: int = 0
    skipped_headless: int = 0
    errors: int = 0
    messages: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"source={self.name} pages={self.pages_seen} extracted={self.extracted} "
            f"stored={self.stored} robots_skip={self.skipped_robots} "
            f"headless_skip={self.skipped_headless} errors={self.errors}"
        )


@dataclass
class CrawlResult:
    sources: list[SourceStats] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.sources) and any(s.pages_seen > 0 or s.skipped_headless > 0 for s in self.sources)


class RateLimiter:
    """Simple minimum-interval gate shared across workers for a source."""

    def __init__(self, delay_ms: int) -> None:
        self._delay = max(0, delay_ms) / 1000.0
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        if self._delay <= 0:
            return
        with self._lock:
            now = time.monotonic()
            sleep_for = self._delay - (now - self._last)
            if sleep_for > 0:
                time.sleep(sleep_for)
            self._last = time.monotonic()


def _process_page(
    client: httpx.Client,
    store: ObjectWriter,
    robots: RobotsCache,
    rate: RateLimiter,
    source: SourceConfig,
    page_url: str,
    stats: SourceStats,
    stats_lock: threading.Lock,
) -> None:
    if not robots.allowed(page_url):
        logger.info("Skipped by robots.txt: %s", page_url)
        with stats_lock:
            stats.skipped_robots += 1
        return

    rate.wait()
    try:
        response = client.get(page_url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Fetch failed %s: %s", page_url, exc)
        with stats_lock:
            stats.errors += 1
        return

    content_type = response.headers.get("content-type", "")
    result = extract_jsonld(page_url, response.text, content_type)
    if not result.ok:
        logger.info("No JSON-LD at %s: %s", page_url, result.error)
        with stats_lock:
            stats.errors += 1
        return

    with stats_lock:
        stats.extracted += 1

    try:
        key = store.put_jsonld(source.name, page_url, result.data)
        logger.info("Stored %s ← %s (%s)", key, page_url, result.source)
        with stats_lock:
            stats.stored += 1
    except Exception as exc:  # noqa: BLE001 — keep crawling
        logger.error("Store failed for %s: %s", page_url, exc)
        with stats_lock:
            stats.errors += 1


def crawl_source(
    source: SourceConfig,
    cfg: AppConfig,
    store: ObjectWriter,
    client: httpx.Client,
    robots: RobotsCache,
    *,
    limit: int | None = None,
) -> SourceStats:
    stats = SourceStats(name=source.name)
    stats_lock = threading.Lock()

    if source.headless:
        msg = (
            f"Source '{source.name}' has headless=true; "
            "static-only v1 skips this source (JS-rendered JSON-LD not supported yet)"
        )
        logger.warning(msg)
        stats.skipped_headless += 1
        stats.messages.append(msg)
        return stats

    if source.sourcetype and source.sourcetype.lower() not in ("sitemap", ""):
        msg = f"Source '{source.name}' sourcetype={source.sourcetype!r} not supported (only sitemap)"
        logger.warning(msg)
        stats.errors += 1
        stats.messages.append(msg)
        return stats

    page_urls = collect_page_urls(source.url, client, limit=limit)
    # de-dupe preserving order
    seen: set[str] = set()
    unique_pages: list[str] = []
    for u in page_urls:
        if u not in seen:
            seen.add(u)
            unique_pages.append(u)

    if limit is not None and limit >= 0:
        unique_pages = unique_pages[:limit]

    stats.pages_seen = len(unique_pages)
    logger.info("Source %s: %d page URL(s) to process", source.name, stats.pages_seen)

    if not unique_pages:
        stats.messages.append("no page URLs from sitemap")
        return stats

    rate = RateLimiter(cfg.summoner.delay)
    workers = max(1, cfg.summoner.threads)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(
                _process_page,
                client,
                store,
                robots,
                rate,
                source,
                page_url,
                stats,
                stats_lock,
            )
            for page_url in unique_pages
        ]
        for fut in as_completed(futures):
            exc = fut.exception()
            if exc is not None:
                logger.error("Worker error: %s", exc)
                with stats_lock:
                    stats.errors += 1

    logger.info(stats.summary())
    return stats


def run_crawl(
    cfg: AppConfig,
    *,
    source_name: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    rude: bool = False,
) -> CrawlResult:
    sources = cfg.select_sources(source_name)
    if not sources:
        if source_name:
            raise ValueError(f"No active source named '{source_name}'")
        raise ValueError("No active sources in config")

    store = store_from_config(cfg.objectstore, dry_run=dry_run)
    timeout = httpx.Timeout(30.0, connect=10.0)
    headers = {"User-Agent": cfg.summoner.user_agent}

    result = CrawlResult()
    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
        robots = RobotsCache(client, cfg.summoner.user_agent, rude=rude)
        for source in sources:
            logger.info("=== Summoning source: %s (%s) ===", source.name, source.url)
            stats = crawl_source(
                source,
                cfg,
                store,
                client,
                robots,
                limit=limit,
            )
            result.sources.append(stats)

    return result
