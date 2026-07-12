"""Build harvest/load provenance N-Quads for a summoned JSON-LD object."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import unquote

from .config import activity_iri, agent_iri, object_iri

logger = logging.getLogger(__name__)

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
PROV = "http://www.w3.org/ns/prov#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD = "http://www.w3.org/2001/XMLSchema#"

# Loose check for IRIs we can put in angle brackets
_IRI_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def sha_from_s3_key(s3_key: str) -> str:
    """Basename without extension, e.g. summoned/medin/abc.json → abc."""
    base = s3_key.rsplit("/", 1)[-1]
    if base.lower().endswith(".jsonld"):
        return base[: -len(".jsonld")]
    if base.lower().endswith(".json"):
        return base[: -len(".json")]
    return base


def collect_entity_ids(body: bytes | str) -> list[str]:
    """Collect top-level @id IRIs from a JSON-LD document (object, array, or @graph)."""
    if isinstance(body, bytes):
        text = body.decode("utf-8")
    else:
        text = body
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.debug("Cannot parse JSON-LD for entity ids: %s", exc)
        return []

    nodes: list[Any]
    if isinstance(data, list):
        nodes = data
    elif isinstance(data, dict):
        if isinstance(data.get("@graph"), list):
            nodes = data["@graph"]
        else:
            nodes = [data]
    else:
        return []

    ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        rid = node.get("@id")
        if isinstance(rid, str) and _is_iri(rid) and rid not in ids:
            ids.append(rid)
    return ids


def build_prov_nquads(
    *,
    source: str,
    s3_key: str,
    data_graph: str,
    prov_graph: str,
    harvest_url: str | None = None,
    entity_ids: list[str] | None = None,
    when: datetime | None = None,
) -> str:
    """Serialize object-level PROV-O as N-Quads in ``prov_graph``.

    Links:
    - harvested JSON-LD object (S3) ↔ harvest page URL (``prov:hadPrimarySource``)
    - object ↔ content entity ``@id`` when present (``prov:wasDerivedFrom``)
    - object ↔ data named graph (``rdfs:seeAlso``)
    """
    sha = sha_from_s3_key(s3_key)
    if not sha:
        logger.warning("Empty sha for s3_key=%s; skipping prov", s3_key)
        return ""

    ts = when or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    # N-Quads / xsd:dateTime: use ISO with Z
    iso = ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    obj = object_iri(source, sha)
    act = activity_iri(source, sha)
    agent = agent_iri()
    entities = entity_ids or []
    page = _normalize_harvest_url(harvest_url)

    lines: list[str] = []

    # Object entity
    lines.append(_quad(obj, f"{RDF}type", f"{PROV}Entity", None, prov_graph))
    lines.append(_quad(obj, f"{PROV}value", None, s3_key, prov_graph, literal=True))
    lines.append(_quad(obj, f"{PROV}wasGeneratedBy", act, None, prov_graph))
    lines.append(
        _quad(
            obj,
            f"{PROV}generatedAtTime",
            None,
            iso,
            prov_graph,
            literal=True,
            datatype=f"{XSD}dateTime",
        )
    )
    lines.append(_quad(obj, f"{RDFS}seeAlso", data_graph, None, prov_graph))

    if page:
        lines.append(_quad(page, f"{RDF}type", f"{PROV}Entity", None, prov_graph))
        lines.append(_quad(obj, f"{PROV}hadPrimarySource", page, None, prov_graph))

    for eid in entities:
        if _is_iri(eid):
            lines.append(_quad(obj, f"{PROV}wasDerivedFrom", eid, None, prov_graph))

    # Activity
    lines.append(_quad(act, f"{RDF}type", f"{PROV}Activity", None, prov_graph))
    lines.append(_quad(act, f"{PROV}generated", obj, None, prov_graph))
    lines.append(_quad(act, f"{PROV}wasAssociatedWith", agent, None, prov_graph))
    lines.append(
        _quad(
            act,
            f"{PROV}endedAtTime",
            None,
            iso,
            prov_graph,
            literal=True,
            datatype=f"{XSD}dateTime",
        )
    )
    if page:
        lines.append(_quad(act, f"{PROV}used", page, None, prov_graph))

    # Agent (idempotent if repeated across objects)
    lines.append(_quad(agent, f"{RDF}type", f"{PROV}SoftwareAgent", None, prov_graph))

    return "\n".join(lines) + "\n"


def _normalize_harvest_url(url: str | None) -> str | None:
    if not url:
        return None
    u = unquote(url.strip())
    if not u or not _is_iri(u):
        return None
    # Prefer http(s) harvest pages; still accept other IRIs if present
    return u


def _is_iri(value: str) -> bool:
    return bool(value) and bool(_IRI_RE.match(value)) and " " not in value and "\n" not in value


def _nquad_iri(iri: str) -> str:
    return f"<{iri}>"


def _nquad_literal(value: str, datatype: str | None = None) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    if datatype:
        return f'"{escaped}"^^<{datatype}>'
    return f'"{escaped}"'


def _quad(
    subject: str,
    predicate: str,
    object_iri_value: str | None,
    object_literal: str | None,
    graph: str,
    *,
    literal: bool = False,
    datatype: str | None = None,
) -> str:
    s = _nquad_iri(subject)
    p = _nquad_iri(predicate)
    if literal:
        assert object_literal is not None
        o = _nquad_literal(object_literal, datatype=datatype)
    else:
        assert object_iri_value is not None
        o = _nquad_iri(object_iri_value)
    g = _nquad_iri(graph)
    return f"{s} {p} {o} {g} ."
