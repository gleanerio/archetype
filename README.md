# Archetype

## About

A test of a set of tools that can be quickly used to form a KG from a 
a set of web based sources.

1.  Students mark-up a web page with schema.org JSON-LD including spatial event elements.
2.  Use Gleaner (pre-installed on the VM) to extract JSON-LD and load into a GeoSPARQL compliant triplestore (ideally, Fuseki)
3.  Make a few simple GeoSPARQL requests to the triplestore
4.  Possibly convert response from GeoSPARQL request to a format that can be used in QGIS

The main goal is to get the students working with spatial JSON-LD and to understand that using a tool like Gleaner, they can add JSON-LD to their data ecosystem without too much effort.

Thoughts:

* think of using json crack
* JSON-LD framing (for spatial)
* SHACL for checking for implementations

