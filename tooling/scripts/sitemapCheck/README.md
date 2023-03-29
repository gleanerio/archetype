# Sitemap check loop

## About

A simple script to loop through a gleaner config file and check the sitemap
status.

Usage:

```bash
python check_sitemap_loop.py -h

usage: check_sitemap_loop.py [-h] [-s SOURCE] [-n NAME] [-f FILE]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Source: URL or file
  -n NAME, --name NAME  Optional name of single source, by name, to check
  -f FILE, --file FILE  Optional name of CSV file to save results to
```

### Pointing to a local file


```bash
python check_sitemap_loop.py -s ~/src/Projects/OIH/odis-arch/config/sources.yaml
```

### Pointing to a URL


```bash
python check_sitemap_loop.py -s https://raw.githubusercontent.com/iodepo/odis-arch/master/config/sources.yaml
```

### Optionally specify the name of single source

Use the `-n` switch to provide the source name, such as:


```bash
python check_sitemap_loop.py -s https://raw.githubusercontent.com/iodepo/odis-arch/master/config/sources.yaml -n cioos
```

### Optionally modify the output

The underlying [advertools](https://advertools.readthedocs.io/en/master/index.html) gives 
some rather verbose output.  You can hide these by redirecting this to /dev/null.
Doing so might give you some nicer output.  So like the following:

```bash
python check_sitemap_loop.py -s https://raw.githubusercontent.com/iodepo/odis-arch/master/config/sources.yaml  2> /dev/null
```

