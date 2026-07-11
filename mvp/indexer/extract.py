"""Extract searchable facade documents from JSON-LD."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _plain_string(value: Any) -> str | None:
    """Coerce Schema.org-ish values to a plain string."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        # language map {"en": "..."} or schema.org TextObject
        if "@value" in value:
            return _plain_string(value.get("@value"))
        for key in ("name", "text", "value", "termCode"):
            if key in value:
                return _plain_string(value[key])
        # simple language map: pick first string value
        for v in value.values():
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None
    if isinstance(value, list):
        for item in value:
            s = _plain_string(item)
            if s:
                return s
        return None
    return str(value)


def _string_list(value: Any) -> list[str]:
    out: list[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            # DefinedTerm etc.: prefer name, then termCode, then @id
            s = (
                _plain_string(item.get("name"))
                or _plain_string(item.get("termCode"))
                or _plain_string(item.get("@id"))
                or _plain_string(item)
            )
        else:
            s = _plain_string(item)
        if s and s not in out:
            out.append(s)
    return out


def _type_list(value: Any) -> list[str]:
    types: list[str] = []
    for item in _as_list(value):
        if isinstance(item, str):
            # strip schema.org URL prefix for nicer keywords
            t = item.rsplit("/", 1)[-1] if item.startswith("http") else item
            if t and t not in types:
                types.append(t)
        else:
            s = _plain_string(item)
            if s and s not in types:
                types.append(s)
    return types


def _doc_id(node: dict[str, Any], s3_key: str, index_in_file: int) -> str:
    rid = node.get("@id")
    if isinstance(rid, str) and rid.strip():
        # ES _id length limit; hash long IRIs
        if len(rid) <= 512:
            return rid
        return hashlib.sha1(rid.encode("utf-8")).hexdigest()
    base = s3_key.rsplit("/", 1)[-1]
    if index_in_file == 0:
        return base
    return f"{base}#{index_in_file}"


def extract_document(
    node: dict[str, Any],
    *,
    source: str,
    s3_key: str,
    graph: str,
    index_in_file: int = 0,
    source_url: str | None = None,
) -> dict[str, Any]:
    """Build one ES document with search facade + full jsonld.

    ``url`` is Schema.org resource/landing page from the JSON-LD.
    ``source_url`` is the harvest page URL recorded by summoner on S3 metadata.
    """
    name = _plain_string(node.get("name"))
    description = _plain_string(node.get("description"))
    keywords = _string_list(node.get("keywords"))
    # also accept schema.org alternate
    if not keywords:
        keywords = _string_list(node.get("keyword"))

    urls = _string_list(node.get("url"))
    url = urls[0] if urls else None

    doc: dict[str, Any] = {
        "source": source,
        "s3_key": s3_key,
        "graph": graph,
        "id": _plain_string(node.get("@id")),
        "type": _type_list(node.get("@type")),
        "name": name,
        "description": description,
        "keywords": keywords,
        "url": url,
        "source_url": source_url,
        "jsonld": node,
        "_id": _doc_id(node, s3_key, index_in_file),
    }
    return doc


def documents_from_jsonld_bytes(
    body: bytes | str,
    *,
    source: str,
    s3_key: str,
    graph: str,
    source_url: str | None = None,
) -> list[dict[str, Any]]:
    """Parse JSON-LD object or array into one or more ES documents."""
    if isinstance(body, bytes):
        text = body.decode("utf-8")
    else:
        text = body

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON in %s: %s", s3_key, exc)
        return []

    nodes: list[Any]
    if isinstance(data, list):
        nodes = data
    elif isinstance(data, dict):
        # Expand @graph if present at top level alongside other keys rarely
        if "@graph" in data and isinstance(data["@graph"], list):
            nodes = data["@graph"]
        else:
            nodes = [data]
    else:
        logger.warning("Unexpected JSON root type in %s: %s", s3_key, type(data))
        return []

    docs: list[dict[str, Any]] = []
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        docs.append(
            extract_document(
                node,
                source=source,
                s3_key=s3_key,
                graph=graph,
                index_in_file=i,
                source_url=source_url,
            )
        )
    return docs

