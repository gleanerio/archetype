"""Orchestrate sitemap walk → extract JSON-LD → object store."""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx

from .browserless import BrowserlessClient, HeadlessError, browserless_from_config
from .config import AppConfig, SourceConfig
from .extract import ExtractResult, extract_jsonld
from .robots import RobotsCache
from .sitemap import collect_page_urls
from .sitegraph import collect_sitegraph_items
from .store import ObjectWriter, store_from_config

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class SourceStats:
    name: str
    pages_seen: int = 0
    extracted: int = 0
    stored: int = 0
    skipped_robots: int = 0
    skipped_headless: int = 0
    headless_ok: int = 0
    headless_errors: int = 0
    static_ok: int = 0
    hybrid_fallback: int = 0
    errors: int = 0
    messages: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"source={self.name} pages={self.pages_seen} extracted={self.extracted} "
            f"stored={self.stored} robots_skip={self.skipped_robots} "
            f"static_ok={self.static_ok} headless_ok={self.headless_ok} "
            f"hybrid_fallback={self.hybrid_fallback} headless_err={self.headless_errors} "
            f"headless_skip={self.skipped_headless} errors={self.errors}"
        )


@dataclass
class CrawlResult:
    sources: list[SourceStats] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.sources) and any(
            s.pages_seen > 0 or s.skipped_headless > 0 for s in self.sources
        )


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


