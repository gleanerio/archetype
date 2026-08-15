from odis_explorer.graph import graph_from_items


def test_nested_publisher_and_catalog_become_edges():
    items = [
        {
            "id": "rec-1",
            "title": "Coral",
            "type": "Dataset",
            "url": "https://example.org/coral",
            "jsonld": {
                "@type": "Dataset",
                "@id": "https://example.org/coral",
                "name": "Coral",
                "publisher": {
                    "@id": "https://example.org/org",
                    "@type": "Organization",
                    "name": "Example Org",
                },
                "includedInDataCatalog": {
                    "@id": "https://obis.org",
                    "@type": "DataCatalog",
                    "url": "https://obis.org",
                },
            },
        }
    ]

    graph = graph_from_items(items)
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert "https://example.org/coral" in nodes
    assert nodes["https://example.org/coral"]["isRecord"] is True
    assert nodes["https://example.org/coral"]["recordId"] == "rec-1"
    assert nodes["https://example.org/org"]["label"] == "Example Org"
    assert nodes["https://obis.org"]["type"] == "DataCatalog"

    labels = {(edge["from"], edge["to"], edge["label"]) for edge in graph["edges"]}
    assert ("https://example.org/coral", "https://example.org/org", "publisher") in labels
    assert ("https://example.org/coral", "https://obis.org", "includedInDataCatalog") in labels


def test_shared_id_merges_across_records():
    items = [
        {
            "id": "a",
            "jsonld": {
                "@id": "https://example.org/a",
                "@type": "Dataset",
                "name": "A",
                "publisher": {"@id": "https://example.org/org", "@type": "Organization", "name": "Org"},
            },
        },
        {
            "id": "b",
            "jsonld": {
                "@id": "https://example.org/b",
                "@type": "Dataset",
                "name": "B",
                "publisher": {"@id": "https://example.org/org", "@type": "Organization"},
            },
        },
    ]
    graph = graph_from_items(items)
    org = next(node for node in graph["nodes"] if node["id"] == "https://example.org/org")
    assert org["label"] == "Org"
    assert set(org["recordIds"]) == {"a", "b"}


def test_blank_nodes_are_scoped_to_the_parent_record():
    items = [
        {
            "id": "one",
            "jsonld": {
                "@id": "https://example.org/one",
                "@type": "Dataset",
                "spatialCoverage": {"@type": "Place", "name": "Bay A"},
            },
        },
        {
            "id": "two",
            "jsonld": {
                "@id": "https://example.org/two",
                "@type": "Dataset",
                "spatialCoverage": {"@type": "Place", "name": "Bay B"},
            },
        },
    ]
    graph = graph_from_items(items)
    blanks = [node for node in graph["nodes"] if str(node["id"]).startswith("_:")]
    assert len(blanks) == 2
    assert {node["label"] for node in blanks} == {"Bay A", "Bay B"}
    assert blanks[0]["id"] != blanks[1]["id"]


def test_missing_jsonld_still_creates_a_record_node():
    graph = graph_from_items([{"id": "x", "title": "Orphan", "type": "Dataset"}])
    assert graph["nodes"][0]["id"] == "x"
    assert graph["nodes"][0]["label"] == "Orphan"
    assert graph["nodes"][0]["isRecord"] is True


def test_jsonld_without_id_uses_item_url():
    graph = graph_from_items(
        [
            {
                "id": "local-1",
                "url": "https://example.org/fallback",
                "jsonld": {"@type": "Dataset", "name": "Fallback"},
            }
        ]
    )
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert "https://example.org/fallback" in nodes
    assert nodes["https://example.org/fallback"]["isRecord"] is True
