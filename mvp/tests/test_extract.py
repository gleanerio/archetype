from __future__ import annotations

import json

from summoner.extract import dumps_jsonld, extract_from_html, extract_from_json_body, extract_jsonld


def test_single_script(read_fixture) -> None:
    result = extract_from_html("https://example.org/dataset/1", read_fixture("page_single.html"))
    assert result.ok
    assert result.source == "script-tag"
    assert result.data["@type"] == "Dataset"
    assert result.data["name"] == "Dataset One"


def test_multi_script(read_fixture) -> None:
    result = extract_from_html("https://example.org/", read_fixture("page_multi.html"))
    assert result.ok
    assert isinstance(result.data, list)
    assert len(result.data) == 2
    types = {item["@type"] for item in result.data}
    assert types == {"Organization", "Dataset"}


def test_cdata_script(read_fixture) -> None:
    result = extract_from_html("https://example.org/", read_fixture("page_cdata.html"))
    assert result.ok
    assert result.data["name"] == "CDATA Dataset"


def test_direct_jsonld(read_fixture) -> None:
    body = read_fixture("direct.jsonld")
    result = extract_from_json_body(
        "https://example.org/jsonld/3.json",
        body,
        "application/ld+json",
    )
    assert result.ok
    assert result.source == "json-body"
    assert result.data["name"] == "Direct JSON-LD"


def test_extract_jsonld_html_content_type(read_fixture) -> None:
    result = extract_jsonld(
        "https://example.org/dataset/1",
        read_fixture("page_single.html"),
        "text/html; charset=utf-8",
    )
    assert result.ok
    assert result.data["@type"] == "Dataset"


def test_extract_jsonld_json_content_type(read_fixture) -> None:
    result = extract_jsonld(
        "https://example.org/x.json",
        read_fixture("direct.jsonld"),
        "application/ld+json",
    )
    assert result.ok


def test_no_jsonld_in_html() -> None:
    html = "<html><body><p>No structured data</p></body></html>"
    result = extract_from_html("https://example.org/", html)
    assert not result.ok
    assert "no application/ld+json" in (result.error or "")


def test_dumps_roundtrip(read_fixture) -> None:
    data = json.loads(read_fixture("direct.jsonld"))
    raw = dumps_jsonld(data)
    assert json.loads(raw.decode("utf-8"))["name"] == "Direct JSON-LD"
