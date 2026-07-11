"""Robots.txt helpers with per-netloc caching."""

from __future__ import annotations

import logging
import threading
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)


class RobotsCache:
    """Thread-safe robots.txt cache."""

    def __init__(self, client: httpx.Client, user_agent: str, *, rude: bool = False) -> None:
        self._client = client
        self._user_agent = user_agent
        self._rude = rude
        self._parsers: dict[str, RobotFileParser | None] = {}
        self._lock = threading.Lock()

    def allowed(self, url: str) -> bool:
        if self._rude:
            return True

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return True

        netloc_key = f"{parsed.scheme}://{parsed.netloc}".lower()
        rp = self._get_parser(netloc_key, parsed.scheme, parsed.netloc)
        if rp is None:
            # If robots.txt missing/unreadable, allow (common crawler default)
            return True
        return rp.can_fetch(self._user_agent, url)

    def _get_parser(self, key: str, scheme: str, netloc: str) -> RobotFileParser | None:
        with self._lock:
            if key in self._parsers:
                return self._parsers[key]

        robots_url = f"{scheme}://{netloc}/robots.txt"
        rp: RobotFileParser | None
        try:
            response = self._client.get(robots_url)
            if response.status_code >= 400:
                logger.debug("No robots.txt at %s (%s)", robots_url, response.status_code)
                rp = None
            else:
                rp = RobotFileParser()
                rp.parse(response.text.splitlines())
                logger.debug("Loaded robots.txt from %s", robots_url)
        except httpx.HTTPError as exc:
            logger.debug("Failed to fetch robots.txt %s: %s", robots_url, exc)
            rp = None

        with self._lock:
            self._parsers[key] = rp
            return self._parsers[key]
