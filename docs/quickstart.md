# Quickstart

This is a command line based example and assumes a bash
or zsh type shell.  If you are using another shell or CLI environment
you will need to adapt these commands to your environment.

First you will need to set a few environment variables.

```bash
export PATH=$PATH:$(pwd)/bin
```

The above assumes you are in the top level directory of this repository.

You will also need to set up Minio or have an S3 compatible
service via AWS, Googl or others.  For Minio see the
[Minio Quickstart](https://min.io/docs/minio/linux/index.html?ref=docs-redirect)

You need to have a valid Gleaner config file and some base JSON-LD
context fils for schema.org.  You can find a skeleton directory
structure for all this in the rundir directory.

```bash 
export MINIO_USE_SSL=false
export MINIO_SECRET_KEY=your-secret-here
export MINIO_ACCESS_KEY=your-access-here
```

You should now be able to run the Gleaner indexing.  The script
that follows works with docker or podman using the

```bash 
-a docker||podman parameter.
```

So an example command might look like:

```bash
cliGleaner.sh -a podman -cfg gleanerconfig.yaml -source africaioc -rude
```
