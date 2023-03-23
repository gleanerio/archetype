# Notes on getting Zenodo to do what I want



## Validation via schema

Using the Python json schema validation package json-spec to validate the JSON.

The Zenodo schema is not very good though as it lacks list constraints that the 
Zenodo will spit back as errors.

```bash
json validate --schema-file=./legacyrecord.json --document-file=./gleanerio-compose/.zenodo.json
```


* NSF DOI: http://data.crossref.org/fundingdata/funder/10.13039/100000001
* https://developers.zenodo.org/#licenses
* https://developers.zenodo.org/#add-metadata-to-your-github-repository-release
* Valid license codes  https://developers.zenodo.org/#licenses
* https://zenodo.org/account/settings/github/ 


From Ilya

```
 Award1 = {"agency": "US National Science Foundation", "award_code": "1928208", "award_URL": "https://www.nsf.gov/awardsearch/showAward?AWD_ID=1928208"}


  "grants": [
    {"id": "10.13039/100000001::1429999"}
  ],
```

1429999 == ECO



```
,
    "communities": [
        {
            "identifier": "EarthCube"
        }
    ],
    "grants": [
        {
            "id": "10.13039/100000001::1928208"
        }
    ]
```


## CITATION.cff


cff-version: 1.1.0
message: "If you use this software, please cite it as below."
authors:
  - family-names: Joe
    given-names: Johnson
    orcid: https://orcid.org/0000-0000-0000-0000
title: gleanerio/gleaner-compose: Updated elements to support dual Blazegraph pattern
version: v0.2
date-released: 2017-12-18
