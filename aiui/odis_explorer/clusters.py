"""Overlapping feature clusters for one page of ODIS search hits."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any
from urllib.parse import quote, urlparse

from odis_explorer.graph import _as_list, _label_from_id, _plain_string

MIN_CLUSTER_SIZE = 2
MAX_CLUSTERS = 12
PRIORITY_KINDS = ("source", "catalog", "org")

ORG_KEYS = (
    "publisher",
    "provider",
    "creator",
    "author",
    "sourceOrganization",
    "schema:publisher",
    "schema:provider",
    "schema:creator",
    "schema:author",
    "schema:sourceOrganization",
)
CATALOG_KEYS = ("includedInDataCatalog", "schema:includedInDataCatalog")
KEYWORD_KEYS = ("keywords", "keyword", "schema:keywords", "schema:keyword")


def _slug(kind: str, key: str) -> str:
    token = quote(key.strip().lower(), safe=".-_")[:120]
    return f"cluster:{kind}:{token}"


def _entity_label(value: Any) -> str | None:
    text = _plain_string(value)
    if text:
        return text
    if not isinstance(value, dict):
        return None
    for key in ("name", "legalName", "alternateName", "title", "schema:name"):
        text = _plain_string(value.get(key))
        if text:
            return text
    node_id = _plain_string(value.get("@id")) or _plain_string(value.get("url"))
    if node_id:
        tail = _label_from_id(node_id)
        if tail != node_id:
            return tail
        parsed = urlparse(node_id)
        if parsed.netloc:
            return parsed.netloc
        return node_id
    return None


def _entity_key(value: Any) -> str | None:
    if isinstance(value, dict):
        node_id = _plain_string(value.get("@id"))
        if node_id:
            return node_id
        url = _plain_string(value.get("url"))
        if url:
            return url
    label = _entity_label(value)
    return label.lower() if label else None


def _keyword_texts(value: Any) -> list[str]:
    texts: list[str] = []
    raw = _plain_string(value)
    if raw:
        texts.append(raw)
        if " | " in raw:
            last = raw.split(" | ")[-1].strip()
            if last and last.lower() != raw.lower():
                texts.append(last)
    elif isinstance(value, dict):
        label = _entity_label(value)
        if label:
            texts.append(label)
    seen: set[str] = set()
    unique: list[str] = []
    for text in texts:
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(text)
    return unique


def _source_feature(item: dict[str, Any]) -> tuple[str, str] | None:
    source = item.get("source")
    if isinstance(source, str) and source.strip():
        return source.strip(), source.strip()
    if not isinstance(source, dict):
        return None
    key = _plain_string(source.get("id")) or _plain_string(source.get("name"))
    if not key:
        return None
    label = _plain_string(source.get("name")) or key
    return key, label


def _collect_features(item: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Return (kind, key, label) features for one hit."""
    features: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, key: str, label: str) -> None:
        key = key.strip()
        label = label.strip()
        if not key or not label:
            return
        pair = (kind, key.lower())
        if pair in seen:
            return
        seen.add(pair)
        features.append((kind, key, label))

    source = _source_feature(item)
    if source:
        add("source", source[0], source[1])

    jsonld = item.get("jsonld")
    nodes: list[dict[str, Any]] = []
    if isinstance(jsonld, dict):
        nodes.append(jsonld)
        graph = jsonld.get("@graph")
        if isinstance(graph, list):
            nodes.extend(part for part in graph if isinstance(part, dict))

    for node in nodes:
        for key in CATALOG_KEYS:
            for child in _as_list(node.get(key)):
                entity_key = _entity_key(child)
                label = _entity_label(child)
                if entity_key and label:
                    add("catalog", entity_key, label)
        for key in ORG_KEYS:
            for child in _as_list(node.get(key)):
                entity_key = _entity_key(child)
                label = _entity_label(child)
                if entity_key and label:
                    add("org", entity_key, label)
        for key in KEYWORD_KEYS:
            for child in _as_list(node.get(key)):
                for text in _keyword_texts(child):
                    add("keyword", text.lower(), text)

    return features


def _record_label(item: dict[str, Any]) -> str:
    title = _plain_string(item.get("title"))
    if title:
        return title[:160]
    jsonld = item.get("jsonld")
    if isinstance(jsonld, dict):
        name = _plain_string(jsonld.get("name")) or _plain_string(jsonld.get("title"))
        if name:
            return name[:160]
    return str(item.get("id") or "(untitled)")


def _select_clusters(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def rank(cluster: dict[str, Any]) -> tuple:
        return (-cluster["size"], cluster["label"].lower(), cluster["id"])

    priority = [c for c in candidates if c["kind"] in PRIORITY_KINDS]
    keywords = [c for c in candidates if c["kind"] == "keyword"]
    other = [c for c in candidates if c["kind"] not in PRIORITY_KINDS and c["kind"] != "keyword"]
    selected: list[dict[str, Any]] = []
    for group in (priority, other, keywords):
        for cluster in sorted(group, key=rank):
            if len(selected) >= MAX_CLUSTERS:
                return selected
            selected.append(cluster)
    return selected


def _cluster_graph(
    items: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for cluster in clusters:
        nodes.append(
            {
                "id": cluster["id"],
                "label": f"{cluster['label']} ({cluster['size']})",
                "type": "Cluster",
                "kind": cluster["kind"],
                "isRecord": False,
                "isCluster": True,
                "recordIds": list(cluster["recordIds"]),
                "details": {"kind": cluster["kind"], "size": str(cluster["size"])},
            }
        )
        for record_id in cluster["recordIds"]:
            edges.append({"from": cluster["id"], "to": record_id, "label": cluster["kind"]})

    for item in items:
        record_id = str(item.get("id") or "")
        if not record_id:
            continue
        nodes.append(
            {
                "id": record_id,
                "label": _record_label(item),
                "type": item.get("type") or "Record",
                "isRecord": True,
                "isCluster": False,
                "recordId": record_id,
                "recordIds": [record_id],
                "details": {"name": _record_label(item)},
            }
        )
    return {"nodes": nodes, "edges": edges}


def clusters_from_items(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = [item for item in items if isinstance(item, dict) and item.get("id")]
    members: dict[tuple[str, str], set[str]] = defaultdict(set)
    labels: dict[tuple[str, str], str] = {}

    for item in records:
        record_id = str(item["id"])
        for kind, key, label in _collect_features(item):
            pair = (kind, key.lower())
            members[pair].add(record_id)
            labels.setdefault(pair, label)

    candidates: list[dict[str, Any]] = []
    for (kind, key), record_ids in members.items():
        if len(record_ids) < MIN_CLUSTER_SIZE:
            continue
        label = labels[(kind, key)]
        ordered = sorted(record_ids)
        candidates.append(
            {
                "id": _slug(kind, key),
                "kind": kind,
                "label": label,
                "recordIds": ordered,
                "size": len(ordered),
            }
        )

    clusters = _select_clusters(candidates)
    memberships: dict[str, list[str]] = {str(item["id"]): [] for item in records}
    for cluster in clusters:
        for record_id in cluster["recordIds"]:
            memberships.setdefault(record_id, []).append(cluster["id"])

    return {
        "clusters": clusters,
        "memberships": memberships,
        "graph": _cluster_graph(records, clusters),
    }
