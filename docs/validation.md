
# Discussions on Validating Graphs


# Validation Personas and  GO FAIR Implementation Network

![relations](./images/relations.png)


- IMPLEMENT  clearly defined plans and deliverables to implement an element of the Internet of FAIR Data and Services (IFDS) within a defined time period;


- FOSTER  a community of harmonized FAIR practices;


- COMMUNICATE  together on critical issues on which consensus has been reached and which are of generic importance for the community.


## RDF Conceptual Model

A brief tour of RDF conceptual mode, the RDF ecosystem and SHACL (and JSON-LD) in that ecosystem.

![relations](./images/ecosystem.png)


Image credit: Pierre-Antoine Champin  https://www.w3.org/Talks/2021/09-19-ddi-cdi/?full#rdf-ecosystem

## Role of Validation

The various personas can be seen described in [https://book.oceaninfohub.org/personas/persona.html](https://book.oceaninfohub.org/personas/persona.html).  These give an idea of some of the players in an implementation.  The relations between these persona are potential areas where the shape of the graph may be important for query or other functions.

Validation also helps to address application.  In particular the application of query to the graph.
**If we allow anything in "author" space, then we make the query in "user" space very complex** (to
deal with the variety).  The result can be poor performance and bad recovery.

# Validation Options

- JSON Schema
- ShEx
- SHACL
- Others (like Cue lang)

## Why SHACL?

SHACL is on a W3C recommendation track while ShEx is a community project.  SHACL has also shown wider adoption in the JSON-LD and broader structured data on the web community including Solid.


## A brief aside on JSON-LD Structure Validation

### Validate the structure of the JSON-LD data graph

These test that your document is well formed but not necessarily valid against a vocabulary or profile / guidance.

* [JSON-LD Playground](https://json-ld.org/playground/)
* [Structured data Linter](http://linter.structured-data.org/)


### Validates against Schema.org usage

This includes things like domain and range issues and predicate and type terms.

* [SDO Validator](https://validator.schema.org/)


## SHACL Resources

- [W3C SHACL](https://www.w3.org/TR/shacl/)
- [Editors Draft](https://w3c.github.io/data-shapes/shacl/)
- [Implementation Report](https://w3c.github.io/data-shapes/data-shapes-test-suite/)

You can try SHACL at the [SHACL Playground](https://shacl.org/playground/)


# Some example SHACL Shapes



Shape Graphs:

The SHACL Shapes Constraint Language, a language for validating RDF graphs against a set of conditions. These conditions are provided as shapes and other constructs expressed in the form of an RDF graph. RDF graphs that are used in this manner are called "shapes graphs"

Data Graphs:

In SHACL and the RDF graphs that are validated against a shapes graph are called "data graphs".

reference: [https://www.w3.org/TR/shacl/#sparql-constraints-example](https://www.w3.org/TR/shacl/#sparql-constraints-example)

## A quick example

This is a basic example but it shows things like checking for node type, min and max counts, setting severity and other aspects.  We can visit the [core constraints](https://www.w3.org/TR/shacl/#core-components) for SHACL to see some, but not, of the patterns SHACL can address.  More complex (or at least alternative) approaches include the SPARQL based on constraints or [SHACL Advanced Features](https://www.w3.org/TR/shacl-af/).

[GitHub resource link](https://github.com/iodepo/odis-arch/blob/master/book/tooling/notebooks/validation/shapes/oih_search.ttl)

```turtle
@prefix schema: <https://schema.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix shacl: <http://www.w3.org/ns/shacl#> .
@prefix oihval: <https://oceans.collaborium.io/voc/validation/1.0.1/shacl#> .

oihval:IDShape
a shacl:NodeShape ;
shacl:targetClass schema:Course ;
shacl:message "Graph must have an ID"@en ;
shacl:description "https://book.oceaninfohub.org/validation/README.html" ;
shacl:nodeKind shacl:IRI ;
.

oihval:DatasetCommonShape
a shacl:NodeShape ;
shacl:targetClass schema:Course ;
shacl:message "OIH Learning Resource validation suite" ;
shacl:description "https://book.oceaninfohub.org/validation/README.html" ;
shacl:property
oihval:nameResourceProperty,
oihval:urlResourceProperty,
oihval:descriptionResourceProperty,
oihval:identifierProviderProperty,
oihval:keywordsResourceProperty,
oihval:licenseResourceProperty
.

oihval:nameResourceProperty
a shacl:PropertyShape ;
shacl:path schema:name ;
shacl:nodeKind shacl:Literal ;
shacl:minCount 1 ;
shacl:message "Name is required "@en ;
shacl:description "https://book.oceaninfohub.org/validation/README.html" ;
.

oihval:keywordsResourceProperty
a shacl:PropertyShape ;
shacl:path schema:keywords ;
shacl:minCount 1 ;
shacl:nodeKind shacl:Literal ;
shacl:severity shacl:Warning ;
shacl:message "A resource should include descriptive keywords" ;
shacl:description "https://book.oceaninfohub.org/validation/README.html" ;
.

oihval:licenseResourceProperty
a shacl:PropertyShape ;
shacl:path schema:license ;
shacl:minCount 1 ;
shacl:nodeKind shacl:Literal ;
shacl:severity shacl:Info ;
shacl:message "Though not required, it is good practice to include a license if one exists" ;
shacl:description "https://book.oceaninfohub.org/validation/README.html" ;
.

oihval:urlResourceProperty
a shacl:PropertyShape ;
shacl:path schema:url ;
shacl:maxCount 1 ;
shacl:minCount 1 ;
shacl:nodeKind shacl:IRIOrLiteral ;
shacl:message "URL required for the location of the resource described by this metadata"@en ;
shacl:description "https://book.oceaninfohub.org/validation/README.html" ;
.

oihval:descriptionResourceProperty
a shacl:PropertyShape ;
shacl:path schema:description;
shacl:nodeKind shacl:Literal ;
shacl:minCount 1 ;
shacl:message "Resource must have a description"@en ;
shacl:description "https://book.oceaninfohub.org/validation/README.html" ;
.

oihval:identifierProviderProperty
a shacl:PropertyShape ;
shacl:path schema:provider;
shacl:minCount 1 ;
shacl:nodeKind shacl:IRIOrLiteral ;
shacl:message "A provider must be noted"@en ;
shacl:description "https://book.oceaninfohub.org/validation/README.html" ;
.

```

## Ensure one instance of a type

This example enforces a constraint that the data graph must contain at least one instance of the class ex:Person. The "trick" is to attach a constraint on the class itself, and then walk an inverse path along rdf:type triples to compute the count of instances.


ref: https://www.w3.org/wiki/SHACL/Examples

```turtle
ex:PersonCountShape
a sh:NodeShape ;
sh:targetNode ex:Person ;
sh:property [
sh:path [ sh:inversePath rdf:type ] ;
sh:minCount 1 ;
] .
```

## Tooling

pySHACL examples  ([https://github.com/RDFLib/pySHACL/](https://github.com/RDFLib/pySHACL/))

[kglab](https://derwen.ai/docs/kgl/) tutorial on [SHACL validation with pySHACL](https://derwen.ai/docs/kgl/ex5_0/)

```python
from pyshacl import validate
r = validate(data_graph,
shacl_graph=sg,
ont_graph=og,
inference='rdfs',
abort_on_first=False,
allow_warnings=False,
meta_shacl=False,
advanced=False,
js=False,
debug=False)
conforms, results_graph, results_text = r
```

## Severity

A brief note on severity levels.  SHACL defines [three levels of severity](https://www.w3.org/TR/shacl/#severity).  These can be useful to convey issues that are not violations for use, but are just warning and info related items.

| Severity     | Description                                                            |
|--------------|------------------------------------------------------------------------|
| sh:Info      | A non-critical constraint violation indicating an informative message. |
| sh:Warning   | A non-critical constraint violation indicating a warning.              |
| sh:Violation | A constraint violation.                                                |



## Linking Constraints to associate a data graph with a SHACL graph

Though there is no formal approach to this we can leverage the web architecture environment to do this.  One
possible approach would be to use something like the following:

The LDP specification introduces an IRI to be used to advertise any constraints on the ability of a client to create or update resources:

```
Link: <https://example.com/SpecificErrorCondition>; rel="http://www.w3.org/ns/ldp#constrainedBy"
```

```html
<link rel="http://www.w3.org/ns/ldp#constrainedBy" href="shape.jsonld">
```

This feature could potentially be used to accomplish a high level of interoperability across servers.

[https://www.w3.org/TR/ldp/#h-ldpr-gen-pubclireqs](https://www.w3.org/TR/ldp/#h-ldpr-gen-pubclireqs)

4.2.1.6 LDP servers must publish any constraints on LDP clients’ ability to create or update LDPRs, by adding a Link header with an appropriate context URI, a link relation of http://www.w3.org/ns/ldp#constrainedBy, and a target URI identifying a set of constraints [RFC5988], to all responses to requests that fail due to violation of those constraints. For example, a server that refuses resource creation requests via HTTP PUT, POST, or PATCH would return this Link header on its 4xx responses to such requests. The same Link header may be provided on other responses. LDP neither defines nor constrains the representation of the link's target resource. Natural language constraint documents are therefore permitted, although machine-readable ones facilitate better client interactions. The appropriate context URI can vary based on the request's semantics and method; unless the response is otherwise constrained, the default (the effective request URI) should be used.

Inbox URLs can announce their own constraints (e.g., SHACL, Web Annotation Protocol) via an HTTP Link header or body of the resource with a rel value of http://www.w3.org/ns/ldp#constrainedBy. Senders should comply with constraint specifications or the receiver may reject their notification and return an appropriate 4xx error code.

# Links to the OIH Notebooks for demonstration

## Examples of using pySHACL

[Basic SHACL](https://book.oceaninfohub.org/tooling/notebooks/validation/OIH_Simple_SHACL.html)



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


