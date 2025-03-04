#  Indexing


![visual](./assets/dt_indexing.svg)

## About

We are at the indexing phase.  Recall the foundation for this all this is the web 
architecture.  So, while we will be using the tools at [gleanerio](https://github.com/gleanerio)
there are other ways to do this.

Also, recall this is the foundation used by Google's [Dataset Search](https://datasetsearch.research.google.com/) as well, so implementing 
this approach allows multiple downstream users. 


## Details

__alternatives__

Take a look at [Alternative](https://book.oceaninfohub.org/indexing/alternatives.html) 
in the OIH Book.  

## Activity

let's index some sources!  

__First, some fun with bash__

[Shell Scraping](./shellScraping.md) describes using the UNIX shell environment to do quick easy
inspection of sitemaps and web pages with JSON-LD.

You can also look again at some of the tools in the [tooling page](../../docs/tooling.md)


__Gleaner.io__

* Indexing via cliGleaner.sh [quickstart](../../docs/quickstart.md)
* Nabu
    * Building graphs via cliNabu.sh   [quickstart](../../docs/quickstart.md)
    * Release graph concept [OIH Release Graph Development](https://github.com/iodepo/odis-arch/tree/master/graphOps/releaseGraphs) and Zenodo plans  [Ocean InfoHub Community](https://zenodo.org/communities/oceaninfohub)
    * Loading to [Oxigraph](https://github.com/oxigraph/oxigraph)

__validation__

We revisit validation here again.  This time as the indexing persona.  

* The _indexer_ persona is likely to conduct validation as well and may have other criteria.
  * See: [validation.md](..%2F..%2Fdocs%2Fvalidation.md)
  * Other options like [Fuji](https://github.com/pangaea-data-publisher/fuji), [JSON schema](https://json-schema.org/), etc.
  * __NOTEBOOK:__ [validationSHACL.ipynb](../commons/notebooks/validationSHACL.ipynb)


> Note: This is all being done manual for this demo and we often use this when working
> with new partners.  However, there is an automation approach we used both 
> in DeCODER and Ocean InfoHub called _scheduler_ in the GleanerIO which is an
> implemenaton of Dagster.  

