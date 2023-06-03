# Release Graphs

This is the start of a simple Python program to work with the 
concept of _release graphs_.  This is rather tightly coupled 
with the object store conventions in Gleaner.  However, it could be 
adapted to address community needs in terms of 
managing graphs.

## Flags

```bash
"-a", "--address", help="address to host plus port like  example.org:1234"
"-s", "--secure", help="SSL:  True or False"
"-b", "--bucket", help="bucket"
"-p", "--prefix", help="prefix"
"-m", "--mode", help="one of: list, markdown, release (requires auth)"
"-sb", "--sourcebucket", help="source bucket for admin feature"
"-sp", "--sourceprefix", help="source prefix for admin feature"
```

## Example Commands

```bash
python rg.py -a ossapi.oceaninfohub.org -b public -p graphs -s false -m list -sb gleaner.oih -sp "graphs/latest"

python rg.py -a ossapi.oceaninfohub.org -b public -p graphs -s false -m markdown -sb gleaner.oih -sp "graphs/latest"

python rg.py -a ossapi.oceaninfohub.org -b public -p graphs -s false -m release -sb testbucket -sp testprefix
```

## Authentication

For the case of _release_ authentication into the S3 system is required.  This script will look for two
environment variables to get the SECRET and KEY values.

```bash
export GLEANER_MINIO_SECRET=yoursecrethere
export GLEANER_MINIO_KEY=yourkeyhere
```
