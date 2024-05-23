Authoring JSON-LD from existing data sources

- starting with CSV or Forms based input exported to CSV or YAML
- this implies starting with data sources that are semi-structured 
- using python as the base language, though that is not a constraint

There are a LOT of approaches:  see   https://www.w3.org/wiki/ConverterToRdf

- OpenRefine,Any23, LinkML, SchemaSheets (Uses LinkML)
- Simple template population with code (for RDF targets, can be validated with SHACL)
- declarative approaches
    - RML (extension of W3C Recommendation R2RML)

Principle: Planed migration
Goal:  Self sustainable approaches

Use established languages and libraries to the greatest extent possible and 
isolate dependencies.
