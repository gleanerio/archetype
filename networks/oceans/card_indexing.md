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

__First, fun with bash__

[Shell Scraping](./shellScraping.md) describes using the UNIX shell environment to do quick easy
inspection of sitemaps and web pages with JSON-LD.

You can also look again at some of the tools in the [tooling page](../../docs/tooling.md)


__Gleaner.io__

* Indexing via cliGleaner.sh [quickstart](../../docs/quickstart.md)
* Nabu
    * Building graphs via cliNabu.sh   [quickstart](../../docs/quickstart.md)
        * Release graph concept [OIH Release Graph Development](https://github.com/iodepo/odis-arch/tree/master/graphOps/releaseGraphs) and Zenodo plans  [Ocean InfoHub Community](https://zenodo.org/communities/oceaninfohub)
        * Load to [Oxigraph](https://github.com/oxigraph/oxigraph)

* The _indexer_ persona is likely to conduct validation as well and may have other criteria.
    * Other options like Fuji, JSON schema, etc.
    * Validation
        * NOTEBOOK: [validationSHACL.ipynb](../commons/notebooks/validationSHACL.ipynb)
