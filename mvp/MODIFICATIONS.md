# Modifications

This MVP is a small Python pipeline that stands in for Gleaner harvest and Nabu graph load. Three command-line programs share one object store. A static page searches Elasticsearch.

How to run the pipeline is in [README.md](./README.md) and [QUICKSTART.md](./QUICKSTART.md). This file is about design. It says what each part is good for, what it is bad at, and how you would replace it.

You can replace one stage if you keep the object-store contract described below. If you change that contract, you must change every consumer.

## The contract to keep

Stages do not call each other. They meet in S3 and in a few stable names.

| Join | Where it lives | Breaks if you |
|------|----------------|---------------|
| Harvest page URL | S3 metadata `source-url`, Elasticsearch `source_url`, PROV `prov:hadPrimarySource` | Drop object metadata |
| S3 key | Path `summoned/<source>/<sha1(url)>.json`, Elasticsearch `s3_key`, PROV `prov:value` | Change the key layout |
| Source name | S3 folder, graph `urn:gleaner:<source>`, index `gleaner-<source>` | Rename a source without a map |
| Entity `@id` | JSON-LD body, Elasticsearch `id`, PROV `prov:wasDerivedFrom` | Compact or frame the JSON-LD so `@id` is lost |

A replacement that writes the same keys and metadata can sit next to the current programs. Store HTML, hash by content, or drop metadata, and you must change scribe, indexer, provenance, and the UI.

---

## 1. Pipeline as a whole

### What it does here

Summoner harvests JSON-LD into S3. Scribe and indexer both read that prefix. Scribe fills Oxigraph. Indexer fills Elasticsearch. You run the three programs by hand.

### Virtues

- Each stage is a small package with a CLI, a dry-run flag, and unit tests.
- Scribe and indexer are independent. Either can fail without blocking the other.
- The object store is a buffer. You can re-load a source without crawling the web again.

### Vices

