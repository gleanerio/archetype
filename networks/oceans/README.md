# Oceans  (DOOS, DeCODER)

## Notes
* listen to data products catalog for inspiration

## About / Prolog

Placeholder for the Dec 14th session.

This work really describes a structure to support 
community needs and goals.  Its goal is the generation 
of the data products of value to the customers of the community.

It is sustained by providing a foundation for the engagement in 
and the use of those products by communities.  

## Social-technical implementation

* Intro to concept of implementation network (or not..  )

This is a social-technical implmentation, with both components
vital.  Aligning people to a mission and keepig them engaged
is vital. 

## Principles over Project

* Introduction to the principles
    * web architecture
    * structured data on the web (data on the web best practices)
    * Linked Open Data/ semantics

We present the technical component as a set of principles
that can have many implmentations or projects to realize them.  It 
is important to always focus on those principles over project

## Data in context

It is important to keep the logic in the data to the greatest
extent possible.  Logic in code is disconnected from the data
and increases the burden of maintaining the generation of the products.

## Goals

- address community needs and goals, ie perhaps FAIR at first
  - note that FAIR is a set of principles too, and mean different things to different groups
- data to product for customers (show data workflow diagram)
- engagement and growth through validation and use

## Activity workflow (demo) three act play

Act I  Problem
We have a community that wants to address FAIR and generate products to address
goals.  Data is in all over, community repos, generalist repos, websites,
catalogs, etc

Act II Solution
web architecture + structured data on the web + schema.org
This is easy to use, a commodity and can address these goals.
let's see this

Act II Future
where to go from here, DeCODER, OIH, etc.
do this, open to all, anyone can use what you do, you can too



* the personas
    * provider
    * indexer
    * consumer
    * community
    * show the relationships via my classic implementation network diagram
* the providers for this demo
    * DOOS based, BCO-DMO, edmo, etc
    * publishing JSON-LD + SOSO via data on the web best practices
* indexer details
    * the implementation of these (DeCODER, OIH)  (the "project" part of principles overs project)
    * the underlying data workflow
    * configure the implementation 
        * sources is the key  (I have the sitmap assay notebook)
        * gleaner / nabu config
* Just shut up and do it...
    * index
    * form the KG
        * search it
        * view it
        * release it (as a file)
        * make a release product
          * search it (duckdb)
        * make a graph network
          * visualize it
    * validate
        * note: avoid logic in code, keep the capactiy in the data
        * SHACL validate with SOSO shacl shapes
        * mention Fuji and FAIR too?

* the future 
    * revisit the data workflow diagram, this is where a community
    can being to think about the products needs to address the goals
    desired.  Those products may or may not be possible, but this 
    flow can help define those that are not enabled now and what is
    needed to realize them.
