# ODIS Search Explorer

Local client for the public [ODIS Search](https://search-demo.odis.org/) API.

`odis-search.py` prints one page of hits as JSON. `odis_explorer` is a small local web UI that maps those hits and draws a force-directed graph from the JSON-LD on each record.

The remote service is not raw Elasticsearch. It is the FastAPI facade documented at <https://search-demo.odis.org/api/docs>.

## Install

```bash
cd aiui
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI

```bash
python odis-search.py "coral"
python odis-search.py "coral" --page 2 --size 10
python odis-search.py "coral" --source ocean-biodiversity-information-system
```

`--type` and `--source` are repeatable. If you omit `--type`, the CLI still asks for `Dataset`. There is no default source filter.

## Explorer UI

```bash
python -m odis_explorer --open
# or: python odis-explorer.py --open
```

Opens <http://127.0.0.1:8765/>. The page:

- searches `https://search-demo.odis.org/api/v1/search`
- plots `spatial.points` and `spatial.boxes` on a Leaflet map (Carto Positron, OSM fallback)
- fetches `GET /api/v1/records/{id}?raw=1` for the current page and unions the `jsonld` nodes into a force graph
- lists landing-page links in a table

Map, graph, and table share one selection. Only the current page is visualized (API max 50 hits).

```bash
python -m odis_explorer --port 8765
```

## Tests

```bash
pip install pytest
python -m pytest tests
```
