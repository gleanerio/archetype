"""Fetch and parse JSON-LD sitegraphs (ItemList)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .extract import extract_jsonld

logger = logging.getLogger(__name__)

def collect_sitegraph_items(
    url: str,
    client: httpx.Client,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch a sitegraph URL and extract items from ItemList.
    
    Returns a list of dictionaries, each being a JSON-LD object.
    """
    logger.info("Fetching sitegraph: %s", url)
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch sitegraph %s: %s", url, exc)
        return []

    result = extract_jsonld(url, response.text, response.headers.get("content-type", ""))
    if not result.ok or not isinstance(result.data, dict):
        logger.error("Could not parse JSON-LD from %s: %s", url, result.error)
        return []

    data = result.data
    items: list[dict[str, Any]] = []

    # Handle ItemList
    types = data.get("@type", [])
    if isinstance(types, str):
        types = [types]
    
    if "ItemList" in types:
        elements = data.get("itemListElement", [])
        if not isinstance(elements, list):
            elements = [elements]
        
        for el in elements:
            if limit is not None and len(items) >= limit:
                break
            
            if isinstance(el, dict):
                # ListItem usually has 'item' property
                item = el.get("item")
                if isinstance(item, dict):
                    items.append(item)
                elif "@type" in el: # Maybe it's the item itself
                    items.append(el)
    else:
        # If it's not an ItemList, maybe it's just a single object or a @graph
        if "@graph" in data:
            graph = data["@graph"]
            if isinstance(graph, list):
                for item in graph:
                    if limit is not None and len(items) >= limit:
                        break
                    if isinstance(item, dict):
                        items.append(item)
        else:
            # Just treat the whole thing as one item if it looks like JSON-LD
            items.append(data)

    logger.info("Sitegraph %s -> %d item(s)", url, len(items))
    return items
