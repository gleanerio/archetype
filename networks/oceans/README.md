# Structured Data on the Web and the UN Ocean Decade

> Note:  This material is being prepared for a Dec 14th 2023 talk. So
> they are still in development (likely till Dec 13th) ;-)

## Introduction

In this session, we'll explore leveraging structured data on the web to establish a knowledge graph serving as a
comprehensive master data catalog for community resources. The discussion will showcase various strategies for
generating data productions that align with community objectives.

All this is done in the context of the UN Ocean Decade and this approach
demonstrates how a group could become a contributor to the Ocean Decade.
We will discuss the [ODIS Ocean InfoHub (OIH)](https://oceaninfohub.org/project-overview/)
as an example these approaches in development. This is also related to the
work of the [NSF funded DeCODER project](https://www.earthcube.org/decoder) and for this talk we will use
resource assocated with the
[Deep Ocean Observing Stragety (DOOS)](https://www.deepoceanobserving.org/).

| UNESCO / ODIS / Ocean InfoHub                                                                                             | NSF DeCODER                                                               |
|---------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [![Ocean InfoHub Intro Video](https://img.youtube.com/vi/KrxeZrPg0u8/0.jpg)](https://www.youtube.com/watch?v=KrxeZrPg0u8) | [![DeCoder](./assets/decoderLogo.png)](https://www.earthcube.org/decoder) |

Additionally, we'll delve into techniques for validating and analyzing this knowledge graph, framing these components as
part of a conceptualized "implementation network" akin to the principles outlined in the GoFAIR approach and developing
data products based on the resources described in the knowledge graph.

### Implementation Network

This approach is __not__ an instance of
a [FAIR Implementation Network](https://www.go-fair.org/implementation-networks/),
however, there are some similarities that make it worth raising the comparison.

The following image highlights some of the interactions between three personas; _Publisher_, _Indexer_ and _User and
Community_.
These are described in More detail in the [Personas Section](../../personas/README.md).  The primary goal here is to highlight that this is a __melding of social and technical elements__ into a continuous workflow. 

<img src="../../docs/images/relations.png" width="800">



### Other notes

I've placed a few supporting notes in the [appendix](./appendix.md).

# Activity

> GOAL: As part of this demo we will use open source tools to index JSON-LD from the web and 
> form a Knowledge Graph.  We will then use that graph to form new products and interact with them.

> NOTE:  What follows is the "project" part of the _Principles over Project_ approach above. Therefore, 
> we are now being prescriptive about how we implement the "principles"

> NOTE: The goal is that this demo can be run with the only pre-requisites
> being Docker, the ability to run command line scripts and optionally the ability to run
> Jupyter notebooks

## Define our environment

* introduction to our tool selection 
  * GleanerIO
      - Gleaner
      - Nabu
* define our sources (see notes.md)
    - identify our sources and show configuration files for gleaner and nabu
    - show [Ocean Catalog](https://catalogue.odis.org/) and example entry for [BCO-DMO](https://catalogue.odis.org/view/3287)
* set up our run environment
    - docker compose 
      - Minio
      - Oxigraph
      - Headless Chrome

## Let's just do it

* Source assessment 
    * NOTEBOOK: [sitemap_assay.ipynb](../commons/sitemap_assay.ipynb)
* Gleaner
    * indexing via cliGleaner.sh [quickstart](../../docs/quickstart.md)
* Nabu
    * building graphs via cliNabu.sh   [quickstart](../../docs/quickstart.md)
      * release graph concept [OIH Release Graph Development](https://github.com/iodepo/odis-arch/tree/master/graphOps/releaseGraphs) and Zenodo plans  [Ocean InfoHub Community](https://zenodo.org/communities/oceaninfohub)
      * load to [Oxigraph](https://github.com/oxigraph/oxigraph)
* Query with SPARQL
    * In Oxigraph UI
    * In jupyter with rdflib loading release graphs
        * NOTEBOOK: [sparql.ipynb](../commons/sparql.ipynb)
* [Tooling digression](../../docs/tooling.md) 
* Validation
    * NOTEBOOK: [validationSHACL.ipynb](../commons/validationSHACL.ipynb)
        * SHACL validate with SOSO, CDIF and OIH shape graphs
    * Other options like Fuji, JSON schema, etc.
* Building data products from the KG
    * Build an example data product NOTEBOOK: [mdpLite.ipynb](../commons/mdpLite.ipynb)
    * Demonstrate using DuckDB on a parquet product NOTEBOOK: [mdpDuckDB.ipynb](../commons/mdpDuckDB.ipynb)
    * Convert to a network and visualize it [example](https://github.com/iodepo/odis-arch/tree/schema-dev-df/graphOps/graphVisualization) NOTEBOOK: NOTEBOOK: kg2network.ipynb
    * Build a spatial product NOTEBOOK: mdp2spatial.ipynb
* Emerging activities
    * CODATA CDIF
    * ML/AI 

## Thanks


* Provide some points of contacts here for some of the projects mentioned
