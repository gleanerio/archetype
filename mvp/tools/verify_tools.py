"""Read-only verification tools against Oxigraph and Elasticsearch."""

from __future__ import annotations

from typing import Any

import httpx
import yaml

from indexer.config import index_name
from scribe.config import graph_iri, prov_graph_iri

from ._util import err_result, ok_result, resolve_config_path


def _load_yaml(config_path: str | None) -> tuple[str, dict[str, Any]]:
    path = resolve_config_path(config_path)
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise ValueError("config root must be a mapping")
    return str(path), raw


def verify_graph(
    source: str,
    *,
    config_path: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    """SPARQL COUNT on data and prov named graphs for a source."""
    try:
        path, raw = _load_yaml(config_path)
        ep = (endpoint or (raw.get("triplestore") or {}).get("endpoint") or "").rstrip("/")
        if not ep:
            return err_result("no triplestore.endpoint in config", source=source)

        data_g = graph_iri(source)
        prov_g = prov_graph_iri(source)

        def count_graph(g: str) -> dict[str, Any]:
            query = f"SELECT (COUNT(*) AS ?c) WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }}"
            try:
                with httpx.Client(timeout=30.0) as client:
                    r = client.post(
                        f"{ep}/query",
                        content=query.encode("utf-8"),
                        headers={
                            "Accept": "application/sparql-results+json",
                            "Content-Type": "application/sparql-query",
                        },
                    )
                if r.status_code >= 400:
                    return {"graph": g, "ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
                payload = r.json()
                bindings = payload.get("results", {}).get("bindings", [])
                count = 0
                if bindings:
                    count = int(bindings[0].get("c", {}).get("value", 0))
                return {"graph": g, "ok": True, "triple_count": count}
            except Exception as exc:  # noqa: BLE001
                return {"graph": g, "ok": False, "error": str(exc)}

        data = count_graph(data_g)
        prov = count_graph(prov_g)
        ok = bool(data.get("ok") and prov.get("ok"))
        return {
            "ok": ok,
            "config_path": path,
            "endpoint": ep,
            "source": source,
            "data": data,
            "prov": prov,
        }
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc), source=source)


def verify_index(
    source: str,
    *,
    config_path: str | None = None,
    endpoint: str | None = None,
    index_prefix: str | None = None,
) -> dict[str, Any]:
    """Elasticsearch _count (and optional sample) for gleaner-<source>."""
    try:
        path, raw = _load_yaml(config_path)
        search = raw.get("search") or {}
        ep = (endpoint or search.get("endpoint") or "").rstrip("/")
        prefix = index_prefix or search.get("index_prefix") or "gleaner"
        if not ep:
            return err_result("no search.endpoint in config", source=source)

        idx = index_name(source, prefix)
        with httpx.Client(timeout=15.0) as client:
            # index exists?
            head = client.head(f"{ep}/{idx}")
            if head.status_code == 404:
                return ok_result(
                    config_path=path,
                    endpoint=ep,
                    source=source,
                    index=idx,
                    exists=False,
                    count=0,
                )
            if head.status_code >= 400 and head.status_code != 200:
                # some ES versions use GET for exists
                pass

            count_r = client.get(f"{ep}/{idx}/_count")
            if count_r.status_code == 404:
                return ok_result(
                    config_path=path,
                    endpoint=ep,
                    source=source,
                    index=idx,
                    exists=False,
                    count=0,
                )
            count_r.raise_for_status()
            count = int(count_r.json().get("count", 0))

            sample_names: list[str] = []
            if count > 0:
                search_r = client.post(
                    f"{ep}/{idx}/_search",
                    json={
                        "size": 3,
                        "query": {"match_all": {}},
                        "_source": ["name", "url", "type"],
                    },
                )
                if search_r.status_code < 400:
                    hits = search_r.json().get("hits", {}).get("hits", [])
                    for h in hits:
                        src = h.get("_source") or {}
                        sample_names.append(str(src.get("name") or h.get("_id")))

        return ok_result(
            config_path=path,
            endpoint=ep,
            source=source,
            index=idx,
            exists=True,
            count=count,
            sample_names=sample_names,
        )
    except Exception as exc:  # noqa: BLE001
        return err_result(str(exc), source=source)
