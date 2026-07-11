from __future__ import annotations

import json

from indexer.extract import documents_from_jsonld_bytes, extract_document


def test_extract_simple() -> None:
    node = {
        "@context": "https://schema.org/",
        "@type": "Dataset",
        "@id": "https://example.org/d1",
        "name": "Example Dataset",
        "description": "A test description",
        "keywords": ["ocean", "temp"],
        "url": "https://example.org/d1.html",
    }
    doc = extract_document(
        node,
        source="medin",
        s3_key="summoned/medin/abc.json",
        graph="urn:gleaner:medin",
        source_url="https://example.org/page-harvested",
    )
    assert doc["name"] == "Example Dataset"
    assert doc["description"] == "A test description"
    assert doc["keywords"] == ["ocean", "temp"]
    assert doc["type"] == ["Dataset"]
    assert doc["id"] == "https://example.org/d1"
    assert doc["_id"] == "https://example.org/d1"
    assert doc["url"] == "https://example.org/d1.html"
    assert doc["source_url"] == "https://example.org/page-harvested"
    assert doc["jsonld"]["@type"] == "Dataset"


def test_extract_defined_term_keywords() -> None:
    node = {
        "@type": "Dataset",
        "name": "X",
        "keywords": [
            {"@type": "DefinedTerm", "name": "current", "termCode": "N01"},
            "waves",
        ],
    }
    doc = extract_document(node, source="m", s3_key="k.json", graph="urn:gleaner:m")
    assert "current" in doc["keywords"]
    assert "waves" in doc["keywords"]


def test_array_root_multiple_docs(read_fixture) -> None:
    # page_multi style: list of two objects
    body = json.dumps(
        [
            {"@type": "Organization", "name": "Org", "@id": "https://example.org/org"},
            {"@type": "Dataset", "name": "Data", "@id": "https://example.org/data"},
        ]
    )
    docs = documents_from_jsonld_bytes(
        body, source="medin", s3_key="summoned/medin/x.json", graph="urn:gleaner:medin"
    )
    assert len(docs) == 2
    names = {d["name"] for d in docs}
    assert names == {"Org", "Data"}


def test_url_list_takes_first() -> None:
    node = {"@type": "DataCatalog", "name": "C", "url": ["https://a.example/", "https://b.example/"]}
    doc = extract_document(node, source="m", s3_key="k.json", graph="urn:gleaner:m")
    assert doc["url"] == "https://a.example/"


def test_direct_jsonld_fixture(read_fixture) -> None:
    docs = documents_from_jsonld_bytes(
        read_fixture("direct.jsonld"),
        source="x",
        s3_key="summoned/x/1.json",
        graph="urn:gleaner:x",
    )
    assert len(docs) == 1
    assert docs[0]["name"] == "Direct JSON-LD"
