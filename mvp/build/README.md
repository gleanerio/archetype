# MVP Docker services

Compose files for local demos. Run from the **`mvp/`** directory (parent of this folder) so paths and project names stay consistent:

```bash
cd mvp

# Elasticsearch (search / UI)
docker compose -f build/docker-compose.es.yaml up -d

# Oxigraph (scribe / SPARQL)
docker compose -f build/docker-compose.oxigraph.yaml up -d

# Browserless (optional headless summoner)
docker compose -f build/docker-compose.browserless.yaml up -d
```

| File | Service | Port | Used by |
|------|---------|------|---------|
| `docker-compose.es.yaml` | Elasticsearch 8 | 9400 | `indexer`, `ui/` |
| `docker-compose.oxigraph.yaml` | Oxigraph | 7878 | `scribe` |
| `docker-compose.browserless.yaml` | Browserless Chromium | 3000 | `summoner` when `headless: true` |

Object store (MinIO / LocalStack) is configured separately in `mvp_config.yaml` (default `localhost:4566`).
