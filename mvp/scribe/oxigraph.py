"""Oxigraph HTTP helpers: CLEAR GRAPH + bulk N-Quads load."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


def clear_graph(endpoint: str, graph_iri: str, *, client: httpx.Client | None = None) -> None:
    """CLEAR GRAPH <graph_iri> via SPARQL Update."""
    base = endpoint.rstrip("/")
    update = f"CLEAR SILENT GRAPH <{graph_iri}>"
    url = f"{base}/update"
    owns = client is None
    if owns:
        client = httpx.Client(timeout=60.0)
    try:
        logger.info("CLEAR GRAPH <%s> → %s", graph_iri, url)
        response = client.post(
            url,
            content=update.encode("utf-8"),
            headers={"Content-Type": "application/sparql-update"},
        )
        response.raise_for_status()
    finally:
        if owns:
            client.close()


def load_nquads(endpoint: str, nquads: str | bytes, *, client: httpx.Client | None = None) -> None:
    """POST N-Quads to Oxigraph /store."""
    base = endpoint.rstrip("/")
    url = f"{base}/store"
    if isinstance(nquads, str):
        payload = nquads.encode("utf-8")
    else:
        payload = nquads

    owns = client is None
    if owns:
        client = httpx.Client(timeout=120.0)
    try:
        logger.info("POST %d bytes N-Quads → %s", len(payload), url)
        response = client.post(
            url,
            content=payload,
            headers={"Content-Type": "application/n-quads"},
        )
        # Some Oxigraph builds prefer text/x-nquads; retry once on 415
        if response.status_code == 415:
            logger.debug("Retrying with Content-Type: text/x-nquads")
            response = client.post(
                url,
                content=payload,
                headers={"Content-Type": "text/x-nquads"},
            )
        response.raise_for_status()
    finally:
        if owns:
            client.close()


def replace_graph_with_nquads(
    endpoint: str,
    graph_iri: str,
    nquads: str | bytes,
    *,
    client: httpx.Client | None = None,
) -> None:
    """Clear named graph then bulk-load N-Quads."""
    replace_graphs_with_nquads(endpoint, [graph_iri], nquads, client=client)


def replace_graphs_with_nquads(
    endpoint: str,
    graph_iris: list[str],
    nquads: str | bytes,
    *,
    client: httpx.Client | None = None,
) -> None:
    """Clear one or more named graphs then bulk-load N-Quads (quads carry graph IRIs)."""
    if not graph_iris:
        raise ValueError("graph_iris must be non-empty")
    owns = client is None
    if owns:
        client = httpx.Client(timeout=120.0)
    try:
        for g in graph_iris:
            clear_graph(endpoint, g, client=client)
        if not nquads or (isinstance(nquads, str) and not nquads.strip()):
            logger.warning(
                "No quads to load after clearing %s",
                ", ".join(f"<{g}>" for g in graph_iris),
            )
            return
        load_nquads(endpoint, nquads, client=client)
    finally:
        if owns:
            client.close()
