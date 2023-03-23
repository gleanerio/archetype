# Provider

## About

This is the provider page.  Here you will edit example pages with JSON-LD markup and
develop a sitemap.xml file to point to them on GitHub via their raw URLs.

## Building a simple sitemap from GitHub raw URLs

The following command can be used to obtain the URLs for a directory in GitHub and
then build a simple sitemap.xml file for testing.

```bash
curl https://api.github.com/repos/BeBOP-OBON/TechOceanS_protocol_collection/contents/odis_metadata\?ref\=main | jq '.[] | .download_url';
```

## References

* link to ESIP SOSO training pages
