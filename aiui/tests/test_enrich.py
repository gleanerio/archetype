from odis_explorer.server import enrich_search, configure_client
from odis_explorer.client import OdisSearchClient


class FakeClient(OdisSearchClient):
    def __init__(self) -> None:
        super().__init__(session=None)

    def get_record(self, record_id: str, *, raw: bool = True):
        if record_id == "missing":
            return None
        return {
            "id": record_id,
            "raw": {
                "jsonld": {
                    "@id": "https://example.org/ds",
                    "@type": "Dataset",
                    "name": "Coral",
                    "publisher": {
                        "@id": "https://example.org/org",
                        "@type": "Organization",
                        "name": "Org",
                    },
                    "spatialCoverage": {
                        "@type": "Place",
                        "geo": {"@type": "GeoCoordinates", "latitude": 10.0, "longitude": 20.0},
                    },
                }
            },
        }


def test_enrich_search_attaches_graph_and_geo(monkeypatch):
    configure_client()
    import odis_explorer.server as server

    monkeypatch.setattr(server, "_client", FakeClient())
    payload = {
        "total": 1,
        "facets": {"types": [], "sources": []},
        "items": [
            {
                "id": "rec-1",
                "title": "Coral",
                "type": "Dataset",
                "url": "https://example.org/ds",
                "spatial": None,
            }
        ],
        "page": 1,
        "size": 1,
    }
    out = enrich_search(payload)
    assert out["items"][0]["jsonld"]["@type"] == "Dataset"
    assert out["geo"]["recordsWithSpatial"] == 1
    assert out["geo"]["points"][0]["lat"] == 10.0
    ids = {node["id"] for node in out["graph"]["nodes"]}
    assert "https://example.org/ds" in ids
    assert "https://example.org/org" in ids


def test_enrich_search_survives_missing_record(monkeypatch):
    import odis_explorer.server as server

    monkeypatch.setattr(server, "_client", FakeClient())
    out = enrich_search(
        {
            "total": 1,
            "facets": {},
            "items": [{"id": "missing", "title": "Gone", "type": "Dataset"}],
            "page": 1,
            "size": 1,
        }
    )
    assert out["items"][0]["jsonld"] is None
    assert out["graph"]["nodes"][0]["label"] == "Gone"
