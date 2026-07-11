from __future__ import annotations

from pathlib import Path

import pytest

from summoner.config import load_config


def test_load_config(fixtures_dir: Path) -> None:
    cfg = load_config(fixtures_dir / "sample_config.yaml")
    assert cfg.objectstore.address == "localhost"
    assert cfg.objectstore.port == 4566
    assert cfg.objectstore.ssl is False
    assert cfg.objectstore.base_url == "http://localhost:4566"
    assert cfg.objectstore.endpoint == "localhost:4566"
    assert cfg.summoner.threads == 2
    assert cfg.summoner.delay == 100
    assert cfg.summoner.user_agent == "test-summoner/0.1"
    assert len(cfg.sources) == 3


def test_select_active_sources(fixtures_dir: Path) -> None:
    cfg = load_config(fixtures_dir / "sample_config.yaml")
    active = cfg.select_sources()
    assert [s.name for s in active] == ["active_src", "headless_src"]


def test_select_by_name(fixtures_dir: Path) -> None:
    cfg = load_config(fixtures_dir / "sample_config.yaml")
    selected = cfg.select_sources("active_src")
    assert len(selected) == 1
    assert selected[0].url.endswith("sitemap.xml")


def test_select_inactive_by_name_returns_empty(fixtures_dir: Path) -> None:
    cfg = load_config(fixtures_dir / "sample_config.yaml")
    assert cfg.select_sources("inactive_src") == []


def test_ssl_https_base_url(tmp_path: Path) -> None:
    p = tmp_path / "cfg.yaml"
    p.write_text(
        """
objectstore:
  address: s3.example.com
  port: 443
  accessKey: a
  secretKey: b
  ssl: true
  bucket: bucket1
sources: []
""",
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.objectstore.base_url == "https://s3.example.com:443"


def test_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/mvp_config.yaml")
