# Quickstart

## Prerequisits

To leverage the scripts below you need:

* Docker or Podman installed
* A valid S3 object store (Minio, AWS, Google Cloud, etc) with your access codes
* The scripts use bash, so some environment like Linux, Mac OS or Bash on Windows to run the scripts

## Steps

This is a command line based example and assumes a bash
or zsh type shell.  If you are using another shell or CLI environment
you will need to adapt these commands to your environment.

You will need to extend your path

```bash
export PATH=$PATH:$(pwd)/bin
```

The above assumes you are in the top level directory of this repository.

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
context fils for schema.org.  You can find a skeleton directory
structure for all this in the rundir directory.


You should now be able to run the Gleaner indexing.  The script
that follows works with docker or podman using the

```bash 
-a docker||podman parameter.
```

So an example command using docker might look like:

```bash
cliGleaner.sh -a docker -cfg gleanerconfig.yaml -source africaioc -rude
```

An example config file and the Schema.org context are in the _rundir_ directory of this repo
for your

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