- Three packages copy the config parser and the S3 read code.
- Each load replaces the whole source. There is no incremental or diff mode.
- The source tree has no dedicated orchestrator (see [Agent layer](#14-agent--graph--tools-layer-orphaned)).

### If you change or replace it

Keep the three-stage shape and swap one backend at a time. That is the cheap path.

You can also collapse harvest and load into one process that writes local files. That is simpler for a laptop demo. You lose the ability to replay S3 into a new store.

A Makefile, a `just` file, or a restored non-LLM `graph` runner would replace the manual CLI sequence. Workflow tools (Prefect, Airflow) only pay off if you run many sources on a schedule.

If you add incremental harvest, you must stop clearing named graphs and deleting indexes. You will also need a stored crawl state (lastmod, etag, or content hash). That is a different program, closer to production Gleaner.

---

## 2. Configuration

### What it does here

`mvp_config.yaml` holds infrastructure: object store, Oxigraph, Elasticsearch, summoner crawl and Browserless settings. `sources.yaml` holds the harvest list. Each package parses the YAML it cares about into dataclasses.

### Virtues

- Infra and source list are split, so you can regenerate sources without touching endpoints.
- Browserless token can come from `BROWSERLESS_TOKEN`.
- Source records match the Gleaner-style fields (`name`, `url`, `sourcetype`, `headless`, `active`).

### Vices

- Access keys live in YAML. That is fine for local `test`/`test`. It is not fine for real buckets.
- Three parsers share names, not code. Each package defines its own `ObjectStoreConfig`.
- Config has `triplestore.type` and `search.type`, then rejects anything except `oxigraph` and `elasticsearch`.
- Scribe and indexer only use the source name after `--source`. They ignore the rest of `sources.yaml` at load time.

### If you change or replace it

Put secrets in the environment and keep YAML for hosts, ports, and source lists. Extract one shared config module so a key rename happens once.

If you want pluggable stores, make `type` select an implementation instead of failing. Until you do that, changing the YAML type field does nothing useful.

Watch the default path: every CLI looks for `mvp_config.yaml` next to `mvp/`. Rename that file and you break docs, tests, and leftover tools.

---

## 3. Object store

### What it does here

Summoner writes JSON-LD with the MinIO client to an S3-compatible endpoint (LocalStack, MinIO, AWS, or the sketch Floci compose). Keys are `summoned/<source>/<sha1(page_url)>.json`. User metadata carries `source-url` and `source-name`. Scribe and indexer list that prefix and fetch each object.

### Virtues

- S3 is portable. The same code can talk to a laptop store or to AWS.
- The key is deterministic from the harvest URL, so a re-crawl overwrites the same object.
- `ObjectWriter` is already a protocol. Dry-run is a second implementation, not a special case in the crawler.

### Vices

- Only the MinIO Python client talks to the store. Listing every key, then `stat` plus `get` per object, is slow at scale.
- Metadata values must be ASCII-safe. Non-ASCII URLs are percent-encoded.
- The object is not hashed by content. Two different JSON-LD bodies for the same URL collapse to one key.
- `build/docker-compose.floci.yaml` pins a host path. It is not a portable demo.

### If you change or replace it

The smallest change is the endpoint in `mvp_config.yaml`. Keep S3 and point at MinIO, LocalStack, or AWS.

A local filesystem (`summoned/<source>/*.json` plus a sidecar for the harvest URL) removes Docker for the store. You must then teach both readers the new layout. Elasticsearch and PROV still need `source-url`.

DuckDB or SQLite can hold JSON-LD and metadata in one file. That is pleasant for notebooks. It is a new contract. Scribe and indexer both reimplement S3 listing, so you change two readers, not one.

Do not change the `sha1(url)` key scheme unless you migrate existing objects and rewrite `s3_key` / `prov:value`. That join is how a search hit points back at the harvested file.

---

## 4. Summoner: discovery

### What it does here

For `sourcetype: sitemap`, summoner walks sitemap indexes (depth cap 5), collects page URLs, and de-duplicates them. For `sitegraph`, it fetches a JSON-LD ItemList or `@graph` and stores each item. Summoner caches robots.txt per host unless `--rude`.

### Virtues

- Nested sitemaps work. `--limit` stops nested fetches early, which is what smoke tests need.
- Sitegraph support matches sources that publish a graph file instead of a sitemap.
- Robots handling is the default, which is the right bias for a demo crawler.

### Vices

- Only sitemap and sitegraph. There is no HTML link crawl.
- No use of `lastmod`, etag, or sitemap changefreq. Every run is a full walk of the URL list (capped by `--limit`).
- A failed sitemap fetch returns an empty list. The source looks empty rather than failed.
- Sitegraph items often have no page URL. The key is then hashed from `@id` or the graph URL.

### If you change or replace it

Production harvest is still [Gleaner](https://github.com/gleanerio/gleaner). Use this Python summoner as a readable stand-in, not as a replacement at catalogue scale.

Other options: a CSV or newline file of URLs (skip sitemap parse), Scrapy, or a dump from Common Crawl. Downstream assumes one JSON-LD object per harvest URL. A crawler that stores HTML needs a separate extract step before S3.

If you invent a third `sourcetype`, add it next to sitemap and sitegraph in `crawl.py`. The crawler rejects any other type.

---

## 5. Summoner: fetch and JSON-LD extract

### What it does here

Summoner fetches each page with httpx (static) and, if needed, Browserless (headless). Extraction looks for `application/ld+json`: a JSON body, or `<script>` tags in HTML. Several blocks on one page become a JSON array. The extractor strips CDATA wrappers.

### Virtues

- Content-type drives the path, with HTML/JSON fallbacks when servers lie.
- Hybrid mode (default) tries static first and only renders when JSON-LD is absent.
- A thread pool plus a per-source delay keeps the crawl polite enough for demos.

### Vices

- No RDFa, microdata, or Open Graph. Pages without `ld+json` are misses.
- Summoner stores JSON-LD as harvested. There is no compact, expand, or frame step.
- The delay is per source process, not a global per-host budget across sources.
- HTTP 403 (Cloudflare and similar) is a hard miss. Headless does not fix that.

### If you change or replace it

`extruct` would add RDFa and microdata. You then have to decide what lands in S3. Indexer splits a JSON array into many Elasticsearch documents. Scribe parses the file as one JSON-LD document. If you change the stored shape, change both consumers in the same commit.

Playwright in-process can replace the Browserless HTTP client for fetch. Extraction can stay as it is. That is a local swap in `browserless.py` if you keep the `HeadlessRenderer` protocol.

Async httpx would raise throughput. It would also rewrite `crawl.py`. The thread pool is the simpler concurrency model and is good enough for `--limit` demos.

---

## 6. Headless (Browserless)

### What it does here

When a source has `headless: true`, summoner can `POST /chromium/content` to Browserless. The client waits for a JSON-LD script tag, blocks images and fonts, and caps concurrent renders. Compose is `build/docker-compose.browserless.yaml`.

### Virtues

- Opt-in per source. Static sites never pay for Chromium.
- Hybrid mode keeps Browserless as a fallback, not the default path.
- The docs are honest: this is not a bot-wall bypass.

### Vices

- Extra service, token, and `shm_size`. Chrome is unhappy on Docker's default shared memory.
- The REST content API is not a full browser session. Cookies, logins, and complex SPAs are out of scope.
- Queue full returns HTTP 429. You then lower `headless_concurrent` or raise the compose `CONCURRENT`/`QUEUED` values.

### If you change or replace it

Swap the client only. Keep `HeadlessRenderer.render_html(url) -> html`. Playwright, Puppeteer, or the commons stack headless Chrome on port 9222 can sit behind that call.

Skip JS sites instead. Many ocean catalogue sources embed JSON-LD in the first HTML. Headless is then unused.

Do not expect open-source Browserless to pass Cloudflare. For those hosts you need an API, an allowlist, or a different harvest path.

---

## 7. Scribe: JSON-LD to named graphs

### What it does here

Scribe reads summoned objects and converts each JSON-LD file to N-Quads with rdflib. It assigns graph `urn:gleaner:<source>`, CLEARs that graph and the prov graph, then POSTs the merged N-Quads to Oxigraph `/store`. Config will not accept another triplestore type.

### Virtues

- Named graphs keep sources apart. You can clear one source without touching others.
- Scribe skips bad JSON-LD per object. One broken file does not abort the load.
- Dry-run converts without touching Oxigraph.

### Vices

- Scribe holds the whole source in memory as merged N-Quads.
- rdflib expands `@context` from the network. There are no local Schema.org context maps (Nabu has those). Failed expansion looks like a bad object.
- CLEAR then POST is not atomic. If the bulk POST fails, the named graphs are empty.
- Oxigraph HTTP paths (`/update`, `/store`) and N-Quads MIME types are hard-coded.

### If you change or replace it

**Same store, different process.** [pyoxigraph](https://pypi.org/project/pyoxigraph/) embeds the store in Python and drops the Docker service. You still need a SPARQL URL if notebooks and curl checks should keep working.

**Different store.** The parent Nabu config already describes GraphDB, Jena, and Blazegraph bulk modes. QLever is a reasonable large-graph alternative. Each store wants its own clear syntax, bulk path, and content type. Copying `oxigraph.py` and renaming it is not enough.

**Nabu itself.** Use Nabu when you need release N-Quads under `graphs/`, or when you load several store types. This MVP scribe is the readable subset: one source, one Oxigraph, replace-all.

Add local context files before you chase random convert failures. Context drift is a common cause of empty graphs.

Oxigraph is a good local SPARQL store. It is not GraphDB. If you need GeoSPARQL as a product, pick a store that implements it and test the queries you care about.

---

## 8. Provenance

### What it does here

For each summoned object, scribe writes PROV-O into `urn:gleaner:prov:<source>`. The object IRI is `urn:gleaner:object:<source>:<sha>`. Links: harvest URL (`prov:hadPrimarySource`), S3 key (`prov:value`), optional JSON-LD `@id` (`prov:wasDerivedFrom`), data graph (`rdfs:seeAlso`), load activity, and software agent `urn:gleaner:agent:scribe`.

### Virtues

- Harvest URL is not in the data triples. PROV is how SPARQL joins a page to an entity.
- Same source name as the data graph, so the pair is easy to remember.

### Vices

- Each load rebuilds the prov graph from scratch. You do not keep prior harvests.
- N-Quads are hand-written, not built with rdflib.
- `prov:wasDerivedFrom` here means "object points at entity `@id`". A strict PROV reading of that predicate is easy to argue with.

### If you change or replace it

Keep PROV if you query harvest URL in SPARQL. The UI never reads this graph.

Sidecar JSON next to each S3 object is simpler to debug and does not need a triplestore. You lose SPARQL joins.

You can skip provenance. Then Elasticsearch `source_url` is the only remaining harvest-URL link, and only for search hits.

If you keep the predicate names, keep the meaning too. Changing `hadPrimarySource` without changing the README SPARQL examples will confuse the next reader.

---

## 9. Indexer: search facade and Elasticsearch

### What it does here

Indexer reads the same S3 prefix and builds one search document per JSON-LD node. Facade fields are `name`, `description`, `keywords`, `type`, `url`, and `source_url`. Elasticsearch stores `jsonld` without mapping it. Indexer then deletes `gleaner-<source>` and bulk-loads. Config accepts Elasticsearch only.

### Virtues

- A small mapped facade is enough for `multi_match` demos.
- Full JSON-LD on the hit means the UI does not need a second S3 fetch.
- `@graph` and arrays become several documents. DefinedTerm keywords flatten to strings.
- Replace-all is simple and idempotent for a demo source.

### Vices

- Elasticsearch 8 is heavy for this job (RAM, CORS, security off in compose).
- Mapping is Schema.org-ish text. No spatial, temporal, or completion fields.
- The browser talks to Elasticsearch directly.
- Replace-all drops any extra fields or synonyms you added by hand.

### If you change or replace it

**OpenSearch** is the closest API. Mapping and bulk should move with little pain. The UI query body can stay.

**Meilisearch or Typesense** are lighter for a demo UI. You rewrite the indexer client and the browser query. You keep the facade document shape.

**Postgres FTS, SQLite FTS5, or Solr** work if you already run those. You then want a small search API so the browser is not bound to one engine.

**Qdrant** (already in the parent commons stack) is the path if you want vectors over descriptions. That is a new index, not a drop-in for `multi_match`.

Document `_id` is the node `@id` when it is short enough, otherwise a hash, otherwise the S3 filename. Changing that rule affects updates if you ever stop deleting the index.

---

## 10. Search UI

### What it does here

`ui/` is static HTML, CSS, and JS. It POSTs Elasticsearch `_search` against `gleaner-*`, renders cards, and shows the stored JSON-LD. Title links prefer Schema.org `url`, then harvest `source_url`, then `@id` when it is `http(s)`.

### Virtues

- No build step. `python -m http.server` is enough.
- The original harvested JSON-LD is visible on the hit.
- Light and dark theme, with the preference stored in `localStorage`.

### Vices

- No server of its own. CORS must be on, and Elasticsearch must be reachable from the browser.
- `ui/config.js` is a host string. If it does not match compose, search fails with a CORS or network error.
- No filters, maps, SPARQL, or paging beyond `size`.

### If you change or replace it

Put a tiny API in front of Elasticsearch (or whatever search you pick). The browser then talks to one origin. You can turn CORS off on the search engine and add auth.

Query Oxigraph instead if SPARQL is the product. Faceted text search will get worse unless you keep a search index.

The parent repo has richer UIs (`aiui/`, GeoCodes-style search, Ocean InfoHub). Reuse those when the facade document is no longer enough.

If you drop Elasticsearch, this page has nothing to call. Replace it in the same change.

---

## 11. Local services (Compose)

### What it does here

`build/` has one compose file per service: Elasticsearch 8 on 9400, Oxigraph on 7878, Browserless on 3000. YAML points at the object store, usually LocalStack on 4566. There is no umbrella compose.

### Virtues

- You start only what a given stage needs.
- Ports are chosen so they do not collide with common local 9200/9000.

### Vices

- ES runs with security off and CORS open. Demo only.
- Oxigraph uses image tag `latest`.
- Floci compose is not a complete, portable object-store demo.
- `mvp_config.yaml` and `ui/config.js` both list ports and tokens.

### If you change or replace it

The parent `networks/commons/compose.yaml` already runs MinIO, Oxigraph, GraphDB, Qdrant, and headless Chrome. Point `mvp_config.yaml` at those ports if you want one stack for archetype and MVP.

Podman works if you keep the same published ports.

Cloud hosts work for S3 and for a remote triplestore. Then TLS, real keys, and network policy matter. The current compose flags will not.

Change a port in compose and in config in the same commit. A mismatch looks like a down service.

---

## 12. Source list

### What it does here

`make_sources.py` pulls https://catalogue.odis.org/odis-arch-records and writes `sources.yaml`. Git ignores that file. Names are slugs of the English dataset name. New records default to `active: true` and `headless: false`.

### Virtues

- The harvest list can track the public catalogue.

### Vices

- A clone does not contain a demo source list unless you generate or copy one.
- Every catalogue record is active. A full summoner run is a large crawl.
- Slug names can collide or become ugly. The generator writes the ODIS pid but does not use it as the S3 folder name.

### If you change or replace it

Commit a `sources.example.yaml` with one working demo source (medin is the documented one). Keep catalogue generation as an optional refresh.

Filter on `active` or on a tag if you generate from the catalogue. Summoner will crawl every active source if you omit `--source`.

---

## 13. Tests

### What it does here

`pytest` covers sitemap parse, JSON-LD extract, S3 key shape, N-Quads convert, PROV lines, Oxigraph HTTP helpers, and the Elasticsearch facade. Fixtures live under `tests/fixtures/`.

### Virtues

- Tests cover extract and convert without Docker. Those are the easy places to regress.

### Vices

- Almost no integration test against real S3, Oxigraph, or Elasticsearch.
- Agent and graph tests remain only as bytecode.

### If you change or replace it

Add a compose smoke test (limit 1, dry-run off, then SPARQL count and ES `_count`) before you trust a backend swap.

Current tests assume `summoned/<source>/<sha1>.json` and `urn:gleaner:<source>`. Change those names and update tests in the same change.

---

## 14. Agent / graph / tools layer (orphaned)

### What it does here

The tree has no Python source for `agents/`, `graph/`, and `tools/`. `__pycache__` shows the intended design: LangChain tools around the three libraries, a linear pipeline (`preflight → summon → scribe∥indexer → verify`), and a supervisor with specialist handoffs (OpenRouter, default Grok). Write tools defaulted to `dry_run=True`.

### Virtues of that design

- The linear pipeline does not need an LLM.
- Specialists match the real CLIs rather than inventing a parallel harvest.
- Dry-run by default is the correct bias when a model can CLEAR a graph.

### Vices

- Extra dependencies and an API key.
- Prompts and tool schemas drift from the CLIs the moment someone edits summoner without editing the tools.
- `--no-dry-run` on a supervisor is a loaded gun.

### If you change or replace it

Do not restore this from bytecode unless you want natural-language ops. Treat the pycache as a design note.

If you want orchestration, restore a non-LLM `python -m graph` or write a Makefile that calls the three CLIs. That is the useful part of the old layer.

---

## What this MVP does not do

Do not look for these here. They live in the parent archetype, in Gleaner/Nabu, or not at all:

- Incremental or diff harvest
- Gleaner mill
- Nabu release graphs under `graphs/`
- SHACL validation
- Several triplestore types in one config
- GeoSPARQL as a supported product
- A search UI beyond Elasticsearch `multi_match`

Those are fair extensions. They are not missing files in `mvp/`. They are a different scope.

## Suggested order of work

1. Change config and compose together when you move hosts or ports.
2. Swap a backend (Oxigraph, Elasticsearch, Browserless) behind the existing CLI.
3. Only then change the S3 key layout, metadata, or stored JSON-LD shape.
4. Add incremental load only after replace-all is no longer acceptable. That change touches scribe, indexer, and harvest state at once.
