#  JSON-LD


![visual](./assets/dt_jsonld.svg)

## About

This document present a flow of concepts we would want to go over with respect to 
the authoring of JSON-LD documents.

See [appendix.md](appendix.md) for references on authoring JSON-LD leveraging schema.org.

## Details

__Sources__

Your metadata is likely already in some form.  This might be a relational model, 
it might be in RDF or even XML files in an object store.  It might also just 
be a CSV document or some other flat file.  In these case you would be 
looking at approaches to convert your existing model to the RDF + schema.org 
environment.  Recall JSON-LD is just a serialization of the RDF data model.  

Tool like those at [JSON-LD Developers](https://json-ld.org/#developers) are 
a great start. You can also look at the tools document for resources that can 
help in this translation.

You might also have your metadata in a service like DataCite.  In that case you 
might be able to leverage their [content negotiation](https://support.datacite.org/docs/datacite-content-resolver#supported-content-types) 
to pull your metadata on JSON-LD for inclusion in a page or in generating a 
graph. 


__Vocabulary__

OIH and DeCODER is focused on the use of [schema.org](https://schema.org).  OIH has 
also leveraged [geoSPARQL](https://www.ogc.org/standard/geosparql/) for spatial information.
Other languages you might leverage include [DCAT](https://www.w3.org/TR/vocab-dcat-3/).

As mentioned, see some of the resources in the [appendix.md](appendix.md) for more
details on authoring JSON-LD in schema.org.

This is also a good place to discuss the role of the community in helping to 
define the patterns and shapes in the structured data graphs.  An example of this
can be seen in the recent collaborative work between DeCODER and OIH on the 
topic of depth.  [Draft of that work](https://github.com/iodepo/odis-arch/blob/master/book/thematics/depth/index.md)

__Serialization__

With your metadata in hand and a vocabulary to map into the next step would be 
to develop a data workflow that generates the JSON-LD data graphs.  Again, 
look at some of the developer and translation tools in [tooling.md](..%2F..%2Fdocs%2Ftooling.md).

[Example OBIS record](./datagraphs/obis_ffd36d51df93af24a9f9b5f40dd79cd4924a9d8b.jsonld)
(try in JSON Crack)

__Publishing__

Once you have the pipeline to generate the data graphs you need to be able to place these into the
web pages leveraing the 

```HTML
<scipt type="application/ld+json>  [JSON-LD here]  </script>"
```
approach.  

If this is not possible you could use JavaScript to load the JSON-LD dynamically into the page
or generate a _sitegraph.json_.  The _sitegraph.json_ approach is a non-standards based approach
where your datagraphs are collected into a single JSON-LD file.  This is then made available 
for indexing.  This somewhat analogous to the data.gov guidance on data.json files 
[ref: https://resources.data.gov/resources/m-13-13-guidance/](https://resources.data.gov/resources/m-13-13-guidance/).

Since OIH is addressing a range of types, we leverage the scheme.org/ItemList approach like 
in the following.

```json
{
  "@context": "https://schema.org/",
  "@type": ["ItemList", "CreativeWork"],
  "@id": "https://example.org/id/graph/X",
  "name": "Resource collection for site X",
  "author": "Creator of the list",
  "itemListOrder": "https://schema.org/ItemListUnordered",
  "numberOfItems": 2,
  "itemListElement": [
    {
      "@type": "ListItem",
      "item": {
           "@id": "ID_for_this_metadata_record1",
           "@type": "Map",
            "@id": "https://example.org/id/XYZ",
            "name": "Name or title of the document",
            "description": "Description of the map to aid in searching",
            "url":  "https://www.sample-data-repository.org/creativework/map.pdf"
      }
    },
    {
      "@type": "ListItem",
      "item": {
           "@id": "ID_for_this_metadata_record2",
            "@type": "Course",
            "courseCode": "F300",
            "name": "Physics",
            "provider": {
                "@type": "CollegeOrUniversity",
                "name": "University of Bristol",
                "url": {
                    "@id": "/provider/324/university-of-bristol"
                }
            }
        }
    }
  ]
}
```

__Validation__

Groups like Science on Schema.org, CODATA, OIH and others often generate validation 
approaches.  For RDF this can be in the form of [SHACL](https://www.w3.org/TR/shacl/)
shape graphs.  There are many tools/implementation for each of these.  For this 
demo we will use the [pySHACL](https://github.com/RDFLib/pySHACL) package.  

See: [RFEADME.md](shapegraphs%2FRFEADME.md)

See: [validation.md](..%2F..%2Fdocs%2Fvalidation.md)

## Activity

JSON-LD brief overview with [json crack](https://jsoncrack.com/editor)
with an example from BCO-DMO or OBIS.  

__NOTEBOOK:__ [validationSHACL.ipynb](../commons/notebooks/validationSHACL.ipynb)

