"""Flatten ODIS spatial extents and leftover JSON-LD geometry for Leaflet."""

from __future__ import annotations

import re
from typing import Any

BOX_PATTERN = re.compile(
    r"^(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)$"
)
COORD_PAIR_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)")

# Boxes this wide/tall are drawn but excluded from fitBounds.
GLOBAL_LON_SPAN = 300.0
GLOBAL_LAT_SPAN = 140.0
BOX_MATCH_TOLERANCE = 1e-4


def is_near_global(box: dict[str, Any]) -> bool:
    try:
        south = float(box["south"])
        west = float(box["west"])
        north = float(box["north"])
        east = float(box["east"])
    except (KeyError, TypeError, ValueError):
        return False
    lon_span = abs(east - west)
    lat_span = abs(north - south)
    return lon_span >= GLOBAL_LON_SPAN or lat_span >= GLOBAL_LAT_SPAN


def _valid_lat_lon(lat: float, lon: float) -> bool:
    return abs(lat) <= 90 and abs(lon) <= 180


def _unwrap(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _empty_spatial() -> dict[str, list]:
    return {"boxes": [], "points": [], "polygons": []}


def _parse_box_string(raw: str) -> dict[str, float] | None:
    match = BOX_PATTERN.match(raw.strip())
    if not match:
        return None
    south, west, north, east = (float(part) for part in match.groups())
    if south > north or not _valid_lat_lon(south, west) or not _valid_lat_lon(north, east):
        return None
    if south == north and west == east:
        return None
    return {"south": south, "west": west, "north": north, "east": east}


def _coord_pairs(raw: str) -> list[tuple[float, float]] | None:
    pairs = COORD_PAIR_PATTERN.findall(raw.strip())
    if not pairs:
        return None
    coords: list[tuple[float, float]] = []
    for lat_raw, lon_raw in pairs:
        lat = float(lat_raw)
        lon = float(lon_raw)
        if not _valid_lat_lon(lat, lon):
            return None
        coords.append((lat, lon))
    return coords


def _bbox_from_coords(coords: list[tuple[float, float]]) -> dict[str, float]:
    lats = [lat for lat, _lon in coords]
    lons = [lon for _lat, lon in coords]
    return {
        "south": min(lats),
        "west": min(lons),
        "north": max(lats),
        "east": max(lons),
    }


def parse_polygon_string(raw: str) -> dict[str, Any] | None:
    """Parse a schema.org GeoShape polygon (lat lon pairs).

    Degenerate rings collapse to a point. Rings with fewer than three unique
    vertices are ignored. Otherwise the vertex list is kept for Leaflet.
    """
    coords = _coord_pairs(raw)
    if not coords:
        return None

    unique: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for pair in coords:
        if pair in seen:
            continue
        seen.add(pair)
        unique.append(pair)

    if len(unique) == 1:
        lat, lon = unique[0]
        return {"kind": "point", "lat": lat, "lon": lon}
    if len(unique) < 3:
        return None

    ring = list(coords)
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return {"kind": "polygon", "coordinates": [[lat, lon] for lat, lon in ring], **_bbox_from_coords(unique)}


def _parse_polygon_box(raw: str) -> dict[str, float] | None:
    parsed = parse_polygon_string(raw)
    if parsed is None or parsed.get("kind") != "polygon":
        return None
    return {
        "south": parsed["south"],
        "west": parsed["west"],
        "north": parsed["north"],
        "east": parsed["east"],
    }


def _point_from_geo(geo_obj: dict[str, Any]) -> dict[str, float] | None:
    lat_raw = lon_raw = None
    for key in ("latitude", "schema:latitude"):
        if key in geo_obj:
            lat_raw = _unwrap(geo_obj.get(key))
            break
    for key in ("longitude", "schema:longitude"):
        if key in geo_obj:
            lon_raw = _unwrap(geo_obj.get(key))
            break
    try:
        if lat_raw is None or lon_raw is None:
            return None
        lat = float(lat_raw)
        lon = float(lon_raw)
    except (TypeError, ValueError):
        return None
    if not _valid_lat_lon(lat, lon):
        return None
    return {"lat": lat, "lon": lon}


def extract_spatial_from_jsonld(jsonld: Any) -> dict[str, list]:
    """Pull GeoCoordinates / GeoShape leftovers out of a Schema.org node."""
    boxes: list[dict[str, float]] = []
    points: list[dict[str, float]] = []
    polygons: list[dict[str, Any]] = []
    seen_boxes: set[tuple[float, float, float, float]] = set()
    seen_points: set[tuple[float, float]] = set()
    seen_polygons: set[tuple[tuple[float, float], ...]] = set()

    def add_box(box: dict[str, float] | None) -> None:
        if not box:
            return
        key = (box["south"], box["west"], box["north"], box["east"])
        if key in seen_boxes:
            return
        seen_boxes.add(key)
        boxes.append(box)

    def add_point(point: dict[str, float] | None) -> None:
        if not point:
            return
        key = (point["lat"], point["lon"])
        if key in seen_points:
            return
        seen_points.add(key)
        points.append(point)

    def add_parsed_polygon(raw: str) -> None:
        parsed = parse_polygon_string(raw)
        if parsed is None:
            return
        if parsed["kind"] == "point":
            add_point({"lat": parsed["lat"], "lon": parsed["lon"]})
            return
        key = tuple((round(lat, 6), round(lon, 6)) for lat, lon in parsed["coordinates"])
        if key in seen_polygons:
            return
        seen_polygons.add(key)
        polygons.append(
            {
                "coordinates": parsed["coordinates"],
                "south": parsed["south"],
                "west": parsed["west"],
                "north": parsed["north"],
                "east": parsed["east"],
            }
        )

    def collect_geo(geo: Any) -> None:
        for geo_obj in _as_dict_list(geo):
            for box_key in ("box", "schema:box"):
                raw = _unwrap(geo_obj.get(box_key))
                if isinstance(raw, str):
                    add_box(_parse_box_string(raw))
            for polygon_key in ("polygon", "schema:polygon"):
                raw = _unwrap(geo_obj.get(polygon_key))
                if isinstance(raw, str):
                    add_parsed_polygon(raw)
            add_point(_point_from_geo(geo_obj))

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        for coverage_key in ("spatialCoverage", "schema:spatialCoverage", "workLocation", "schema:workLocation"):
            for place in _as_dict_list(node.get(coverage_key)):
                for geo_key in ("geo", "schema:geo"):
                    if geo_key in place:
                        collect_geo(place.get(geo_key))
                walk(place)
        for box_key in ("box", "schema:box"):
            raw = _unwrap(node.get(box_key))
            if isinstance(raw, str):
                add_box(_parse_box_string(raw))
        for polygon_key in ("polygon", "schema:polygon"):
            raw = _unwrap(node.get(polygon_key))
            if isinstance(raw, str):
                add_parsed_polygon(raw)
        add_point(_point_from_geo(node))
        for key, value in node.items():
            if key.startswith("@") or key in {
                "spatialCoverage",
                "schema:spatialCoverage",
                "workLocation",
                "schema:workLocation",
                "geo",
                "schema:geo",
            }:
                continue
            if isinstance(value, (dict, list)):
                walk(value)

    walk(jsonld)
    return {"boxes": boxes, "points": points, "polygons": polygons}


def _normalize_api_spatial(spatial: Any) -> dict[str, list]:
    result = _empty_spatial()
    if not isinstance(spatial, dict):
        return result

    for box in spatial.get("boxes") or []:
        if not isinstance(box, dict):
            continue
        try:
            normalized = {
                "south": float(box["south"]),
                "west": float(box["west"]),
                "north": float(box["north"]),
                "east": float(box["east"]),
            }
        except (KeyError, TypeError, ValueError):
            continue
        if not _valid_lat_lon(normalized["south"], normalized["west"]):
            continue
        if not _valid_lat_lon(normalized["north"], normalized["east"]):
            continue
        result["boxes"].append(normalized)

    for point in spatial.get("points") or []:
        if not isinstance(point, dict):
            continue
        try:
            normalized = {"lat": float(point["lat"]), "lon": float(point["lon"])}
        except (KeyError, TypeError, ValueError):
            continue
        if not _valid_lat_lon(normalized["lat"], normalized["lon"]):
            continue
        result["points"].append(normalized)

    for polygon in spatial.get("polygons") or []:
        if not isinstance(polygon, dict):
            continue
        coords = polygon.get("coordinates")
        if not isinstance(coords, list) or len(coords) < 4:
            continue
        ring: list[list[float]] = []
        valid = True
        for pair in coords:
            if not isinstance(pair, (list, tuple)) or len(pair) < 2:
                valid = False
                break
            try:
                lat = float(pair[0])
                lon = float(pair[1])
            except (TypeError, ValueError):
                valid = False
                break
            if not _valid_lat_lon(lat, lon):
                valid = False
                break
            ring.append([lat, lon])
        if not valid or len(ring) < 4:
            continue
        bbox = _bbox_from_coords([(lat, lon) for lat, lon in ring])
        result["polygons"].append({"coordinates": ring, **bbox})

    return result


def _boxes_equivalent(left: dict[str, float], right: dict[str, float]) -> bool:
    return all(
        abs(left[key] - right[key]) <= BOX_MATCH_TOLERANCE
        for key in ("south", "west", "north", "east")
    )


def _merge_points(*groups: list[dict[str, float]]) -> list[dict[str, float]]:
    merged: list[dict[str, float]] = []
    seen: set[tuple[float, float]] = set()
    for group in groups:
        for point in group:
            key = (round(point["lat"], 6), round(point["lon"], 6))
            if key in seen:
                continue
            seen.add(key)
            merged.append(point)
    return merged


def _merge_polygons(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[tuple[float, float], ...]] = set()
    for group in groups:
        for polygon in group:
            key = tuple((round(lat, 6), round(lon, 6)) for lat, lon in polygon["coordinates"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(polygon)
    return merged


def _boxes_not_covered_by_polygons(
    boxes: list[dict[str, float]],
    polygons: list[dict[str, Any]],
) -> list[dict[str, float]]:
    kept: list[dict[str, float]] = []
    seen: set[tuple[float, float, float, float]] = set()
    for box in boxes:
        key = (box["south"], box["west"], box["north"], box["east"])
        if key in seen:
            continue
        if any(_boxes_equivalent(box, polygon) for polygon in polygons):
            continue
        seen.add(key)
        kept.append(box)
    return kept


def spatial_for_item(item: dict[str, Any]) -> dict[str, list]:
    """Merge API extents with JSON-LD polygons when the raw node is attached."""
    from_api = _normalize_api_spatial(item.get("spatial"))
    from_jsonld = extract_spatial_from_jsonld(item.get("jsonld"))
    polygons = _merge_polygons(from_jsonld["polygons"], from_api["polygons"])
    points = _merge_points(from_api["points"], from_jsonld["points"])
    boxes = _boxes_not_covered_by_polygons(from_api["boxes"] + from_jsonld["boxes"], polygons)
    return {"boxes": boxes, "points": points, "polygons": polygons}


def item_meta(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    return {
        "recordId": item.get("id"),
        "title": item.get("title") or "(untitled)",
        "type": item.get("type") or "Record",
        "url": item.get("url"),
        "source": source.get("name") or source.get("id"),
    }


def _has_geometry(spatial: dict[str, list]) -> bool:
    return bool(spatial["points"] or spatial["boxes"] or spatial["polygons"])


def collect_geo(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build Leaflet-ready points, boxes, and polygons for a page of hits."""
    points: list[dict[str, Any]] = []
    boxes: list[dict[str, Any]] = []
    polygons: list[dict[str, Any]] = []
    records_with_spatial = 0

    for item in items:
        spatial = spatial_for_item(item)
        meta = item_meta(item)
        if _has_geometry(spatial):
            records_with_spatial += 1
        for point in spatial["points"]:
            points.append({**meta, **point})
        for box in spatial["boxes"]:
            boxes.append({**meta, **box, "nearGlobal": is_near_global(box)})
        for polygon in spatial["polygons"]:
            polygons.append({**meta, **polygon, "nearGlobal": is_near_global(polygon)})

    return {
        "points": points,
        "boxes": boxes,
        "polygons": polygons,
        "recordsWithSpatial": records_with_spatial,
        "recordCount": len(items),
    }