def _static_fetch(
    client: httpx.Client,
    page_url: str,
) -> tuple[str, str] | None:
    """Return (html, content_type) or None on HTTP failure."""
    try:
        response = client.get(page_url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Static fetch failed %s: %s", page_url, exc)
        return None
    return response.text, response.headers.get("content-type", "")


def _fetch_and_extract(
    *,
    page_url: str,
    source: SourceConfig,
    cfg: AppConfig,
    http_client: httpx.Client,
    headless: BrowserlessClient | None,
    stats: SourceStats,
    stats_lock: threading.Lock,
) -> ExtractResult | None:
    """Static and/or headless fetch, then extract JSON-LD.

    Modes when ``source.headless``:
    - hybrid (default): static first; Browserless if no JSON-LD
    - non-hybrid: Browserless only
    When ``source.headless`` is false: static only.
    """
    use_headless = source.headless
    hybrid = cfg.summoner.headless_hybrid

    if use_headless and headless is None:
        # Should have been caught at source start; defensive
        logger.error("Headless required for %s but Browserless not configured", page_url)
        with stats_lock:
            stats.errors += 1
        return None

    # --- Static path ---
    static_result: ExtractResult | None = None
    if not use_headless or hybrid:
        fetched = _static_fetch(http_client, page_url)
        if fetched is not None:
            html, content_type = fetched
            static_result = extract_jsonld(page_url, html, content_type)
            if static_result.ok:
                with stats_lock:
                    stats.static_ok += 1
                return static_result
            logger.debug(
                "Static extract miss %s: %s",
                page_url,
                static_result.error if static_result else "fetch failed",
            )
        elif not use_headless:
            with stats_lock:
                stats.errors += 1
            return None

    # --- Headless path ---
    if use_headless and headless is not None:
        if hybrid and static_result is not None and not static_result.ok:
            with stats_lock:
                stats.hybrid_fallback += 1
            logger.info("Hybrid fallback to Browserless: %s", page_url)
        try:
            html = headless.render_html(page_url)
        except HeadlessError as exc:
            logger.warning("Headless fetch failed %s: %s", page_url, exc)
            with stats_lock:
                stats.headless_errors += 1
                stats.errors += 1
            return None
        result = extract_jsonld(page_url, html, "text/html")
        if result.ok:
            # Mark provenance of extraction path on result
            result = ExtractResult(
                url=result.url,
                data=result.data,
                source=f"headless-{result.source or 'script-tag'}",
                error=None,
            )
            with stats_lock:
                stats.headless_ok += 1
            return result
        logger.info("No JSON-LD after headless render %s: %s", page_url, result.error)
        with stats_lock:
            stats.errors += 1
        return None

    # Static-only miss
    if static_result is not None:
        logger.info("No JSON-LD at %s: %s", page_url, static_result.error)
    with stats_lock:
        stats.errors += 1
    return None


def _process_page(
    http_client: httpx.Client,
    store: ObjectWriter,
    robots: RobotsCache,
    rate: RateLimiter,
    source: SourceConfig,
    cfg: AppConfig,
    page_url: str,
    stats: SourceStats,
    stats_lock: threading.Lock,
    headless: BrowserlessClient | None,
) -> None:
    if not robots.allowed(page_url):
        logger.info("Skipped by robots.txt: %s", page_url)
        with stats_lock:
            stats.skipped_robots += 1
        return

    rate.wait()
    result = _fetch_and_extract(
        page_url=page_url,
        source=source,
        cfg=cfg,
        http_client=http_client,
        headless=headless,
        stats=stats,
        stats_lock=stats_lock,
    )
    if result is None or not result.ok:
        return

    with stats_lock:
        stats.extracted += 1

    try:
        meta = {"fetch-mode": "headless" if (result.source or "").startswith("headless") else "static"}
        key = store.put_jsonld(source.name, page_url, result.data, metadata=meta)
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
    headless: BrowserlessClient | None,
    *,
    limit: int | None = None,
) -> SourceStats:
    stats = SourceStats(name=source.name)
    stats_lock = threading.Lock()

    if source.headless and headless is None:
        msg = (
            f"Source '{source.name}' has headless=true but summoner.headless "
            "Browserless URL is not configured"
        )
        logger.warning(msg)
        stats.skipped_headless += 1
        stats.messages.append(msg)
        return stats

    if source.sourcetype and source.sourcetype.lower() not in ("sitemap", "sitegraph", ""):
        msg = f"Source '{source.name}' sourcetype={source.sourcetype!r} not supported (only sitemap, sitegraph)"
        logger.warning(msg)
        stats.errors += 1
        stats.messages.append(msg)
        return stats

    stype = (source.sourcetype or "sitemap").lower()
    if stype == "sitegraph":
        items = collect_sitegraph_items(source.url, client, limit=limit)
        stats.pages_seen = 1  # The sitegraph file itself
        stats.extracted = len(items)
        for item in items:
            try:
                # For sitegraph, we might not have a distinct page URL per item
                # use @id if present, otherwise fallback to source.url
                item_url = item.get("@id") or source.url
                meta = {"fetch-mode": "sitegraph", "source-url": source.url}
                key = store.put_jsonld(source.name, item_url, item, metadata=meta)
                logger.info("Stored %s (from sitegraph %s)", key, source.url)
                stats.stored += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Store failed for sitegraph item from %s: %s", source.url, exc)
                stats.errors += 1
        logger.info(stats.summary())
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
    mode = "headless" if source.headless else "static"
    if source.headless and cfg.summoner.headless_hybrid:
        mode = "hybrid(static→headless)"
    logger.info(
        "Source %s: %d page URL(s) to process [%s]",
        source.name,
        stats.pages_seen,
        mode,
    )

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
                cfg,
                page_url,
                stats,
                stats_lock,
                headless,
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

    needs_headless = any(s.headless for s in sources)
    headless = browserless_from_config(cfg.summoner) if needs_headless or cfg.summoner.headless_configured else None
    if needs_headless and headless is None:
        logger.warning(
            "One or more sources request headless but summoner.headless is empty; "
            "those sources will be skipped"
        )

    store = store_from_config(cfg.objectstore, dry_run=dry_run)
    timeout = httpx.Timeout(30.0, connect=10.0)
    headers = {"User-Agent": cfg.summoner.user_agent}

    result = CrawlResult()
    try:
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
                    headless,
                    limit=limit,
                )
                result.sources.append(stats)
    finally:
        if headless is not None:
            headless.close()

    return result
