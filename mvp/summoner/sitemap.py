"""Fetch and parse XML sitemaps and sitemap indexes."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Callable
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
MAX_DEPTH = 5


def _local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _child_text(elem: ET.Element, name: str) -> str | None:
    for child in elem:
        if _local_name(child.tag) == name and child.text:
            return child.text.strip()
    return None


def parse_sitemap_xml(content: str | bytes, base_url: str = "") -> tuple[str, list[str]]:
    """Parse sitemap XML.

    Returns:
        (kind, urls) where kind is 'urlset' or 'sitemapindex'.
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML sitemap: {exc}") from exc

    kind = _local_name(root.tag)
    if kind not in ("urlset", "sitemapindex"):
        # Some servers omit proper root naming; try children.
        raise ValueError(f"Unrecognized sitemap root element: {root.tag}")

    locs: list[str] = []
    child_name = "url" if kind == "urlset" else "sitemap"
    for child in root:
        if _local_name(child.tag) != child_name:
            continue
        loc = _child_text(child, "loc")
        if not loc:
            continue
        if base_url and not loc.startswith(("http://", "https://")):
            loc = urljoin(base_url, loc)
        locs.append(loc)

    return kind, locs


def collect_page_urls(
    sitemap_url: str,
    client: httpx.Client,
    *,
    max_depth: int = MAX_DEPTH,
    seen: set[str] | None = None,
    depth: int = 0,
    limit: int | None = None,
) -> list[str]:
    """Recursively expand a sitemap or sitemap index into page URLs.

    If ``limit`` is set, stop once that many page URLs have been collected
    (avoids downloading every nested sitemap during smoke tests).
    """
    if seen is None:
        seen = set()

    if depth > max_depth:
        logger.warning("Sitemap recursion depth exceeded at %s (max=%s)", sitemap_url, max_depth)
        return []

    if sitemap_url in seen:
        logger.debug("Skipping already-seen sitemap: %s", sitemap_url)
        return []
    seen.add(sitemap_url)

    logger.info("Fetching sitemap: %s", sitemap_url)
    try:
        response = client.get(sitemap_url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch sitemap %s: %s", sitemap_url, exc)
        return []

    content_type = (response.headers.get("content-type") or "").lower()
    text = response.text
    # gzip is usually handled by httpx; if body still looks binary XML, parse as text.
    try:
        kind, locs = parse_sitemap_xml(text, base_url=str(response.url))
    except ValueError as exc:
        logger.error("Could not parse sitemap %s (%s): %s", sitemap_url, content_type, exc)
        return []

    if kind == "urlset":
        if limit is not None:
            locs = locs[:limit]
        logger.info("Sitemap urlset %s → %d page URL(s)", sitemap_url, len(locs))
        return locs

    # sitemapindex: recurse into each nested sitemap
    logger.info("Sitemap index %s → %d nested sitemap(s)", sitemap_url, len(locs))
    pages: list[str] = []
    for nested in locs:
        remaining = None if limit is None else max(0, limit - len(pages))
        if remaining == 0:
            break
        pages.extend(
            collect_page_urls(
                nested,
                client,
                max_depth=max_depth,
                seen=seen,
                depth=depth + 1,
                limit=remaining,
            )
        )
    return pages


def collect_page_urls_from_text(
    content: str | bytes,
    *,
    base_url: str = "",
    fetch_nested: Callable[[str], str | bytes] | None = None,
    max_depth: int = MAX_DEPTH,
    seen: set[str] | None = None,
    depth: int = 0,
) -> list[str]:
    """Parse sitemap content without HTTP (useful for tests).

    If content is a sitemapindex, ``fetch_nested`` must return nested sitemap bodies.
    """
    if seen is None:
        seen = set()
    if depth > max_depth:
        return []

    kind, locs = parse_sitemap_xml(content, base_url=base_url)
    if kind == "urlset":
        return locs

    if fetch_nested is None:
        raise ValueError("sitemapindex requires fetch_nested callback when offline")

    pages: list[str] = []
    for nested_url in locs:
        if nested_url in seen:
            continue
        seen.add(nested_url)
        nested_body = fetch_nested(nested_url)
        pages.extend(
            collect_page_urls_from_text(
                nested_body,
                base_url=nested_url,
                fetch_nested=fetch_nested,
                max_depth=max_depth,
                seen=seen,
                depth=depth + 1,
            )
        )
    return pages
