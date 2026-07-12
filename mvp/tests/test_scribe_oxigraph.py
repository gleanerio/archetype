from __future__ import annotations

from unittest.mock import MagicMock, call

import httpx
import pytest

from scribe.oxigraph import (
    clear_graph,
    load_nquads,
    replace_graph_with_nquads,
    replace_graphs_with_nquads,
)


def test_clear_graph_posts_update() -> None:
    client = MagicMock()
    response = MagicMock()
    response.status_code = 204
    response.raise_for_status = MagicMock()
    client.post.return_value = response

    clear_graph("http://localhost:7878", "urn:gleaner:medin", client=client)

    client.post.assert_called_once()
    args, kwargs = client.post.call_args
    assert args[0] == "http://localhost:7878/update"
    assert kwargs["headers"]["Content-Type"] == "application/sparql-update"
    assert b"CLEAR SILENT GRAPH <urn:gleaner:medin>" in kwargs["content"]


def test_load_nquads_posts_store() -> None:
    client = MagicMock()
    response = MagicMock()
    response.status_code = 204
    response.raise_for_status = MagicMock()
    client.post.return_value = response

    load_nquads("http://localhost:7878/", "<a> <b> <c> <urn:gleaner:x> .\n", client=client)

    client.post.assert_called_once()
    args, kwargs = client.post.call_args
    assert args[0] == "http://localhost:7878/store"
    assert kwargs["headers"]["Content-Type"] == "application/n-quads"


def test_replace_graph_clear_then_load() -> None:
    client = MagicMock()
    response = MagicMock()
    response.status_code = 204
    response.raise_for_status = MagicMock()
    client.post.return_value = response

    replace_graph_with_nquads(
        "http://localhost:7878",
        "urn:gleaner:medin",
        "<s> <p> <o> <urn:gleaner:medin> .\n",
        client=client,
    )

    assert client.post.call_count == 2
    urls = [c.args[0] for c in client.post.call_args_list]
    assert urls[0].endswith("/update")
    assert urls[1].endswith("/store")


def test_replace_graphs_clears_both_then_loads() -> None:
    client = MagicMock()
    response = MagicMock()
    response.status_code = 204
    response.raise_for_status = MagicMock()
    client.post.return_value = response

    replace_graphs_with_nquads(
        "http://localhost:7878",
        ["urn:gleaner:medin", "urn:gleaner:prov:medin"],
        "<s> <p> <o> <urn:gleaner:medin> .\n",
        client=client,
    )

    # two CLEAR updates + one store
    assert client.post.call_count == 3
    urls = [c.args[0] for c in client.post.call_args_list]
    assert urls[0].endswith("/update")
    assert urls[1].endswith("/update")
    assert urls[2].endswith("/store")
    contents = [c.kwargs["content"] for c in client.post.call_args_list[:2]]
    assert any(b"urn:gleaner:medin" in c and b"CLEAR" in c for c in contents)
    assert any(b"urn:gleaner:prov:medin" in c for c in contents)
