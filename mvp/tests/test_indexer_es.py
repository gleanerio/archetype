from __future__ import annotations

from unittest.mock import MagicMock, patch

from indexer.elasticsearch_client import bulk_index, replace_index


def test_replace_index_deletes_then_creates() -> None:
    client = MagicMock()
    client.indices.exists.return_value = True
    replace_index(client, "gleaner-medin")
    client.indices.delete.assert_called_once_with(index="gleaner-medin")
    client.indices.create.assert_called_once()
    kwargs = client.indices.create.call_args.kwargs
    assert kwargs["index"] == "gleaner-medin"
    assert "mappings" in kwargs
    assert kwargs["mappings"]["properties"]["name"]["type"] == "text"
    assert kwargs["mappings"]["properties"]["jsonld"]["enabled"] is False


def test_bulk_index_pops_id() -> None:
    client = MagicMock()
    docs = [
        {
            "_id": "https://example.org/1",
            "name": "A",
            "source": "medin",
        }
    ]
    with patch("indexer.elasticsearch_client.helpers.bulk") as bulk:
        bulk.return_value = (1, [])
        success, errors = bulk_index(client, "gleaner-medin", docs)
    assert success == 1
    assert errors == 0
    actions = list(bulk.call_args[0][1])
    assert actions[0]["_id"] == "https://example.org/1"
    assert actions[0]["_source"]["name"] == "A"
    assert "_id" not in actions[0]["_source"]
