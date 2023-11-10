#  Triplestore

## My commands

### Oxigraph

```bash
podman run --group-add keep-groups --privileged --rm -v $PWD/data:/data -p 7878:7878 ghcr.io/oxigraph/oxigraph --location /data serve --bind 0.0.0.0:7878
```

### GraphExplorer

```bash
podman run --group-add keep-groups  --env HOST=ghost.lan --privileged  -v ./config.json:/graph-explorer/config.json  -p 80:80 -p 443:443 -p 8182:8182 localhost/graph-explorer:latest
```

## Notes

* The system requires HTTPS support on all connections.  So using this in localhost
  dev setups can be problematic to resolve these issues.  
* The code appends /sparql to all URLs for SPARQL endpoints, this is an issue and 
  means the package can only be used easily with AWS Neptune or Blazegraph and a few 
  others.  Packages like GraphDB and Oxigraph will not work well, if at all.  

## Graph Explorer

```bash
docker run -p 80:80 -p 443:443 --env HOST={hostname-or-ip-address} -v /path/to/config.json:/graph-explorer/config.json graph-explorer`

podman run --group-add keep-groups  --env HOST=ghost.lan --privileged  -v ./config.json:/graph-explorer/config.json  -p 80:80 -p 443:443 localhost/graph-explorer:latest
```

## From the Oxigraph Documentation

Expose the server on port 7878 of the host machine, and save data on the local ./data folder

```bash
docker run --rm -v $PWD/data:/data -p 7878:7878 ghcr.io/oxigraph/oxigraph --location /data serve --bind 0.0.0.0:7878
```


You can then access it from your machine on port 7878:

### Open the GUI in a browser

firefox http://localhost:7878

### Post some data

```bash
curl http://localhost:7878/store?default -H 'Content-Type: text/turtle' -T ./data.ttl
```

### Make a query

```bash
curl -X POST -H 'Accept: application/sparql-results+json' -H 'Content-Type: application/sparql-query' --data 'SELECT * WHERE { ?s ?p ?o } LIMIT 10' http://localhost:7878/query
```

### Make an UPDATE

curl -X POST -H 'Content-Type: application/sparql-update' --data 'DELETE WHERE { <http://example.com/s> ?p ?o }' http://localhost:7878/update

