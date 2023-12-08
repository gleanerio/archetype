# TODO

* [ ] explore the depth approach, note this in the presentation as an example of the community process
* [ ] document the cli scripts pointing to specific docker images and potential issues there
* [ ] document my use of podman vs the typical use of docker
* [ ] add in the gihub repos for odis and decoder
* [ ] review use of https://towardsdatascience.com/the-new-best-python-package-for-visualising-network-graphs-e220d59e054e
* [ ] MDP code 
* [ ] qdrant workflow in a notebook, with loading and query

## Notes

```Bash
podman-compose -f compose.yaml up
```

Run the web page and see if you can connect

```Bash
python -m http.server 8000
```

```Bash
export PATH=$PATH:$(pwd)/bin
```

### Gleaner Phase

```Bash
cliGleaner.sh -a podman -cfg gleanerconfig.yaml -setup
```

```Bash
cliGleaner.sh -a podman -cfg gleanerconfig.yaml -source obis
```

* When indexing obis I got rejected to index due to settings in the robots.txt. I need to look into this and see what is
  up. --rude resolved this

```Bash
cliGleaner.sh -a podman -cfg gleanerconfig.yaml -source obis -rude
```

```Bash
docker run -it --entrypoint=/bin/sh minio/mc
```

```Bash
mc alias set minio http://192.168.202.159:9000 minioadmin minioadmin
```

#### A few notes on indexing

- robots.txt is honored and this means oceanexpert is very slow, do be kind out there
- headless vs embedded 
- sitegraphs


### Nabu Phase

#### Release Graphs

```Bash
 cliNabu.sh  -a podman release --cfg nabuconfig.yaml  --prefix summoned/obis
```

could also make up the prov release graph

```Bash
 cliNabu.sh  -a podman release --cfg nabuconfig.yaml  --prefix prov/obis
```

See this at:  http://0.0.0.0:54321/browser/devbucket/

#### Load to Oxigraph

```Bash
 cliNabu.sh  -a podman bulk  --cfg nabuconfig.yaml --prefix summoned/obis --endpoint oxigraph
```

At this  point you can visit http://0.0.0.0:7878/ and use a sparql query
like:

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT  ( COUNT( DISTINCT ?s) as ?count) ?type
WHERE
 {
     graph ?g {
         ?s rdf:type ?type .
     }
}
GROUP BY ?type
ORDER BY DESC(?count)
```




```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX schema: <https://schema.org/>

SELECT DISTINCT ?source ?type ?target ?sType ?tType
WHERE {
  graph ?g {
    ?source a ?sType .
    ?target a ?tType .
    ?source ?type ?target .
    FILTER((?sType) IN (schema:Person, schema:Organization, schema:Dataset, schema:Course, schema:Document))
    FILTER((?tType) IN (schema:Person, schema:Organization, schema:Dataset, schema:Course, schema:Document))
  }
}
```



## Appendix

### curl load Oxigraph

Replace the contents

```bash
curl -i  -X PUT -H 'Content-Type:text/x-nquads' --data-binary @oceanexperts_release.nq  http://localhost:7878/store
```

Insert the contents
```bash
curl -i  -X POST -H 'Content-Type:text/x-nquads' --data-binary @oceanexperts_release.nq  http://localhost:7878/store
```
