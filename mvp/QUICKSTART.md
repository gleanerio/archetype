# MVP quickstart

Get the full pipeline running: **summon → S3 → Oxigraph + Elasticsearch → search UI**.

Assumes Docker (or compatible compose), Python ≥ 3.11, and network access to a sitemap source (default demo: **medin**).

## 1. Python env

```bash
cd mvp
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Services

You need three backends. Adjust `mvp_config.yaml` if your hosts/ports differ.

| Service | Default | Purpose |
|---------|---------|---------|
| S3-compatible store | `localhost:4566` (HTTP, keys `test`/`test`, bucket `gleanerio`) | JSON-LD objects |
| Oxigraph | `http://localhost:7878` | Named-graph RDF |
| Elasticsearch 8 | `http://localhost:9200` | Text search + UI |
| Browserless (optional) | `http://localhost:3000` | JS-rendered HTML for headless sources |

### Elasticsearch (included)

```bash
docker compose -f docker-compose.es.yaml up -d
curl -s http://localhost:9200   # expect cluster JSON
```

CORS is enabled for the browser UI.

### Browserless (optional headless summoner)

Only needed when a source has `headless: true` (JSON-LD injected after JS).

```bash
docker compose -f docker-compose.browserless.yaml up -d
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://localhost:3000/active?token=mvp-local-token"   # expect 204 or 200
```

Match `summoner.headless` / `headless_token` in `mvp_config.yaml` to the compose service (`TOKEN=mvp-local-token` by default).
### Oxigraph (example)

```bash
docker run --rm -d --name mvp-oxigraph -p 7878:7878 \
  ghcr.io/oxigraph/oxigraph --location /data serve --bind 0.0.0.0:7878
# or: podman / your existing container on :7878
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:7878/
```

### Object store (LocalStack / MinIO)

`mvp_config.yaml` defaults to LocalStack-style **port 4566**, `accessKey`/`secretKey` = `test`, bucket **`gleanerio`**.

Ensure the bucket exists (LocalStack often creates on first write; MinIO may need a one-time `mb`).

Smoke check from Python:

```bash
python - <<'PY'
from minio import Minio
c = Minio("localhost:4566", access_key="test", secret_key="test", secure=False)
print("buckets:", [b.name for b in c.list_buckets()])
PY
```

## 3. Harvest JSON-LD (summoner)

```bash
# small real run (writes to S3)
python -m summoner --config mvp_config.yaml --source medin --limit 5

# dry-run only (no S3 write)
python -m summoner --config mvp_config.yaml --source medin --limit 5 --dry-run -v
```

Objects land at:

```text
s3://gleanerio/summoned/medin/<sha1(page_url)>.json
```

Metadata on each object includes harvest page URL (`source-url`).

## 4. Load graph (scribe → Oxigraph)

```bash
python -m scribe --config mvp_config.yaml --source medin
```

Named graphs:

- data: `urn:gleaner:medin`
- prov: `urn:gleaner:prov:medin` (harvest URL ↔ S3 key ↔ optional `@id`)

Check data:

```bash
curl -s -X POST http://localhost:7878/query \
  -H 'Accept: application/sparql-results+json' \
  -H 'Content-Type: application/sparql-query' \
  --data 'SELECT (COUNT(*) AS ?c) WHERE { GRAPH <urn:gleaner:medin> { ?s ?p ?o } }'
```

Check provenance:

```bash
curl -s -X POST http://localhost:7878/query \
  -H 'Accept: application/sparql-results+json' \
  -H 'Content-Type: application/sparql-query' \
  --data 'PREFIX prov: <http://www.w3.org/ns/prov#> SELECT ?harvest ?s3key WHERE { GRAPH <urn:gleaner:prov:medin> { ?o prov:hadPrimarySource ?harvest ; prov:value ?s3key } } LIMIT 5'
```

## 5. Load search (indexer → Elasticsearch)

```bash
python -m indexer --config mvp_config.yaml --source medin
```

Index: `gleaner-medin`

Check:

```bash
curl -s 'http://localhost:9200/gleaner-medin/_count'
curl -s 'http://localhost:9200/gleaner-medin/_search' \
  -H 'Content-Type: application/json' \
  -d '{"query":{"multi_match":{"query":"topographic","fields":["name","description","keywords"]}},"_source":["name","url","source_url"]}'
```

## 6. Search UI

```bash
cd ui
python -m http.server 8080
```

Open **http://localhost:8080** and search (e.g. `topographic` or `coastal`).

Edit `ui/config.js` if Elasticsearch is not at `http://localhost:9200`.

## One-shot cheat sheet

```bash
cd mvp
source .venv/bin/activate

docker compose -f docker-compose.es.yaml up -d
# start Oxigraph + S3 if not already running

python -m summoner --config mvp_config.yaml --source medin --limit 5
python -m scribe   --config mvp_config.yaml --source medin
python -m indexer  --config mvp_config.yaml --source medin

cd ui && python -m http.server 8080
```

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| Summoner 403 on sitemap | Source blocks bots (e.g. Cloudflare). Try `medin`; `cioos` often fails. |
| Summoner finds pages, no JSON-LD | Page lacks `ld+json`, or needs `headless: true` + Browserless if JS-injected. |
| Headless 401 / connection refused | `docker compose -f docker-compose.browserless.yaml up -d`; match `headless_token` to compose `TOKEN`. |
| CIOOS / Cloudflare 403 | Open-source Browserless is not a bot bypass; use API path or allowlisting. |
| Scribe cannot connect | Oxigraph on `:7878`? `curl http://localhost:7878/` |
| Indexer connection refused | `docker compose -f docker-compose.es.yaml up -d` and wait until healthy |
| UI “Search failed” / CORS | Recreate ES with current compose (CORS uses `/.*/`). Serve UI via `http.server`, not `file://` |
| Empty ES after index | Confirm S3 has `summoned/<source>/` objects first |
| Wrong S3 endpoint | Match `objectstore` in `mvp_config.yaml` (port, ssl, keys, bucket) |

## What links what

| Field | Meaning |
|-------|---------|
| S3 key `summoned/{source}/{sha1}.json` | Deterministic from harvest page URL |
| S3 meta `source-url` | Harvest page summoner fetched |
| ES `source_url` | Same harvest URL (copied by indexer) |
| ES `url` | Schema.org resource/landing page from JSON-LD |
| ES / Oxigraph data graph | `urn:gleaner:{source}` |
| Oxigraph data triples | From JSON-LD body |
| Oxigraph prov graph | `urn:gleaner:prov:{source}` — `prov:hadPrimarySource` (harvest URL), `prov:value` (s3 key) |

More detail: [README.md](./README.md), [ui/README.md](./ui/README.md).
