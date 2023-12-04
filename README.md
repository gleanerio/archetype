# GleanerIO: Archetype

[![FAIR checklist badge](https://fairsoftwarechecklist.net/badge.svg)](https://fairsoftwarechecklist.net/v0.2?f=31&a=32100&i=31100&r=133)

## About

This repository gives a basic set of tools and guides to allow someone to
get a feel for the structured data on the web approach. See the
[Data on the Web Best Practices](https://www.w3.org/TR/dwbp/) document for
details on this approach.

The examples here are intended as a way to quickly get a feel for the process
that is implemented to collect and work with the JSON-LD documents.

It was named _archetype_ originally since the plan was for it to be a core model 
with the fundamental characteristics, themes and motifs of a provider instance. 
However, it evolved from that to act more as a demonstrator for the workflow 
of an implementation across the range of personas. 

## Personas

[Personas](./personas/README.md)

## Scripts and code

We are developing the tooling in the _bin_ directory. 
Usually this is just added to your PATH as shown in the quickstart.

### Quick start

[Quick Start](./docs/quickstart.md)


## Implementation Networks

This is based on, but is not a direction implementation of, 
the [GoFAIR Implementation Networks](https://www.go-fair.org/implementation-networks/).

## Validation

[Validation](./docs/validation.md)


## Activity Flow

A rough draft of the activity flow.  This is very Gleaner centric at this time which is not
required. So you can assume that Gleaner and Nabu could be replaced by other services.  Indeed,
the S3 and graph stores are also very optional.  

![relations](./docs/images/activityFlow.svg)

## References

* [Schema.org for research data managers: a primer](https://www.inderscienceonline.com/doi/10.1504/IJBDM.2022.128449)
* [Data on the Web Best Practices](https://www.w3.org/TR/dwbp/)
* [Science on Schema](https://github.com/ESIPFed/science-on-schema.org//)
* [Ocean Best Practices on Schema](https://github.com/adamml/ocean-best-practices-on-schema)
* [FAIR software](https://fairsoftwarechecklist.net/v0.2/)

