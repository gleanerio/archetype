# Validation

## Notes


```
curl http://ossapi.oceaninfohub.org/public/graphs/summonededmo_2023-02-21-06-26-50_release.rdf |  pyshacl -s shapeGraphs/googleRecommended.ttl -sf turtle -df n3 -f human -
```

## CLI approach

### pySHACL
Once you have pySHACL installed it's easy to leverage it directly from the command line.  

For command line use:
_(these example commandline instructions are for a Linux/Unix based OS)_
```bash
$ pyshacl -s /path/to/shapesGraph.ttl -m -i rdfs -a -j -f human /path/to/dataGraph.ttl
`````
Where
 - `-s` is an (optional) path to the shapes graph to use
 - `-e` is an (optional) path to an extra ontology graph to import
 - `-i` is the pre-inferencing option
 - `-f` is the ValidationReport output format (`human` = human-readable validation report)
 - `-m` enable the meta-shacl feature
 - `-a` enable SHACL Advanced Features
 - `-j` enable SHACL-JS Features (if `pyhsacl[js]` is installed)

For detailed CLI usage of pySHACL visit [https://github.com/rdflib/pyshacl](https://github.com/rdflib/pyshacl)

### REST alternative (tangram.gleaner.io)

An instance of pySHACL is exposed at tangram.gleaner.io.   Through this you can use simple web clients to interact with pySHACL, like curl.

As example of that follows:

```
curl -F  'datagraph=@./datagraphs/dataset-minimal-BAD.json-ld'  -F  'shapegraph=@./shapegraphs/googleRecommended.ttl' -F 'format=machine'  https://tangram.gleaner.io/uploader 
```
        
Here, a data graph and a shape graph are uploaded and processed by pySHACL.  You can set the format to _human_ or _machne_ depending on the result style you need.  The target URL for this at the end of the command.   You can simply visit 
[https://tangram.gleaner.io](https://tangram.gleaner.io) for usage information too.  


