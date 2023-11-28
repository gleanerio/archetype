# Structured Data on the Web and the UN Ocean Decade

## Introduction

This session will discuss the use of structured data on the web as a means
for a community to define a knowledge graph as a type of master 
data catalog of resources.  From this KG we will demonstrate 
potential approaches for the creation of data productions to 
support the goals of a community.  

We will also look at methods to validate and analyse this KG 
and look at how all these elements can be seen as a conceptualization 
of an _implementation network_ along the lines as defined in the 
GoFAIR approach. 

![relations](../../docs/images/relations.png)

TODO: discuss the personas of this image

All this is done in the context of the UN Ocean Decade and this approach
demonstrates how a group could become a contributor to the Ocean Decade. 
We will discuss the [ODIS Ocean InfoHub](https://oceaninfohub.org/project-overview/) 
as an example these approaches in development.  

[![Ocean InfoHub Intro Video](https://img.youtube.com/vi/KrxeZrPg0u8/0.jpg)](https://www.youtube.com/watch?v=KrxeZrPg0u8)

## Three Act Play 

I will frame this session along the classic three act play structure.

### Act I  Problem
How do communities of practice organize their desperate data and research
projects to generate the products and resources to support their goals.
We might call this "addressing FAIR" though that could risk disconnecting 
this from specific research goals within a community.

### Act II Solution
Focus on the creation of a KG as your "master data catalog" and 
use that as a foundation to generate data products from.  Also, 
as a foundation to define needed products and iterate/validate the 
data workflow to generate those products

### Act III Future
where to go from here, DeCODER, OIH, etc.
do this, open to all, anyone can use what you do, you can too

## Boundary conditions

Given this context we can briefly set some boundaries on what 
this talk will not and will be about.

### Is not

* This is not another review of structured data on the web
    - we have those, link to adams presentation in SOSO
* This is not a vocabulary review, see SOSO or schema.org in general
    or guidance like book.oceaninfohub.org
* This is not a review of JSON-LD as a means to serialize knowledge via
    RDF (a data model) + schema.org (a vocabulary)

### Is

* This is a description of a socio-technical implementation 
 to enable FAIR, but also the implementation network approach
 to enable a community to generate products to address their needs
* demonstration of web architecture as foundation for structured data
on the web to address FAIR
* this is a review of the principles of such an architecture
* this is a demonstration of an implementation of those principles


## Principles

### Principles over projects

We present the technical component as a set of principles
that can have many implementations or projects to realize them.  It 
is important to always focus on those principles over project

### Data in context

It is important to keep the logic in the data to the greatest
extent possible.  Logic in code is disconnected from the data
and increases the burden of maintaining the generation of the products.

## Activity workflow (demo draft) 

* define our tools (GleanerIO, but could be other)
    - our tools (gleaner, nabu)
    - our system architecture (docker compose for minio et al)
    - link to docs
* define out sources (edmo, others from OIH that index quickly)
    - link to configs, use as an example of what to look for
        - both gleaner and nabu
    - show Ocean Catalog, link to BCO-DMO entry
* set up our run environment via archetype
    - why was archetype made?  as a means to quickly test/demonstrate to providers for OIH
* show the data products workflow here to show what we are doing

At this point we should be ready to index.  Have this done ahead of time too, 
but go ahead and do it here for people.
    
* index
* make the release graphs
* load them into the triplestore, but mention that is not needed as we can use a notebook
* form the KG
    * search it
    * view it
* Using the mdp notebook, make a release product
* search it (duckdb)
* make a graph network
    * visualize it
* validate
    * SHACL validate with SOSO shacl shapes
    * mention Fuji and FAIR too?
* products: discuss here how the catalog can let us tap the variables
    and even the data distributions to marshall data as well.  
    We can form up parquet, geojson, geopackage, OGC geoapi, etc.
    Would be fun to show a query that pulls variables and distribution links to files. 
* the future 
    * revisit the data workflow diagram, this is where a community
    can being to think about the products needs to address the goals
    desired.  Those products may or may not be possible, but this 
    flow can help define those that are not enabled now and what is
    needed to realize them.
    * Mention Tom's ML work here 
    * NOTE:  Mention CDIF here too

