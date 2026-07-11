from __future__ import annotations

from scribe.convert import count_quad_lines, jsonld_to_nquads, merge_nquads


def test_jsonld_to_nquads_includes_graph(read_fixture) -> None:
    body = read_fixture("direct.jsonld")
    nq = jsonld_to_nquads(body, "urn:gleaner:medin")
    assert "urn:gleaner:medin" in nq
    assert count_quad_lines(nq) >= 1
    # Each data line should end with the graph IRI before the period
    data_lines = [ln for ln in nq.splitlines() if ln.strip() and not ln.startswith("#")]
    for line in data_lines:
        assert "<urn:gleaner:medin>" in line or "urn:gleaner:medin" in line


def test_merge_and_count() -> None:
    a = jsonld_to_nquads(
        '{"@context":"https://schema.org/","@type":"Thing","name":"A"}',
        "urn:gleaner:x",
    )
    b = jsonld_to_nquads(
        '{"@context":"https://schema.org/","@type":"Thing","name":"B"}',
        "urn:gleaner:x",
    )
    merged = merge_nquads([a, b])
    assert count_quad_lines(merged) == count_quad_lines(a) + count_quad_lines(b)
