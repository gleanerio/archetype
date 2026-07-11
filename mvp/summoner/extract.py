"""Detect and extract JSON-LD from HTTP responses."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Match type values that indicate JSON-LD script tags (with optional charset etc.)
_LD_JSON_TYPE_RE = re.compile(r"application/ld\+json", re.IGNORECASE)


@dataclass
class ExtractResult:
    """Result of attempting to extract JSON-LD from a URL response."""

    url: str
    data: Any | None = None
    source: str | None = None  # "json-body" | "script-tag"
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.data is not None and self.error is None


def _looks_like_jsonld(value: Any) -> bool:
    """Lightweight structural check for JSON-LD."""
    if isinstance(value, list):
        return bool(value) and all(_looks_like_jsonld(item) for item in value if item is not None)
    if not isinstance(value, dict):
        return False
    return any(k in value for k in ("@context", "@type", "@graph", "@id"))


def _parse_json_text(text: str) -> Any | None:
    text = text.strip()
    if not text:
        return None
    # Strip HTML/XML CDATA wrappers if present
    if text.startswith("<![CDATA[") and text.endswith("]]>"):
        text = text[9:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_from_json_body(url: str, body: str, content_type: str = "") -> ExtractResult:
    """Treat the response body as a JSON / JSON-LD document."""
    parsed = _parse_json_text(body)
    if parsed is None:
        return ExtractResult(url=url, error="body is not valid JSON")
    if not _looks_like_jsonld(parsed):
        # Still accept plain JSON if content-type claims ld+json
        ct = content_type.lower()
        if "ld+json" not in ct:
            return ExtractResult(url=url, error="JSON body does not look like JSON-LD")
    return ExtractResult(url=url, data=parsed, source="json-body")


def extract_from_html(url: str, html: str) -> ExtractResult:
    """Extract application/ld+json script blocks from HTML."""
    soup = BeautifulSoup(html, "lxml")
    blocks: list[Any] = []

    for script in soup.find_all("script"):
        script_type = script.get("type") or ""
        if not _LD_JSON_TYPE_RE.search(script_type):
            continue
        raw = script.string if script.string is not None else script.get_text()
        if raw is None:
            continue
        parsed = _parse_json_text(raw)
        if parsed is None:
            logger.debug("Skipping invalid JSON-LD script on %s", url)
            continue
        if isinstance(parsed, list):
            blocks.extend(parsed)
        else:
            blocks.append(parsed)

    if not blocks:
        return ExtractResult(url=url, error="no application/ld+json script tags found")

    data: Any = blocks[0] if len(blocks) == 1 else blocks
    return ExtractResult(url=url, data=data, source="script-tag")


def _is_json_content_type(content_type: str) -> bool:
    ct = content_type.lower()
    return any(
        token in ct
        for token in (
            "application/ld+json",
            "application/json",
            "text/json",
            "+json",
        )
    )


def _is_html_content_type(content_type: str) -> bool:
    ct = content_type.lower()
    return "text/html" in ct or "application/xhtml" in ct


def _looks_like_html(body: str) -> bool:
    sample = body.lstrip()[:200].lower()
    return sample.startswith("<!doctype html") or sample.startswith("<html") or "<script" in sample


def extract_jsonld(url: str, body: str, content_type: str = "") -> ExtractResult:
    """Classify response and extract JSON-LD.

    Preference order:
    1. JSON content-type → parse as JSON-LD document
    2. HTML content-type or HTML-looking body → script tags
    3. Try JSON parse, then HTML parse as fallbacks
    """
    ct = content_type or ""

    if _is_json_content_type(ct):
        result = extract_from_json_body(url, body, ct)
        if result.ok:
            return result
        # Fall through: some servers mislabel HTML as JSON rarely; try HTML next

    if _is_html_content_type(ct) or _looks_like_html(body):
        return extract_from_html(url, body)

    # Unknown type: try JSON first, then HTML
    json_result = extract_from_json_body(url, body, ct)
    if json_result.ok:
        return json_result

    if body.lstrip().startswith("<"):
        return extract_from_html(url, body)

    return ExtractResult(
        url=url,
        error=json_result.error or "could not extract JSON-LD",
    )


def dumps_jsonld(data: Any) -> bytes:
    """Serialize extracted JSON-LD for storage."""
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
