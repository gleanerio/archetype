# CLAUDE.md

Guidance for AI assistants working in this repository.

## What this repository is

**GleanerIO Archetype** is a demonstrator and reference workspace for the *structured data on the web* workflow: publish Schema.org/JSON-LD, harvest it, form knowledge graphs, validate, and query.

It is **not** the Gleaner or Nabu source code. Core engines live in separate repos and are invoked here via Docker/Podman wrapper scripts under `bin/`.

- Origin: https://github.com/gleanerio/archetype
- Related: [gleanerio/gleaner](https://github.com/gleanerio/gleaner), [gleanerio/nabu](https://github.com/gleanerio/nabu)
- Concepts: [Data on the Web Best Practices](https://www.w3.org/TR/dwbp/), [Science on Schema.org](https://github.com/ESIPFed/science-on-schema.org), FAIR Implementation Networks

Originally planned as a “core model” provider instance; it evolved into a multi-persona workflow demonstrator (Publisher → Aggregator/Indexer → User & Community).

## Personas (design model)

| Persona | Role | Main paths |
|---------|------|------------|
| **Publisher** | Author JSON-LD, expose sitemaps on the web | `personas/publisher/` |
| **Aggregator (Indexer)** | Harvest JSON-LD (Gleaner), ETL to graphs (Nabu), deploy infra | `personas/aggregator/` |
| **User & Community** | Validate, query, notebooks, web UIs over the graph | `personas/userAndCommunity/` |

Personas are design archetypes, not mutually exclusive roles. Details: `personas/README.md`.

## Repository layout

```
archetype/
├── bin/                    # CLI wrappers & helpers (on PATH for demos)
│   ├── cliGleaner.sh       # Docker/Podman wrapper → nsfearthcube/gleaner
│   ├── cliNabu.sh          # Docker/Podman wrapper → fils/nabu
│   ├── cliPySHACL.sh       # Docker wrapper → ashleysommer/pyshacl
│   ├── github_jsonld_sitemap.py
│   ├── loadTriples/        # Load NQ/JSON-LD into triplestores
│   ├── releaseGraphs/      # Release-graph utilities
│   ├── sitemapCheck/       # Sitemap health checks
│   └── headless/           # Headless browser helpers
├── rundir/                 # Skeleton run config (gleaner + nabu YAML, schema.org context)
├── docs/                   # Quickstart, validation, tooling catalog, shell recipes
├── personas/               # Publisher / Aggregator / User materials
├── networks/               # Implementation-network demos
│   ├── commons/            # Shared compose stack (MinIO, Oxigraph, GraphDB, Qdrant, headless)
│   ├── oceans/             # Ocean Decade / ODIS-OIH oriented demo
│   └── inspire/            # Additional network notes
├── workbench/              # Local JSON-LD → Oxigraph + notebook experiment setup
├── topics/                 # Deep dives (metadata generation, workshops)
├── secret/                 # Local/private configs, logs, credentials — gitignored
├── logs/                   # Ad-hoc run logs
├── requirements.txt        # Light Python deps (polars, pandas, minio, pyshacl, PyGithub)
├── pyproject.toml          # Project metadata (Python ≥3.11)
└── VERSION                 # 0.1.0
```

## Core pipeline

```
Sitemap / sitegraph URLs
        │
        ▼
   Gleaner (summon)  ──JSON-LD──►  S3/MinIO  (prefix: summoned/<source>)
        │
        ▼
   Nabu (release | bulk | prefix)
        │
        ├─ release → N-Quads object under graphs/ prefix
        └─ bulk/prefix → SPARQL Update / bulk load into triplestore
        │
        ▼
   Oxigraph / GraphDB / Blazegraph / Jena  →  SPARQL, SHACL, notebooks, UIs
```

1. **Gleaner** visits publisher sitemaps (or sitegraphs), extracts JSON-LD, writes objects to an S3-compatible store.
2. **Nabu** reads those objects and either builds a release graph (N-Quads) or loads into a triplestore.
3. **Validation** is typically SHACL (pySHACL) against shapes in `personas/userAndCommunity/graphs/shapes/` or network-specific `shapegraphs/`.
4. **Use** via SPARQL, Jupyter notebooks, or web search UIs.

Headless (JS-rendered) indexing is limited; many demos assume embedded JSON-LD. See `docs/quickstart.md`.

## Prerequisites

- Docker **or** Podman
- Bash/zsh
- S3-compatible object store (local MinIO recommended for demos; AWS/GCS also supported)
- Optional: Python ≥3.11, Jupyter for notebooks

## Common commands

From repository root:

```bash
export PATH=$PATH:$(pwd)/bin

export MINIO_USE_SSL=true   # false for local MinIO without TLS
export MINIO_ACCESS_KEY=...
export MINIO_SECRET_KEY=...
```

### Local infrastructure (commons stack)

```bash
cd networks/commons
podman-compose -f compose.yaml up   # or docker compose
# Services: GraphDB :7200, Oxigraph :7878, Qdrant :6333, MinIO :9000/:54321, headless :9222
```

Default MinIO in compose: `minioadmin` / `minioadmin`.

### Gleaner

Run from a directory that has `gleanerconfig.yaml` (e.g. `rundir/` or `networks/oceans/rundir/`):

```bash
cliGleaner.sh -a docker -cfg gleanerconfig.yaml -setup
cliGleaner.sh -a docker -cfg gleanerconfig.yaml -source africaioc -rude
# -a podman also supported
# -rude: ignore robots.txt when needed (use sparingly; be kind to sources)
```

Docker image (wrapper): `nsfearthcube/gleaner:latest`.

### Nabu

Ensure Schema.org contexts exist (paths must match `contextmaps` in config):

```bash
mkdir -p assets && cd assets
curl -L -O https://schema.org/version/latest/schemaorg-current-https.jsonld
curl -L -O https://schema.org/version/latest/schemaorg-current-http.jsonld
```

```bash
docker pull fils/nabu:2.0.18-df-development   # match tag in bin/cliNabu.sh (NBIMAGE)
cliNabu.sh -a docker --cfg nabuconfig.yaml release --prefix summoned/sourcex
cliNabu.sh -a docker --cfg nabuconfig.yaml bulk --prefix summoned/sourcex --endpoint triplestore
cliNabu.sh -a docker --cfg nabuconfig.yaml prefix --prefix summoned/sourcex --endpoint triplestore
```

- **release**: ETL summoned JSON-LD → single N-Quads release under the configured bucket `graphs/` prefix  
- **bulk**: temporary aggregate + bulk load into triplestore (preferred over per-object **prefix**)  
- Tested endpoints: Blazegraph, Jena, Oxigraph, GraphDB

### SHACL

```bash
# Via wrapper (docker)
cliPySHACL.sh ...

# Or local pySHACL
pyshacl -s shapes/oih_search.ttl -sf turtle -df json-ld -f human ./datagraphs/test_org.json
```

Shapes live under `personas/userAndCommunity/graphs/shapes/` (e.g. Google recommended/required, SOSO, P418) and network-specific trees such as `networks/oceans/shapegraphs/`.

### Workbench (Oxigraph + notebooks)

```bash
# Example Oxigraph
podman run --rm -v $PWD/data:/data -p 7878:7878 ghcr.io/oxigraph/oxigraph \
  --location /data serve --bind 0.0.0.0:7878
```

See `workbench/README.md` for Graph Notebook / Graph Explorer notes.

## Configuration conventions

### `gleanerconfig.yaml`

Key sections:

- **minio**: `address`, `port`, `accessKey`, `secretKey`, `ssl`, `bucket`, `region` (region required for AWS; use region-specific endpoint, e.g. `s3.ca-central-1.amazonaws.com`)
- **gleaner**: `runid`, `summon`, `mill`
- **context / contextmaps**: local Schema.org JSON-LD context files
- **summoner**: `mode` (`full` | `diff`), `threads`, `delay`, `headless` URL
- **sources[]**: `name`, `url` (sitemap), `sourcetype`, `active`, `headless`, etc.

Credentials may be empty in YAML when provided via `MINIO_*` env vars (preferred for secrets).

### `nabuconfig.yaml`

- Same **minio** block style as Gleaner
- **contextmaps**: paths to schema.org contexts (often under `./assets/`)
- **endpoints[]**: named triplestore services with `modes` for `sparql`, `update`, and `bulk` (suffix, accept, method differ per store)

Skeleton templates: `rundir/gleanerconfig.yaml`, `rundir/nabuconfig.yaml`. Network-specific copies under `networks/*/rundir/` or `networks/commons/demorundir/`.

## Content types and data formats

| Kind | Formats | Typical locations |
|------|---------|-------------------|
| Data graphs | JSON-LD | `personas/.../datagraphs/`, `networks/*/datagraphs/`, `topics/.../examples/` |
| Shapes | Turtle (SHACL) | `**/shapes/`, `**/shapegraphs/` |
| Frames | JSON | `personas/userAndCommunity/graphs/frames/` |
| Configs | YAML | `rundir/`, `networks/*/`, `secret/` (local only) |
| Docs / demos | Markdown, Jupyter, Slidev | `docs/`, `networks/oceans/`, `topics/` |

Vocabulary focus: **Schema.org** (often via Science on Schema.org / OIH profiles), RDF, GeoSPARQL-capable stores.

## Python environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# deps: polars, pandas, minio, pyshacl, PyGithub
```

`pyproject.toml` declares `requires-python = ">=3.11"`; dependencies list is minimal—many demos rely on system tools and containers rather than a heavy Python package tree.

## What to edit vs leave alone

**Safe / intended to extend**

- Docs under `docs/`, `personas/`, `networks/*/README.md`, `topics/`
- Example JSON-LD, shapes, frames, SPARQL/notebook materials
- Skeleton configs in `rundir/` (keep secrets out of committed YAML)
- Helper scripts under `bin/` when improving demo ergonomics
- `docs/tooling.md` (curated tool list for the ecosystem)

**Do not commit**

- Anything under `secret/` (gitignored: credentials, private source configs, large dumps)
- Real `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` or endpoint passwords
- `rundir/logs/*`, `workbench/data/`, `networks/commons/output/`, `.venv/`, `.idea/`

**Treat carefully**

- `networks/oceans/slides/` and similar trees may contain large generated/node_modules-like trees—prefer not to bulk-regenerate or reformat them unless asked
- Docker image tags in `bin/cliGleaner.sh` / `bin/cliNabu.sh` (`GLIMAGE`, `NBIMAGE`)—changing them affects all demos

## Conventions when contributing

- Prefer **Docker or Podman** for Gleaner/Nabu so demos stay portable; document which engine you used (`-a docker` vs `-a podman`).
- Keep **principle over project**: document patterns (JSON-LD on the web, SHACL validation, personas) so examples can be swapped for other networks.
- Be respectful when indexing: robots.txt is honored by default; `-rude` is for demos only.
- Prefer **SHACL** for graph validation (W3C track; broader adoption in this community than ShEx).
- Recommended lightweight triplestore for local work: **Oxigraph** (see `docs/tooling.md`); GraphDB/others are fine when compose demos require them.
- Diagrams often use **D2** (`.d2` → `.svg` under `docs/images/` or network `assets/`).

## Documentation map

| Need | Start here |
|------|------------|
| Install & first Gleaner/Nabu run | `docs/quickstart.md`, `rundir/README.md` |
| Validation concepts & SHACL | `docs/validation.md` |
| Tool catalog (RDF, JSON-LD, viz, FAIR platforms) | `docs/tooling.md` |
| Shell recipes (sitemaps, scraping) | `docs/shellScraping.md` |
| Ocean Decade demo walkthrough | `networks/oceans/README.md`, `networks/oceans/commands.md` |
| Shared compose services | `networks/commons/compose.yaml` |
| Aggregator server architecture | `personas/aggregator/serverArch/` |
| Metadata generation (CSV→RDF, RML, Morph, SchemaSheets) | `topics/metadataGeneration/` |
| Local experiment workbench | `workbench/README.md` |

## External references (ecosystem)

- Ocean InfoHub / ODIS: https://oceaninfohub.org/, https://github.com/iodepo/odis-arch  
- DeCODER / EarthCube: https://www.earthcube.org/decoder  
- Nabu docs: https://github.com/gleanerio/nabu/tree/master/docs  
- Awesome KGC tools: https://github.com/kg-construct/awesome-kgc-tools  

## Working style for assistants

1. **Read before rewrite**: configs and demos are intentionally copy-adapted per network; prefer small, local edits over repo-wide renames.
2. **Secrets**: never invent real credentials; use placeholders and env vars.
3. **No silent dependency on `secret/`**: public docs and `rundir/` should remain runnable without private trees.
4. **Containers first**: when fixing Gleaner/Nabu workflows, change wrappers/configs here—not by assuming a local Go build unless the user has the engine repos checked out.
5. **Explain trade-offs** when recommending stores (Oxigraph vs GraphDB vs Blazegraph) or load paths (bulk vs prefix).
6. **Keep demos runnable with Docker + bash + optional Jupyter** when adding material under `networks/`.
