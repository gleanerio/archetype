# Structured Data on the Web and the UN Ocean Decade

> Note:  This material is being prepared for a Dec 14th 2023 talk.  So 
> they are still in development (likely till Dec 13th) ;-)

## Introduction

In this session, we'll explore leveraging structured data on the internet to establish a knowledge graph serving as a
comprehensive master data catalog for community resources. The discussion will showcase various strategies for
generating data productions that align with community objectives.

All this is done in the context of the UN Ocean Decade and this approach
demonstrates how a group could become a contributor to the Ocean Decade.
We will discuss the [ODIS Ocean InfoHub (OIH)](https://oceaninfohub.org/project-overview/)
as an example these approaches in development. This is also related to the
work of the NSF funded DeCODER project and for this talk we will use
resource assocated with the
[Deep Ocean Observing Stragety (DOOS)](https://www.deepoceanobserving.org/).

Additionally, we'll delve into techniques for validating and analyzing this knowledge graph, framing these components as
part of a conceptualized "implementation network" akin to the principles outlined in the GoFAIR approach.

### Implementation Network

This approach is not an instance of a [FAIR Implementation Network](https://www.go-fair.org/implementation-networks/),
however there are some similarities
worth make the connection through.

We have broken down the following image with the concept of three persona
in the form of the _Publisher_, _Indexer_ and _User and Community_. More details
on these can be found in the [Personas Section](../../personas/README.md).

![relations](../../docs/images/relations.png)

### Ocean Infohub introduction

You can find more information on Ocean InfoHub at the [overview page](https://oceaninfohub.org/project-overview/). A
broad introduction to
the concept can be seen in the following video as well.

[![Ocean InfoHub Intro Video](https://img.youtube.com/vi/KrxeZrPg0u8/0.jpg)](https://www.youtube.com/watch?v=KrxeZrPg0u8)

## This talk as a Three Act Play

I will frame this session along the classic three act play structure

### Act I  Problem

How do communities of practice organize their desperate data and research
projects to generate the products and resources to support their goals.
We might call this "addressing FAIR" though that could risk disconnecting
this from specific research goals within a community.

### Act II Solution

Focus on the creation of a knowledge graph as a type of  "master data catalog" and
use that as a foundation to generate data products from. Also, we will explore the
knowledge graph as a foundation to define needed products and iterate/validate the
data workflow to generate those products

### Act III Future

During this phase, I aim to illustrate the potential directions that OIH and DeCODER are exploring. The primary
objective is to produce essential metadata and broad products, facilitating exploration within these domains. The
overarching goal is to empower the utilization of data to address community objectives.

## Boundary conditions

Given this context we can briefly set some boundaries on what
this talk will and will not be about.

### Is not

* This is not another review of structured data on the web, we have those; 
  * link to Adam's presentation in SOSO
  * some others 
* This is not a vocabulary review, see;
  * SOSO
  * schema.org
  * book.oceaninfohub.org
* This is not a review of JSON-LD as a means to serialize knowledge via
  RDF (a data model) + schema.org (a vocabulary), see;
  * json-ld site and the presentation link there

### Is

* This is a description of a socio-technical implementation
  to enable FAIR and allow a community to generate products to address 
  their data needs
* demonstration of web architecture as foundation for structured data
  on the web to build community knowledge graphs
* a review of the principles of such an architecture and a reference
  implementation of those principles

## Approaches

### Principles over projects

Our technical component is introduced as a collection of principles. These principles can be executed through various
implementations or projects. It's crucial to continually direct our attention to these principles rather than the
projects themselves.

### Data in context

It is important to keep the logic in the data to the greatest
extent possible. Logic in code is disconnected from the data
and increases the burden of maintaining the generation of the products.

## Activity workflow (demo draft)

### define our environment and set up things with Docker
* define our tools (GleanerIO, but could be other)
    - our tools (gleaner, nabu)
    - our system architecture (docker compose for minio et al)
    - link to docs
* define our sources (see notes.md)
    - link to configs, use as an example of what to look for
        - both gleaner and nabu
    - show [Ocean Catalog](https://catalogue.odis.org/)
      - Example entgry for [BCO-DMO](https://catalogue.odis.org/view/3287)
* set up our run environment via archetype
    - docker compose based  
    - why was archetype made? as a means to quickly test/demonstrate to providers for OIH
* show the data products workflow here to show what we are doing

### Let's just do it

* source selection
    * web architecture approach via sitemaps as a primary source
      * validate sitemaps with notebook
    * define configuration
* index (cliGleaner)
* make the release graphs (cliNabu)
* load them into the triplestore, but mention that is not needed as we can use a notebook
  * search it in oxigraph
* load the KG's into notebook and rdflib for local query
    * search it
    * view it
* Using the mdp notebook to build a release product
* search the release product with duckdb  (notebook)
* make a graph network
    * visualize it [example](https://github.com/iodepo/odis-arch/tree/schema-dev-df/graphOps/graphVisualization)
* make a geopackage
  * visualize with grids (notebook)
* validation notebook
    * SHACL validate with SOSO shacl shapes
    * mention Fuji and FAIR too?
* potential products: discuss here how the catalog can let us tap the variables
  and even the data distributions to marshall data as well.  
  We can form up parquet, geojson, geopackage, OGC geoapi, etc.
  Would be fun to show a query that pulls variables and distribution links to files.
* the future
    * revisit the data workflow diagram, this is where a community
      can being to think about the products needs to address the goals
      desired. Those products may or may not be possible, but this
      flow can help define those that are not enabled now and what is
      needed to realize them.
    * Mention Tom's ML work here
    * NOTE:  Mention CDIF here too

