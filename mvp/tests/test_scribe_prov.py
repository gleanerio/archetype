from __future__ import annotations

from datetime import datetime, timezone

from scribe.config import activity_iri, agent_iri, object_iri, prov_graph_iri
from scribe.prov import build_prov_nquads, collect_entity_ids, sha_from_s3_key


def test_sha_from_s3_key() -> None:
    assert sha_from_s3_key("summoned/medin/abc123.json") == "abc123"
    assert sha_from_s3_key("summoned/medin/abc123.jsonld") == "abc123"


def test_collect_entity_ids_object() -> None:
    body = b'{"@id":"https://example.org/d1","@type":"Dataset","name":"X"}'
    assert collect_entity_ids(body) == ["https://example.org/d1"]


def test_collect_entity_ids_graph() -> None:
    body = b"""{
      "@context": "https://schema.org/",
      "@graph": [
        {"@id": "https://example.org/a", "@type": "Thing"},
        {"@id": "https://example.org/b", "@type": "Thing"},
        {"name": "no-id"}
      ]
    }"""
    assert collect_entity_ids(body) == [
        "https://example.org/a",
        "https://example.org/b",
    ]


def test_build_prov_nquads_shape() -> None:
    when = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    nq = build_prov_nquads(
        source="medin",
        s3_key="summoned/medin/deadbeef.json",
        data_graph="urn:gleaner:medin",
        prov_graph=prov_graph_iri("medin"),
        harvest_url="https://portal.example/page",
        entity_ids=["https://example.org/dataset/1"],
        when=when,
    )
    assert "urn:gleaner:prov:medin" in nq
    assert "https://portal.example/page" in nq
    assert "summoned/medin/deadbeef.json" in nq
    assert object_iri("medin", "deadbeef") in nq
    assert activity_iri("medin", "deadbeef") in nq
    assert agent_iri() in nq
    assert "hadPrimarySource" in nq
    assert "wasDerivedFrom" in nq
    assert "https://example.org/dataset/1" in nq
    assert "urn:gleaner:medin" in nq
    assert "2026-03-15T12:00:00Z" in nq
    # every line is in the prov graph
    for line in nq.splitlines():
        if line.strip():
            assert "<urn:gleaner:prov:medin>" in line


def test_build_prov_without_harvest_url() -> None:
    nq = build_prov_nquads(
        source="medin",
        s3_key="summoned/medin/abc.json",
        data_graph="urn:gleaner:medin",
        prov_graph="urn:gleaner:prov:medin",
        harvest_url=None,
        entity_ids=[],
    )
    assert "hadPrimarySource" not in nq
    assert object_iri("medin", "abc") in nq
    assert "summoned/medin/abc.json" in nq
