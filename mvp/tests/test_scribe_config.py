from __future__ import annotations

from pathlib import Path

import pytest

from scribe.config import graph_iri, load_config


def test_load_config(fixtures_dir: Path) -> None:
    cfg = load_config(fixtures_dir / "scribe_config.yaml")
    assert cfg.objectstore.bucket == "gleanerio"
    assert cfg.objectstore.ssl is False
    assert cfg.triplestore.type == "oxigraph"
    assert cfg.triplestore.base_endpoint == "http://localhost:7878"


def test_graph_iri() -> None:
    assert graph_iri("medin") == "urn:gleaner:medin"
    assert graph_iri("bodc") == "urn:gleaner:bodc"
    assert graph_iri("  cioos ") == "urn:gleaner:cioos"


def test_graph_iri_empty() -> None:
    with pytest.raises(ValueError):
        graph_iri("   ")


def test_missing_triplestore(tmp_path: Path) -> None:
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
    with pytest.raises(ValueError, match="triplestore"):
        load_config(p)


def test_unsupported_store_type(tmp_path: Path) -> None:
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
triplestore:
  type: graphdb
  endpoint: http://localhost:7200
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="oxigraph"):
        load_config(p)
