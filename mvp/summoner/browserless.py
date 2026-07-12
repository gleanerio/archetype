"""Browserless REST client: render pages and return full HTML for JSON-LD extract."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

# Resource types to skip when harvesting metadata (speed + lower load).
DEFAULT_REJECT_RESOURCE_TYPES = ["image", "media", "font", "stylesheet"]


class HeadlessRenderer(Protocol):
    def render_html(self, url: str) -> str: ...


class HeadlessError(RuntimeError):
    """Browserless request failed."""


@dataclass
class BrowserlessClient:
    """POST /chromium/content → rendered HTML."""

    base_url: str
    token: str = ""
    timeout_ms: int = 60_000
    concurrent: int = 2
    wait_for_timeout_ms: int | None = 5_000
    wait_for_ldjson: bool = True
    block_assets: bool = True
    user_agent: str | None = None
    client: httpx.Client | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self._owns_client = self.client is None
        if self.client is None:
            # Allow long browser sessions
            timeout = httpx.Timeout(
                max(self.timeout_ms / 1000.0 + 15.0, 45.0),
                connect=15.0,
            )
            self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self._sem = threading.Semaphore(max(1, self.concurrent))

    def close(self) -> None:
        if self._owns_client and self.client is not None:
            self.client.close()

    def __enter__(self) -> BrowserlessClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @property
    def content_url(self) -> str:
        path = f"{self.base_url}/chromium/content"
        if self.token:
            return f"{path}?{urlencode({'token': self.token})}"
        return path

    def render_html(self, url: str) -> str:
        """Navigate to ``url`` in Chromium and return the fully rendered HTML."""
        body: dict = {
            "url": url,
            "gotoOptions": {
                "waitUntil": "networkidle2",
                "timeout": max(1000, self.timeout_ms - 5000),
            },
            "bestAttempt": True,
        }
        if self.wait_for_timeout_ms is not None and self.wait_for_timeout_ms > 0:
            body["waitForTimeout"] = self.wait_for_timeout_ms
        if self.wait_for_ldjson:
            # Prefer waiting for JSON-LD script; bestAttempt continues if missing
            body["waitForSelector"] = {
                "selector": 'script[type="application/ld+json"]',
                "timeout": min(15_000, max(1000, self.timeout_ms // 2)),
            }
        if self.block_assets:
            body["rejectResourceTypes"] = list(DEFAULT_REJECT_RESOURCE_TYPES)
        if self.user_agent:
            body["setExtraHTTPHeaders"] = {"User-Agent": self.user_agent}

        logger.debug("Browserless content render: %s", url)
        with self._sem:
            assert self.client is not None
            try:
                response = self.client.post(
                    self.content_url,
                    json=body,
                    headers={"Content-Type": "application/json", "Cache-Control": "no-cache"},
                )
            except httpx.HTTPError as exc:
                raise HeadlessError(f"Browserless request failed for {url}: {exc}") from exc

        if response.status_code == 401:
            raise HeadlessError(
                "Browserless returned 401 Unauthorized — check summoner.headless_token / BROWSERLESS_TOKEN"
            )
        if response.status_code == 429:
            raise HeadlessError(
                f"Browserless queue full (429) for {url}; lower headless_concurrent or raise CONCURRENT/QUEUED"
            )
        if response.status_code == 503:
            raise HeadlessError(f"Browserless unavailable (503) for {url}")
        if response.status_code >= 400:
            snippet = (response.text or "")[:200]
            raise HeadlessError(
                f"Browserless HTTP {response.status_code} for {url}: {snippet}"
            )

        html = response.text
        if not html or not html.strip():
            raise HeadlessError(f"Browserless returned empty HTML for {url}")
        return html


def browserless_from_config(cfg: object) -> BrowserlessClient | None:
    """Build a client from SummonerConfig-like object, or None if headless URL unset."""
    base = getattr(cfg, "headless", "") or ""
    base = str(base).strip()
    if not base:
        return None
    return BrowserlessClient(
        base_url=base,
        token=str(getattr(cfg, "headless_token", "") or ""),
        timeout_ms=int(getattr(cfg, "headless_timeout_ms", 60_000) or 60_000),
        concurrent=int(getattr(cfg, "headless_concurrent", 2) or 2),
        wait_for_timeout_ms=getattr(cfg, "headless_wait_ms", 5_000),
        wait_for_ldjson=bool(getattr(cfg, "headless_wait_for_ldjson", True)),
        block_assets=bool(getattr(cfg, "headless_block_assets", True)),
        user_agent=str(getattr(cfg, "user_agent", "") or "") or None,
    )
