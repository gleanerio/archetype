from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock

from summoner.store import DryRunStore, S3Store, object_key, sha1_key


def test_sha1_key_stable() -> None:
    url = "https://example.org/dataset/1"
    assert sha1_key(url) == sha1_key(url)
    assert len(sha1_key(url)) == 40


def test_object_key() -> None:
    url = "https://example.org/dataset/1"
    key = object_key("cioos", url)
    assert key == f"summoned/cioos/{sha1_key(url)}.json"


def test_s3_put_jsonld() -> None:
    client = MagicMock()
    client.bucket_exists.return_value = True
    store = S3Store(client=client, bucket="gleanerio")
    store.ensure_bucket()
    key = store.put_jsonld(
        "cioos",
        "https://example.org/dataset/1",
        {"@context": "https://schema.org/", "@type": "Dataset", "name": "X"},
    )
    assert key.startswith("summoned/cioos/")
    assert key.endswith(".json")
    client.put_object.assert_called_once()
    kwargs = client.put_object.call_args
    assert kwargs[0][0] == "gleanerio"
    assert kwargs[0][1] == key
    assert kwargs[1]["content_type"] == "application/ld+json"
    data_arg = kwargs[0][2]
    assert isinstance(data_arg, BytesIO)


def test_dry_run_store() -> None:
    store = DryRunStore()
    key = store.put_jsonld("x", "https://example.org/a", {"@type": "Thing"})
    assert key == object_key("x", "https://example.org/a")
