from __future__ import annotations

from unittest.mock import MagicMock

import httpx

from summoner.config import AppConfig, ObjectStoreConfig, SourceConfig, SummonerConfig
from summoner.crawl import SourceStats, _fetch_and_extract
from summoner.store import DryRunStore


def _app(hybrid: bool = True, headless_url: str = "http://localhost:3000") -> AppConfig:
    return AppConfig(
        objectstore=ObjectStoreConfig(
            address="localhost",
            port=4566,
            access_key="t",
            secret_key="t",
            ssl=False,
            bucket="b",
        ),
        summoner=SummonerConfig(
            headless=headless_url,
            headless_token="tok",
            headless_hybrid=hybrid,
            threads=1,
            delay=0,
        ),
        sources=[],
    )


def test_static_only_success() -> None:
    html = '''
    <html><script type="application/ld+json">
    {"@context":"https://schema.org/","@type":"Dataset","name":"A"}
    </script></html>
    '''

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    stats = SourceStats(name="x")
    source = SourceConfig(name="x", url="https://ex/s.xml", headless=False)
    result = _fetch_and_extract(
        page_url="https://ex/page",
        source=source,
        cfg=_app(),
        http_client=client,
        headless=None,
        stats=stats,
        stats_lock=__import__("threading").Lock(),
    )
    assert result is not None and result.ok
    assert stats.static_ok == 1
    assert stats.headless_ok == 0
    client.close()


def test_hybrid_fallback_to_headless() -> None:
    static_html = "<html><body>no ld</body></html>"
    rendered = '''
    <html><script type="application/ld+json">
    {"@context":"https://schema.org/","@type":"Thing","name":"FromJS"}
    </script></html>
    '''

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=static_html)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    headless = MagicMock()
    headless.render_html.return_value = rendered

    stats = SourceStats(name="x")
    source = SourceConfig(name="x", url="https://ex/s.xml", headless=True)
    result = _fetch_and_extract(
        page_url="https://ex/page",
        source=source,
        cfg=_app(hybrid=True),
        http_client=client,
        headless=headless,
        stats=stats,
        stats_lock=__import__("threading").Lock(),
    )
    assert result is not None and result.ok
    assert stats.hybrid_fallback == 1
    assert stats.headless_ok == 1
    assert (result.source or "").startswith("headless")
    headless.render_html.assert_called_once_with("https://ex/page")
    client.close()


def test_headless_only_when_hybrid_false() -> None:
    rendered = '''
    <html><script type="application/ld+json">
    {"@context":"https://schema.org/","@type":"Thing","name":"H"}
    </script></html>
    '''
    headless = MagicMock()
    headless.render_html.return_value = rendered
    # Static client should not be needed; if called, fail
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: (_ for _ in ()).throw(AssertionError("static")))
    )
    stats = SourceStats(name="x")
    source = SourceConfig(name="x", url="https://ex/s.xml", headless=True)
    result = _fetch_and_extract(
        page_url="https://ex/page",
        source=source,
        cfg=_app(hybrid=False),
        http_client=client,
        headless=headless,
        stats=stats,
        stats_lock=__import__("threading").Lock(),
    )
    assert result is not None and result.ok
    assert stats.static_ok == 0
    assert stats.headless_ok == 1
    client.close()


def test_dry_run_store_accepts_metadata() -> None:
    store = DryRunStore()
    key = store.put_jsonld(
        "s",
        "https://ex/p",
        {"@type": "Thing"},
        metadata={"fetch-mode": "headless"},
    )
    assert key.startswith("summoned/s/")
