from __future__ import annotations

from pathlib import Path

import pytest

from summoner.sitemap import collect_page_urls_from_text, parse_sitemap_xml


def test_parse_urlset(read_fixture) -> None:
    kind, locs = parse_sitemap_xml(read_fixture("urlset.xml"))
    assert kind == "urlset"
    assert locs == [
        "https://example.org/dataset/1",
        "https://example.org/dataset/2",
        "https://example.org/jsonld/3.json",
    ]


def test_parse_sitemap_index(read_fixture) -> None:
    kind, locs = parse_sitemap_xml(read_fixture("sitemap_index.xml"))
    assert kind == "sitemapindex"
    assert len(locs) == 2


def test_expand_index_offline(read_fixture, fixtures_dir: Path) -> None:
    nested = {
        "https://example.org/sitemaps/a.xml": read_fixture("nested_a.xml"),
        "https://example.org/sitemaps/b.xml": read_fixture("nested_b.xml"),
    }
    pages = collect_page_urls_from_text(
        read_fixture("sitemap_index.xml"),
        fetch_nested=lambda url: nested[url],
    )
    assert pages == [
        "https://example.org/a/1",
        "https://example.org/a/2",
        "https://example.org/b/1",
    ]


def test_invalid_xml() -> None:
    with pytest.raises(ValueError, match="Invalid XML"):
        parse_sitemap_xml("<not-closed")
