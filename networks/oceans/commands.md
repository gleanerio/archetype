# Commands

> NOTE:  I use podman, which is a drop in replacement for docker.
> You will likely be using docker so simply replace _podman_ with 
> _docker_ in the following examples. 

## Setup
```Bash
> pwd 
.../archetype
> export PATH=$PATH:$(pwd)/bin
```


```Bash
> pwd
.../archetype/networks/commons
> podman-compose -f compose.yaml up
```

Run the web page and see if you can connect

```Bash
> pwd
.../archetype/networks/commons
> python -m http.server 8000
```

## Gleaner Phase

```Bash
> pwd
.../archetype/networks/oceans
> cliGleaner.sh -a podman -cfg gleanerconfig.yaml -setup
```

```Bash
> pwd
.../archetype/networks/oceans
> cliGleaner.sh -a podman -cfg gleanerconfig.yaml -source obis
```

* When indexing obis I got rejected to index due to settings in the robots.txt. I need to look into this and see what is
  up. --rude resolved this

```Bash
> pwd
.../archetype/networks/oceans
> cliGleaner.sh -a podman -cfg gleanerconfig.yaml -source obis -rude
```

```Bash
> docker run -it --entrypoint=/bin/sh minio/mc
```

```Bash
> mc alias set minio http://192.168.202.159:9000 minioadmin minioadmin
```

### A few notes on indexing

- robots.txt is honored and this means oceanexpert is very slow, do be kind out there
- headless vs embedded 
- sitegraphs


## Nabu Phase

### Release Graphs

```Bash
> cliNabu.sh  -a podman release --cfg nabuconfig.yaml  --prefix summoned/obis
```

could also make up the prov release graph

```Bash
> cliNabu.sh  -a podman release --cfg nabuconfig.yaml  --prefix prov/obis
```

See this at:  http://0.0.0.0:54321/browser/devbucket/

### Load to Oxigraph

```Bash
> cliNabu.sh  -a podman bulk  --cfg nabuconfig.yaml --prefix summoned/obis --endpoint oxigraph
```

or load a release graph already built

```bash
cliNabu.sh  -a podman object --cfg nabuconfig.yaml graphs/latest/bcodmo_release.nq --endpoint oxigraph
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



# Appendix

## curl load Oxigraph

Replace the contents

```bash
> curl -i  -X PUT -H 'Content-Type:text/x-nquads' --data-binary @oceanexperts_release.nq  http://localhost:7878/store
```

Insert the contents
```bash
> curl -i  -X POST -H 'Content-Type:text/x-nquads' --data-binary @oceanexperts_release.nq  http://localhost:7878/store
```
