# README

## Quick start

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

### Command

```bash
 cliGleaner.sh -a podman -cfg gleanerconfig.yaml -source r2r --rude 
```