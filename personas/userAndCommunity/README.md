# User & Community

## About

The user persona is mostly focused on those people or machines using the
generated knowledge graph or associated indexes.  This could be simple web
based search via search portals.  It could also include more advanced use
via workflows or other more programtic access.

The community persona represents the


## Valiation

For validation one of the better and easier tools to us the
[pySHACL](https://github.com/RDFLib/pySHACL) package.  There is
also the [Jena SHACL](https://jena.apache.org/documentation/shacl/index.html)
implementation that works well across platform.

A very good overview of some of the more mature SHACL
packags can be found at [W3C SHACL Test Suite and Implementation Report](https://w3c.github.io/data-shapes/data-shapes-test-suite/).

A simple example of a validation call using the pySHACL package follows.

```bash
pyshacl -s shapes/oih_search.ttl -sf turtle -df json-ld -f human ./datagraphs/test_org.json
```
