# MVP search UI

Minimal HTML/JS search against Elasticsearch indexes produced by `indexer`.

## Run

1. Elasticsearch with CORS (see `../build/docker-compose.es.yaml`):

   ```bash
   cd ..
   docker compose -f build/docker-compose.es.yaml up -d
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

## Theme (dark / light)

- Toggle in the header switches between light and dark.
- Preference is stored in `localStorage` under **`mvp-ui-theme`** (`"light"` | `"dark"`).
- On first visit (no stored value), the UI follows **`prefers-color-scheme`**.
- A small script in `index.html` applies the theme before CSS paint to avoid a flash.

## Result fields

| Field | Meaning |
|-------|---------|
| **name** / **description** | From JSON-LD (Schema.org) |
| **url** | Resource / landing page from JSON-LD `url` |
| **source_url** | Harvest page summoner fetched (S3 metadata → indexer) |
| **source** | Source name (`medin`, …) |
| **s3_key** | Object under `summoned/<source>/` |
| **jsonld** | Full harvested JSON-LD node (shown in per-result accordion) |

The title link prefers `url`, then `source_url`, then `@id` if it is an `http(s)` URL.

Each hit includes a small **Original JSON-LD** accordion under the description. Expanding it shows the document body stored by the indexer (same payload as in S3), plus the `s3_key` when present. No extra S3 round-trip is required.

## Provenance (how stages connect)

| Stage | Harvest page URL | Resource `@id` / `url` | Source graph |
|-------|------------------|------------------------|--------------|
| **S3** (summoner) | Yes — `x-amz-meta-source-url` + key = sha1(page) | Inside JSON-LD body | folder name |
| **Elasticsearch** | Yes — `source_url` (copied from S3 metadata) | `id`, `url` | `graph` = `urn:gleaner:{source}` |
| **Oxigraph data** (scribe) | via join to prov graph | RDF triples from body | `urn:gleaner:{source}` |
| **Oxigraph prov** (scribe) | Yes — `prov:hadPrimarySource` | `prov:wasDerivedFrom` `@id` when present | `urn:gleaner:prov:{source}` |

So: S3 ↔ ES join via `s3_key` / harvest URL; Oxigraph joins the same keys through the **prov** named graph (`prov:value` = s3 key, `prov:hadPrimarySource` = harvest URL) and content via entity `@id` or data graph `urn:gleaner:{source}`.
