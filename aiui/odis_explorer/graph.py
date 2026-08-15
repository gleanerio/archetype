"""Turn Schema.org JSON-LD nodes into a force-graph of records and related entities."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

SKIP_KEYS = {"@context", "@vocab", "@graph", "@included"}
IDENTITY_KEYS = {"sameAs", "url", "identifier", "schema:sameAs", "schema:url", "schema:identifier"}
LABEL_KEYS = ("name", "title", "legalName", "alternateName", "schema:name", "schema:title")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _plain_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        for key in ("@value", "value", "name"):
            inner = value.get(key)
            if isinstance(inner, str) and inner.strip():
                return inner.strip()
    return None


def _first_type(value: Any) -> str | None:
    for item in _as_list(value):
        text = _plain_string(item)
        if text:
            return text.split("/")[-1].removeprefix("schema:")
    return None


def _is_http_id(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _label_from_id(node_id: str) -> str:
    parsed = urlparse(node_id)
    tail = (parsed.path or "").rstrip("/").split("/")[-1]
    if tail:
        return tail
    return node_id


def _node_label(obj: dict[str, Any], node_id: str) -> str:
    for key in LABEL_KEYS:
        text = _plain_string(obj.get(key))
        if text:
            return text[:160]
    node_type = _first_type(obj.get("@type"))
    if node_type:
        return node_type
    if node_id.startswith("_:"):
        return "blank"
    return _label_from_id(node_id)[:160]


def _literal_details(obj: dict[str, Any]) -> dict[str, str]:
    details: dict[str, str] = {}
    for key, value in obj.items():
        if key.startswith("@") or key in SKIP_KEYS:
            continue
        text = _plain_string(value)
        if text and not isinstance(value, (dict, list)):
            details[key.split(":")[-1]] = text[:240]
            continue
        if isinstance(value, list):
            strings = [part for part in (_plain_string(item) for item in value) if part]
            if strings and all(not isinstance(item, dict) for item in value):
                details[key.split(":")[-1]] = ", ".join(strings[:8])[:240]
    return details


def _is_graph_object(value: Any) -> bool:
    return isinstance(value, dict) and ("@id" in value or "@type" in value or any(
        key not in {"@context", "@value", "@language", "@type"} for key in value
    ))


class GraphBuilder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self._edge_keys: set[tuple[str, str, str]] = set()
        self._blank_seq = 0

    def add_item(self, item: dict[str, Any]) -> None:
        record_id = str(item.get("id") or "")
        jsonld = item.get("jsonld")
        if isinstance(jsonld, dict):
            if not _plain_string(jsonld.get("@id")):
                fallback = _plain_string(item.get("url")) or record_id
                if fallback:
                    jsonld = {**jsonld, "@id": fallback}
            self._walk(jsonld, record_id=record_id, path="root", is_root=True)
            return
        if not record_id:
            return
        self._upsert_node(
            record_id,
            {
                "@id": item.get("url") or record_id,
                "@type": item.get("type") or "Record",
                "name": item.get("title") or "(untitled)",
            },
            record_id=record_id,
            is_root=True,
        )

    def as_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "nodes": list(self.nodes.values()),
            "edges": list(self.edges),
        }

    def _blank_id(self, record_id: str, path: str) -> str:
        self._blank_seq += 1
        scope = record_id or "record"
        return f"_:{scope}:{path}:{self._blank_seq}"

    def _upsert_node(
        self,
        node_id: str,
        obj: dict[str, Any],
        *,
        record_id: str,
        is_root: bool,
    ) -> str:
        node = self.nodes.get(node_id)
        label = _node_label(obj, node_id)
        node_type = _first_type(obj.get("@type")) or ("Record" if is_root else "Thing")
        details = _literal_details(obj)
        if node is None:
            node = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "recordIds": [],
                "isRecord": False,
                "details": details,
            }
            self.nodes[node_id] = node
        else:
            if label and (node["label"] in {node["type"], _label_from_id(node_id), "blank"}):
                node["label"] = label
            if node["type"] in {"Thing", "Record"} and node_type not in {"Thing", "Record"}:
                node["type"] = node_type
            for key, value in details.items():
                node["details"].setdefault(key, value)

        if record_id and record_id not in node["recordIds"]:
            node["recordIds"].append(record_id)
        if is_root:
            node["isRecord"] = True
            if record_id:
                node["recordId"] = record_id
        return node_id

    def _add_edge(self, source: str, target: str, label: str) -> None:
        key = (source, target, label)
        if key in self._edge_keys or source == target:
            return
        self._edge_keys.add(key)
        self.edges.append({"from": source, "to": target, "label": label})

    def _walk(self, obj: Any, *, record_id: str, path: str, is_root: bool) -> str | None:
        if isinstance(obj, list):
            last = None
            for index, item in enumerate(obj):
                last = self._walk(item, record_id=record_id, path=f"{path}.{index}", is_root=False)
            return last
        if not isinstance(obj, dict):
            return None

        raw_id = _plain_string(obj.get("@id"))
        node_id = raw_id if raw_id else self._blank_id(record_id, path)
        self._upsert_node(node_id, obj, record_id=record_id, is_root=is_root)

        for key, value in obj.items():
            if key.startswith("@") or key in SKIP_KEYS:
                continue
            edge_label = key.split(":")[-1]
            for index, child in enumerate(_as_list(value)):
                child_path = f"{path}.{edge_label}.{index}"
                if isinstance(child, dict) and (
                    "@id" in child or "@type" in child or _is_graph_object(child)
                ):
                    child_id = self._walk(child, record_id=record_id, path=child_path, is_root=False)
                    if child_id:
                        self._add_edge(node_id, child_id, edge_label)
                    continue
                text = _plain_string(child)
                if text and key in IDENTITY_KEYS and _is_http_id(text) and text != node_id:
                    self._upsert_node(
                        text,
                        {"@id": text, "@type": "Thing", "name": _label_from_id(text)},
                        record_id=record_id,
                        is_root=False,
                    )
                    self._add_edge(node_id, text, edge_label)
        return node_id


def graph_from_items(items: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    builder = GraphBuilder()
    for item in items:
        if isinstance(item, dict):
            builder.add_item(item)
    return builder.as_dict()
