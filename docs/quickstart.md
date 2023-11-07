# Quickstart

> Note:  This system currently doesn't support headless indexing.  That is,
> indexing that requires an approach that processes a web page to execute
> javascript that places the JSON-LD into the document object model.


## Requirements

To leverage the scripts below you need:

* Docker or Podman installed
* A valid S3 object store (Minio, AWS, Google Cloud, etc) with your access codes
* The scripts use bash, so some environment like Linux, Mac OS or Bash on Windows to run the scripts

## Steps

This is a command line based example and assumes a bash
or zsh type shell.  If you are using another shell or CLI environment
you will need to adapt these commands to your environment.

You will need to extend your path, by executing the following at
the top level directory of this repository:

```bash
export PATH=$PATH:$(pwd)/bin
```

You will also need to set up Minio or have an S3 compatible
service via AWS, Googl or others.  For Minio see the
[Minio Quickstart](https://min.io/docs/minio/linux/index.html?ref=docs-redirect)


Next you will need to set a few environment variables.

```bash 
export MINIO_USE_SSL=true
export MINIO_SECRET_KEY=your-secret-here
export MINIO_ACCESS_KEY=your-access-here
```

Set the SSL variable for your environment.  AWS or Google services will always be true but
a local setup might not be.

You need to have a valid Gleaner config file and some base JSON-LD
context files for schema.org.  You can find a skeleton directory
structure for all this in the rundir directory.

> **_NOTE:_** In the case of AWS S3, it is important to use the region-specific  
> version of the AWS API URL, for the `address` parameter in your Gleaner config  
> file, such as `address: s3.ca-central-1.amazonaws.com` if your AWS buckets
> are in the `ca-central-1` region


You should now be able to run the Gleaner indexing.  The script
that follows works with docker or podman using the

```bash 
-a docker||podman parameter.
```

So an example command using docker might look like:

```bash
cliGleaner.sh -a docker -cfg gleanerconfig.yaml -source africaioc -rude
```

> **_NOTE:_** If you receive an error of `permission denied while trying to connect to the Docker daemon socket` 
> then you likely have to add your user to the docker group, 
> see [here](https://www.digitalocean.com/community/questions/how-to-fix-docker-got-permission-denied-while-trying-to-connect-to-the-docker-daemon-socket)

An example config file and the Schema.org context are in the _rundir_ directory of this repo
for your use.  You can try executing the above `cliGleaner.sh` command 
from inside that `rundir` folder, which will use the config located there.


## Nabu CLI

There is also a CLI tools for transforming JSON-LD objects into a single release graph in NQuads format.
This tool can also load JSON-LD objects into a triplestore.  It has been tested with BlazeGraph, Jena, Oxigraph and GraphDB.  

### Release

This command will ETL the JSON-LD documents into a single relase graph in NQUADS format.  It will 
place these in the ```graphs``` bucket prefix in the bucket you specify in the config file
at ```minio:bucket```

```bash
cliNabu.sh -a docker --cfg nabuconfig.yaml release --prefix summoned/sourcex 
```

The path specified in --prefix must be a bucket prefix in the bucket you specify in the config file
at ```minio:bucket```.   So in the case above and using the default config file the bucket path

```bash
yourbucketname/summoed/sourcex
```

must exist.  


### Bulk

```bash
cliNabu.sh -a docker --cfg nabuconfig.yaml bulk --prefix summoned/sourcex --endpoint triplestore
```

### Prefix

```bash
cliNabu.sh -a docker --cfg nabuconfig.yaml prefix --prefix summoned/sourcex --endpoint triplestore
```


You can also reference the [Nabu docs](https://github.com/gleanerio/nabu/tree/master/docs)


## configs for various sources

For a local S3 like Minio.  Here is an example on a local port 45123 with no SSL.  No _region_ is needed
in this case.

```yaml
---
minio:
address: myminio.dev
port: 45123
accessKey:
secretKey:
ssl: false
bucket: yourbucketname
```


Google

```yaml
---
minio:
address: storage.googleapis.com
port: 443
accessKey:
secretKey:
ssl: true
bucket: yourbucketname
region: US-CENTRAL-1
```

AWS

Note for many regions you will need to encode the URL in the address node with the region such as

```yaml
address: http://s3-us-west-2.amazonaws.com/
```

for region us-west-2.  Use that pattern for your region.

```yaml
---
minio:
address: s3.amazonaws.com
port: 443
accessKey:
secretKey:
ssl: true
bucket: yourbucketname
region: us-east-1
```
