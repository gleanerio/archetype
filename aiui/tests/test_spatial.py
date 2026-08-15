from odis_explorer.spatial import (
    collect_geo,
    extract_spatial_from_jsonld,
    is_near_global,
    parse_polygon_string,
    spatial_for_item,
)


def test_api_points_and_boxes_are_passed_through():
    item = {
        "id": "rec",
        "title": "Coral",
        "type": "Dataset",
        "url": "https://example.org/coral",
        "source": {"id": "obis"},
        "spatial": {
            "boxes": [{"south": 25.0, "west": -80.2, "north": 26.2, "east": -80.0}],
            "points": [{"lat": 9.25, "lon": -82.13}],
        },
    }
    spatial = spatial_for_item(item)
    assert spatial["boxes"][0]["south"] == 25.0
    assert spatial["points"][0]["lat"] == 9.25

    geo = collect_geo([item])
    assert geo["recordsWithSpatial"] == 1
    assert geo["boxes"][0]["recordId"] == "rec"
    assert geo["points"][0]["title"] == "Coral"
    assert geo["boxes"][0]["nearGlobal"] is False


def test_null_spatial_falls_back_to_jsonld_geocoordinates():
    item = {
        "id": "rec",
        "title": "Site",
        "spatial": None,
        "jsonld": {
            "@type": "Dataset",
            "spatialCoverage": {
                "@type": "Place",
                "geo": {"@type": "GeoCoordinates", "latitude": 18.33, "longitude": -64.75},
            },
        },
    }
    spatial = spatial_for_item(item)
    assert spatial["points"] == [{"lat": 18.33, "lon": -64.75}]
    assert spatial["boxes"] == []
    assert spatial["polygons"] == []


def test_jsonld_polygon_keeps_the_ring():
    spatial = extract_spatial_from_jsonld(
        {
            "spatialCoverage": {
                "geo": {
                    "@type": "GeoShape",
                    "polygon": "25.591 -80.133, 25.591 -80.077, 26.164 -80.077, 26.164 -80.133, 25.591 -80.133",
                }
            }
        }
    )
    assert spatial["boxes"] == []
    assert len(spatial["polygons"]) == 1
    polygon = spatial["polygons"][0]
    assert polygon["south"] == 25.591
    assert polygon["west"] == -80.133
    assert polygon["north"] == 26.164
    assert polygon["east"] == -80.077
    assert polygon["coordinates"][0] == [25.591, -80.133]
    assert polygon["coordinates"][-1] == [25.591, -80.133]
    assert len(polygon["coordinates"]) == 5


def test_polygon_replaces_matching_api_box():
    item = {
        "id": "rec",
        "title": "Florida",
        "spatial": {"boxes": [{"south": 25.591, "west": -80.133, "north": 26.164, "east": -80.077}], "points": []},
        "jsonld": {
            "spatialCoverage": {
                "geo": {
                    "@type": "GeoShape",
                    "polygon": "25.591 -80.133, 25.591 -80.077, 26.164 -80.077, 26.164 -80.133, 25.591 -80.133",
                }
            }
        },
    }
    spatial = spatial_for_item(item)
    assert spatial["boxes"] == []
    assert len(spatial["polygons"]) == 1
    geo = collect_geo([item])
    assert geo["boxes"] == []
    assert geo["polygons"][0]["recordId"] == "rec"
    assert geo["polygons"][0]["nearGlobal"] is False


def test_irregular_polygon_is_not_reduced_to_a_rectangle():
    parsed = parse_polygon_string("10 0, 11 2, 9 3, 8 1, 10 0")
    assert parsed["kind"] == "polygon"
    assert parsed["coordinates"] == [[10, 0], [11, 2], [9, 3], [8, 1], [10, 0]]


def test_degenerate_polygon_becomes_a_point():
    parsed = parse_polygon_string(
        "-58.11666667 -43.008335, -58.11666667 -43.008335, -58.11666667 -43.008335"
    )
    assert parsed == {"kind": "point", "lat": -58.11666667, "lon": -43.008335}

    spatial = extract_spatial_from_jsonld(
        {"spatialCoverage": {"geo": {"@type": "GeoShape", "polygon": "-58.1 -43.0, -58.1 -43.0, -58.1 -43.0"}}}
    )
    assert spatial["polygons"] == []
    assert spatial["points"] == [{"lat": -58.1, "lon": -43.0}]


def test_near_global_boxes_are_flagged():
    assert is_near_global({"south": -31.5, "west": -170.7, "north": 33.3, "east": 178.9}) is True
    assert is_near_global({"south": 24.4, "west": -81.9, "north": 25.3, "east": -80.2}) is False


def test_missing_spatial_is_empty():
    geo = collect_geo([{"id": "x", "title": "No geo", "spatial": None}])
    assert geo["recordsWithSpatial"] == 0
    assert geo["points"] == []
    assert geo["boxes"] == []
    assert geo["polygons"] == []
