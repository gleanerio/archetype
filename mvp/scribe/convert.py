"""Convert JSON-LD documents to N-Quads in a named graph."""

from __future__ import annotations

import logging

from rdflib import Dataset, Graph, URIRef

logger = logging.getLogger(__name__)


def jsonld_to_nquads(body: bytes | str, graph_iri: str) -> str:
    """Parse JSON-LD and serialize as N-Quads all in ``graph_iri``.

    Uses a temporary Graph for JSON-LD parse (reliable across rdflib versions),
    then copies triples into a Dataset named graph for N-Quads output.
    """
    if isinstance(body, bytes):
        text = body.decode("utf-8")
    else:
        text = body

    g = Graph()
    g.parse(data=text, format="json-ld")

    ds = Dataset()
    named = ds.graph(URIRef(graph_iri))
    for triple in g:
        named.add(triple)

    # rdflib may return str or bytes depending on version
    raw = ds.serialize(format="nquads")
    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    return raw


def jsonld_to_nquads_safe(body: bytes | str, graph_iri: str, *, key: str = "") -> str | None:
    """Like jsonld_to_nquads but returns None on parse failure."""
    try:
        return jsonld_to_nquads(body, graph_iri)
    except Exception as exc:  # noqa: BLE001 — per-object skip
        label = key or "<inline>"
        logger.warning("Failed to convert JSON-LD %s: %s", label, exc)
        return None


def count_quad_lines(nquads: str) -> int:
    return sum(1 for line in nquads.splitlines() if line.strip() and not line.strip().startswith("#"))


def merge_nquads(fragments: list[str]) -> str:
    parts = [f.strip() for f in fragments if f and f.strip()]
    if not parts:
        return ""
    return "\n".join(parts) + "\n"
