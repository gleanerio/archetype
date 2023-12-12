# Bash commands

What follows are some examples of commands and scripts that can be used for 
quick inspection of resources like sitemaps or even to pull JSON-LD from pages.

Note the sitemap and example resource used below may change. So replace with your 
values. 


```bash
curl -s https://obis.org/sitemap_datasets.xml
```

```bash
curl -s https://obis.org/sitemap_datasets.xml |   grep -oP '<loc>\K[^<]*'
```

Simple shell script of the above
```bash
#!/bin/bash

url=$1
curl -s $url |   grep -oP '<loc>\K[^<]*'
```

Let's get the JSON-LD
```bash
curl -s  --header "Accept: text/html"   https://obis.org/dataset/dac63ff7-e96f-41fa-8ba9-710c7a92d098 | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p'
```

now remove the script tags
```bash
curl -s  --header "Accept: text/html"   https://obis.org/dataset/dac63ff7-e96f-41fa-8ba9-710c7a92d098 | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//'
```

With the [jsonld-cli](https://github.com/digitalbazaar/jsonld-cli) tool installed, we can now grab these as RDF triples
```bash
curl -s  --header "Accept: text/html"   https://obis.org/dataset/dac63ff7-e96f-41fa-8ba9-710c7a92d098 | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//' | jsonld format -q
```

reformatted 
```bash
curl -s  --header "Accept: text/html"   https://obis.org/dataset/dac63ff7-e96f-41fa-8ba9-710c7a92d098 \
    | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' \
    | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//' | jsonld format -q
```

script version
```bash
#!/bin/bash

url=$1

curl -s  --header "Accept: text/html"   $url \
    | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' \
    | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//' 
```

