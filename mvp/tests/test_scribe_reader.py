from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from scribe.reader import list_jsonld_keys, source_prefix


def test_source_prefix() -> None:
    assert source_prefix("medin") == "summoned/medin/"


def test_list_jsonld_keys_filters() -> None:
    client = MagicMock()
    client.list_objects.return_value = [
        SimpleNamespace(object_name="summoned/medin/aaa.json"),
        SimpleNamespace(object_name="summoned/medin/notes.txt"),
        SimpleNamespace(object_name="summoned/medin/bbb.jsonld"),
        SimpleNamespace(object_name="summoned/medin/subdir/"),
    ]
    keys = list_jsonld_keys(client, "gleanerio", "medin")
    assert keys == [
        "summoned/medin/aaa.json",
        "summoned/medin/bbb.jsonld",
    ]
    client.list_objects.assert_called_once_with(
        "gleanerio", prefix="summoned/medin/", recursive=True
    )
