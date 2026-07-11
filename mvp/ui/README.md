# MVP search UI

Minimal HTML/JS search against Elasticsearch indexes produced by `indexer`.

## Run

1. Elasticsearch with CORS (see `../docker-compose.es.yaml`):

   ```bash
   cd ..
   docker compose -f docker-compose.es.yaml up -d
   ```

2. Index at least one source:

   ```bash
   cd ..
   source .venv/bin/activate
   python -m indexer --config mvp_config.yaml --source medin
   ```

3. Serve this folder:

   ```bash
   cd ui
   python -m http.server 8080
   ```

4. Open [http://localhost:8080](http://localhost:8080) and search (e.g. `topographic`).

Config: edit `config.js` if ES is not at `http://localhost:9200`.

## Result fields

| Field | Meaning |
|-------|---------|
| **name** / **description** | From JSON-LD (Schema.org) |
| **url** | Resource / landing page from JSON-LD `url` |
| **source_url** | Harvest page summoner fetched (S3 metadata → indexer) |
| **source** | Source name (`medin`, …) |
| **s3_key** | Object under `summoned/<source>/` |

The title link prefers `url`, then `source_url`, then `@id` if it is an `http(s)` URL.

## Provenance (how stages connect)

| Stage | Harvest page URL | Resource `@id` / `url` | Source graph |
|-------|------------------|------------------------|--------------|
| **S3** (summoner) | Yes — `x-amz-meta-source-url` + key = sha1(page) | Inside JSON-LD body | folder name |
| **Elasticsearch** | Yes — `source_url` (copied from S3 metadata) | `id`, `url` | `graph` = `urn:gleaner:{source}` |
| **Oxigraph** (scribe) | **No** (not stored as PROV yet) | RDF triples from body | named graph `urn:gleaner:{source}` |

So: S3 ↔ ES are joinable via `s3_key` and harvest URL; ES ↔ Oxigraph join best at **source** (`graph`) and **entity** (`@id`) when present. Harvest URL is not yet written into Oxigraph.
