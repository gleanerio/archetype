from __future__ import annotations

from pathlib import Path

import pytest

from indexer.config import graph_iri, index_name, load_config


def test_load_config(fixtures_dir: Path) -> None:
    cfg = load_config(fixtures_dir / "indexer_config.yaml")
    assert cfg.objectstore.bucket == "gleanerio"
    assert cfg.search.type == "elasticsearch"
    assert cfg.search.base_endpoint == "http://localhost:9200"
    assert cfg.search.index_prefix == "gleaner"


def test_index_name() -> None:
    assert index_name("medin") == "gleaner-medin"
    assert index_name("BODC", "gleaner") == "gleaner-bodc"


def test_graph_iri() -> None:
    assert graph_iri("medin") == "urn:gleaner:medin"


def test_missing_search(tmp_path: Path) -> None:
    p = tmp_path / "cfg.yaml"
    p.write_text(
        """
objectstore:
  address: localhost
  port: 4566
  accessKey: a
  secretKey: b
  ssl: false
  bucket: b1
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="search"):
        load_config(p)
