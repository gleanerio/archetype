# Sitemap check loop

## About

A simple script to loop through a gleaner config file and check the sitemap
status.

Usage:

```bash
❯ python check_sitemap_loop.py -h

usage: check_sitemap_loop.py [-h] [-s SOURCE] [-n NAME]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Source: URL or file
  -n NAME, --name NAME  Optional name of single source, by name, to check
```

With file

```bash
python check_sitemap_loop.py ~/src/Projects/OIH/odis-arch/config/sources.yaml
```

With URL

```bash
python check_sitemap_loop.py https://raw.githubusercontent.com/iodepo/odis-arch/master/config/sources.yaml
```

The adv tools does some rather verbose output.  You can hide these by redirecting this to /dev/null.
Doing so might give you some nicer output.  So like the following:

```bash
python check_sitemap_loop.py https://raw.githubusercontent.com/iodepo/odis-arch/master/config/sources.yaml  2> /dev/null
```

