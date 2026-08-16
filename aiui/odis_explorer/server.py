"""Local FastAPI sidecar: static explorer UI plus an enriched ODIS search proxy."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from odis_explorer.client import (
    DEFAULT_BASE_URL,
    MAX_PAGE_SIZE,
    OdisSearchClient,
    OdisSearchError,
)
from odis_explorer.clusters import clusters_from_items
from odis_explorer.graph import graph_from_items
from odis_explorer.spatial import collect_geo, spatial_for_item

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_WORKERS = 8

app = FastAPI(title="ODIS Search Explorer", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_client = OdisSearchClient()


def configure_client(*, base_url: str = DEFAULT_BASE_URL, backend: str = "elasticsearch") -> None:
    global _client
    _client = OdisSearchClient(base_url=base_url, backend=backend)


def _attach_jsonld(item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    enriched["jsonld"] = None
    record_id = item.get("id")
    if not record_id:
        return enriched
    try:
        record = _client.get_record(str(record_id), raw=True)
    except OdisSearchError:
        return enriched
    if not record:
        return enriched
    raw = record.get("raw") if isinstance(record.get("raw"), dict) else {}
    jsonld = raw.get("jsonld")
    if isinstance(jsonld, dict):
        enriched["jsonld"] = jsonld
    elif isinstance(record.get("raw"), dict) and "@type" in record["raw"]:
        enriched["jsonld"] = record["raw"]
    return enriched


def enrich_search(payload: dict[str, Any]) -> dict[str, Any]:
    items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
    enriched: list[dict[str, Any]] = []
    if items:
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(items))) as pool:
            futures = {pool.submit(_attach_jsonld, item): index for index, item in enumerate(items)}
            slots: list[dict[str, Any] | None] = [None] * len(items)
            for future in as_completed(futures):
                slots[futures[future]] = future.result()
        enriched = [item or items[index] for index, item in enumerate(slots)]

    for item in enriched:
        spatial = spatial_for_item(item)
        if spatial["boxes"] or spatial["points"] or spatial["polygons"]:
            item["spatial"] = spatial

    return {
        "total": payload.get("total", 0),
        "facets": payload.get("facets") or {"types": [], "sources": []},
        "items": enriched,
        "page": payload.get("page", 1),
        "size": payload.get("size", len(enriched)),
        "graph": graph_from_items(enriched),
        "clusters": clusters_from_items(enriched),
        "geo": collect_geo(enriched),
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    try:
        return _client.health()
    except OdisSearchError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc


@app.get("/api/search")
def search(
    q: Annotated[str | None, Query()] = None,
    types: Annotated[list[str] | None, Query()] = None,
    source: Annotated[list[str] | None, Query()] = None,
    sort: Annotated[str, Query()] = "relevance",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
    include_graph_fragments: Annotated[bool, Query()] = False,
) -> dict[str, Any]:
    try:
        payload = _client.search(
            q,
            types=types,
            sources=source,
            sort=sort,
            page=page,
            size=size,
            include_graph_fragments=include_graph_fragments,
        )
    except OdisSearchError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return enrich_search(payload)


@app.get("/api/record/{record_id:path}")
def record(record_id: str, raw: bool = True) -> dict[str, Any]:
    try:
        payload = _client.get_record(record_id, raw=raw)
    except OdisSearchError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc
    if payload is None:
        raise HTTPException(status_code=404, detail=f"Record not found: {record_id}")
    return payload
