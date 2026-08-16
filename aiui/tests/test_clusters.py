from odis_explorer.clusters import MAX_CLUSTERS, clusters_from_items


def _item(record_id, *, title="Coral", source=None, jsonld=None):
    item = {"id": record_id, "title": title, "type": "Dataset"}
    if source is not None:
        item["source"] = source
    if jsonld is not None:
        item["jsonld"] = jsonld
    return item


def test_shared_publisher_becomes_org_cluster():
    items = [
        _item(
            "a",
            title="A",
            jsonld={
                "@type": "Dataset",
                "name": "A",
                "publisher": {"@id": "https://example.org/org", "@type": "Organization", "name": "Example Org"},
            },
        ),
        _item(
            "b",
            title="B",
            jsonld={
                "@type": "Dataset",
                "name": "B",
                "publisher": {"@id": "https://example.org/org", "@type": "Organization"},
            },
        ),
    ]
    payload = clusters_from_items(items)
    org = next(c for c in payload["clusters"] if c["kind"] == "org")
    assert org["label"] == "Example Org"
    assert set(org["recordIds"]) == {"a", "b"}
    assert set(payload["memberships"]["a"]) == {org["id"]}
    assert set(payload["memberships"]["b"]) == {org["id"]}


def test_shared_keyword_clusters_across_publishers():
    items = [
        _item(
            "a",
            jsonld={"@type": "Dataset", "keywords": ["Metagenomics"], "publisher": {"name": "Org A"}},
        ),
        _item(
            "b",
            jsonld={"@type": "Dataset", "keywords": ["metagenomics"], "publisher": {"name": "Org B"}},
        ),
    ]
    payload = clusters_from_items(items)
    keyword = next(c for c in payload["clusters"] if c["kind"] == "keyword")
    assert keyword["label"].lower() == "metagenomics"
    assert set(keyword["recordIds"]) == {"a", "b"}
    kinds = {c["kind"] for c in payload["clusters"]}
    assert "org" not in kinds


def test_record_can_belong_to_multiple_clusters():
    items = [
        _item(
            "a",
            jsonld={
                "@type": "Dataset",
                "keywords": ["coral"],
                "publisher": {"@id": "https://example.org/org", "name": "Shared Org"},
            },
        ),
        _item(
            "b",
            jsonld={
                "@type": "Dataset",
                "keywords": ["coral"],
                "publisher": {"@id": "https://example.org/org", "name": "Shared Org"},
            },
        ),
    ]
    payload = clusters_from_items(items)
    kinds = {c["kind"] for c in payload["clusters"]}
    assert {"org", "keyword"} <= kinds
    assert len(payload["memberships"]["a"]) >= 2
    assert len(payload["memberships"]["b"]) >= 2


def test_unique_keywords_do_not_form_clusters_but_record_nodes_remain():
    items = [
        _item("a", title="One", jsonld={"@type": "Dataset", "keywords": ["alpha"]}),
        _item("b", title="Two", jsonld={"@type": "Dataset", "keywords": ["beta"]}),
    ]
    payload = clusters_from_items(items)
    assert payload["clusters"] == []
    node_ids = {node["id"] for node in payload["graph"]["nodes"]}
    assert node_ids == {"a", "b"}
    assert payload["graph"]["edges"] == []


def test_missing_jsonld_still_clusters_by_source():
    items = [
        _item("a", title="Gone A", source={"id": "obis", "name": "OBIS"}),
        _item("b", title="Gone B", source={"id": "obis"}),
    ]
    payload = clusters_from_items(items)
    source = next(c for c in payload["clusters"] if c["kind"] == "source")
    assert source["label"] == "OBIS"
    assert set(source["recordIds"]) == {"a", "b"}


def test_keyword_cap_does_not_drop_org_or_catalog():
    shared_org = {"@id": "https://example.org/org", "name": "Keep Org"}
    items = []
    for index in range(MAX_CLUSTERS + 3):
        items.append(
            _item(
                f"left-{index}",
                jsonld={
                    "@type": "Dataset",
                    "publisher": shared_org,
                    "keywords": [f"term-{index}", "shared-kw"],
                },
            )
        )
        items.append(
            _item(
                f"right-{index}",
                jsonld={
                    "@type": "Dataset",
                    "keywords": [f"term-{index}"],
                },
            )
        )
    payload = clusters_from_items(items)
    assert len(payload["clusters"]) == MAX_CLUSTERS
    kinds = [c["kind"] for c in payload["clusters"]]
    assert "org" in kinds
    assert kinds[0] == "org" or any(c["kind"] == "org" for c in payload["clusters"])
    org = next(c for c in payload["clusters"] if c["kind"] == "org")
    assert org["label"] == "Keep Org"


def test_catalog_without_name_uses_host_label():
    items = [
        _item("a", jsonld={"@type": "Dataset", "includedInDataCatalog": {"@id": "https://obis.org"}}),
        _item("b", jsonld={"@type": "Dataset", "includedInDataCatalog": {"@id": "https://obis.org"}}),
    ]
    catalog = next(c for c in clusters_from_items(items)["clusters"] if c["kind"] == "catalog")
    assert catalog["label"] == "obis.org"


def test_cluster_graph_is_bipartite():
    items = [
        _item(
            "a",
            title="Alpha",
            jsonld={"@type": "Dataset", "includedInDataCatalog": {"@id": "https://obis.org", "name": "OBIS"}},
        ),
        _item(
            "b",
            title="Beta",
            jsonld={"@type": "Dataset", "includedInDataCatalog": {"@id": "https://obis.org"}},
        ),
    ]
    graph = clusters_from_items(items)["graph"]
    nodes = {node["id"]: node for node in graph["nodes"]}
    clusters = [node for node in graph["nodes"] if node.get("isCluster")]
    records = [node for node in graph["nodes"] if node.get("isRecord")]
    assert len(clusters) == 1
    assert {node["id"] for node in records} == {"a", "b"}
    assert nodes["a"]["label"] == "Alpha"
    assert all(edge["from"] == clusters[0]["id"] for edge in graph["edges"])
    assert {edge["to"] for edge in graph["edges"]} == {"a", "b"}
