from __future__ import annotations

import httpx
import pytest

from summoner.browserless import BrowserlessClient, HeadlessError


def test_content_url_with_token() -> None:
    c = BrowserlessClient(base_url="http://localhost:3000/", token="abc", concurrent=1)
    try:
        assert c.content_url == "http://localhost:3000/chromium/content?token=abc"
    finally:
        c.close()


def test_render_html_success() -> None:
    html = '<html><script type="application/ld+json">{"@type":"Thing"}</script></html>'

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "/chromium/content" in str(request.url)
        assert "token=secret" in str(request.url)
        body = request.read()
        assert b"https://example.org/page" in body
        return httpx.Response(200, text=html)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    bl = BrowserlessClient(
        base_url="http://browserless:3000",
        token="secret",
        client=client,
        concurrent=1,
        wait_for_ldjson=True,
        block_assets=True,
    )
    try:
        out = bl.render_html("https://example.org/page")
        assert out == html
    finally:
        bl.close()


def test_render_html_401() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    bl = BrowserlessClient(
        base_url="http://localhost:3000",
        token="bad",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        concurrent=1,
    )
    try:
        with pytest.raises(HeadlessError, match="401"):
            bl.render_html("https://example.org/")
    finally:
        bl.close()


def test_render_html_429() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="queued")

    bl = BrowserlessClient(
        base_url="http://localhost:3000",
        token="t",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        concurrent=1,
    )
    try:
        with pytest.raises(HeadlessError, match="429"):
            bl.render_html("https://example.org/")
    finally:
        bl.close()


def test_render_html_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="   ")

    bl = BrowserlessClient(
        base_url="http://localhost:3000",
        token="t",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        concurrent=1,
        wait_for_ldjson=False,
    )
    try:
        with pytest.raises(HeadlessError, match="empty"):
            bl.render_html("https://example.org/")
    finally:
        bl.close()


def test_browserless_from_config() -> None:
    from summoner.browserless import browserless_from_config
    from summoner.config import SummonerConfig

    assert browserless_from_config(SummonerConfig(headless="")) is None
    client = browserless_from_config(
        SummonerConfig(headless="http://localhost:3000", headless_token="x", headless_concurrent=2)
    )
    assert client is not None
    try:
        assert client.base_url == "http://localhost:3000"
        assert client.token == "x"
    finally:
        client.close()
