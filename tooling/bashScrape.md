# Bash commands

What follows are some examples of commands and scripts that can be used for 
quick inspection of resources like sitemaps or even to pull JSON-LD from pages.



```bash
curl -s https://samples.earth/sitemap0.xml
```

```bash
curl -s https://samples.earth/sitemap0.xml |   grep -oP '<loc>\K[^<]*'
```

```bash
#!/bin/bash

url=$1
curl -s $url |   grep -oP '<loc>\K[^<]*'
```

```bash
curl -s  --header "Accept: text/html"   https://samples.earth/id/documents/c1pnht3h2h44frv6igfg | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p'

```

```bash
curl -s  --header "Accept: text/html"   https://samples.earth/id/documents/c1pnht3h2h44frv6igfg | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//'

```

```bash
curl -s  --header "Accept: text/html"   https://samples.earth/id/documents/c1pnht3h2h44frv6igfg | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//' | jsonld format -q

```


```bash
curl -s  --header "Accept: text/html"   https://samples.earth/id/documents/c1pnht3h2h44frv6igfg \
    | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' \
    | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//' | jsonld format -q
```

```bash
#!/bin/bash

url=$1

curl -s  --header "Accept: text/html"   $url \
    | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' \
    | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//' 
```

