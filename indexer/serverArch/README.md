# Configuration

## About

Quick start on architecture setup.  This document assumes a recent install of the 
[Docker environment](https://www.docker.com/).  Storage requirements are minimal at
a few GB for the Docker images but depending on how much you index, your storage
needs will need to grow to address that.  You will also need Git installed to pull down the working files and configurations.  However, you can also go to the GitHub website and download via http if you don't have or want Git installed.  

## Steps to configure

We will use the configuration files in [harvest.geoconnex.us](https://github.com/internetofwater/harvest.geoconnex.us) so use git to clone that repository to your local system or the machine you are going to run on or download an archive of the repo via the web site if you wish.  

### Environment


The setenv.sh is an example script for setting the environment variables for 
your local install.  This might also be done in a secrets store or some other method
that aligns with your local environment.  For now we will use this as an example 
who's functionality can be adapted.

```
#!/bin/bash

# Object store keys
export MINIO_ACCESS_KEY= 
export MINIO_SECRET_KEY= 

# local data volumes
export GLEANER_BASE=/mnt/path/to/data
mkdir --parents ${GLEANER_BASE}
export GLEANER_OBJECTS=${GLEANER_BASE}/datavol/s3
export GLEANER_MEILI=${GLEANER_BASE}/datavol/data.ms
export GLEANER_GRAPH=${GLEANER_BASE}/datavol/graph
export GLEANER_GRAPH_CONF=${GLEANER_BASE}/config
export GLEANER_TRAEFIK=${GLEANER_BASE}/config
# build out the paths for good measure
mkdir --parents ${GLEANER_OBJECTS}
mkdir --parents ${GLEANER_MEILI}
mkdir --parents ${GLEANER_GRAPH}
mkdir --parents ${GLEANER_GRAPH_CONF}

# domains
export GLEANER_DOMAIN=local.dev
export GLEANER_ADMIN_DOMAIN=admin.${GLEANER_DOMAIN}
export GLEANER_OSS_DOMAIN=oss.${GLEANER_DOMAIN}
export GLEANER_GRAPH_DOMAIN=graph.${GLEANER_DOMAIN}
export GLEANER_WEB_DOMAIN=search.${GLEANER_DOMAIN}
export GLEANER_WEB2_DOMAIN=search.${GLEANER_DOMAIN}
```

The main items we need to set in this file are the ACCESS and SECRET keys for our
[Minio](https://min.io/) installation.  We use Minio as the S3 API compatible object store.  You could also use AWS S3, Google Cloud Storage, Swift or any of a number of S3 compatible object stores.  

The other items to set include the base location on the local disk for things like 
logs, temp files and the like.  Set GLEANER_BASE as the top level of this location which will be used to build out the remaining paths.  

Last we need to set a domain, either fully qualified and on the Internet, or a local developer domain.  Set GLEANER_DOMAIN to some value you wish to use.  

Note that the networking setup, especially for a local network off the main Internet, can be problematic at times.  Firewalls or other rules on your machine and local SSL certificates can sometimes be troublesome.  This aspect may be one of the most 
difficult elements of the setup.  

### Settings

### Running Server Arch

Outline of steps to run:

* ```git clone https://github.com/internetofwater/harvest.geoconnex.us``` to pull down the configuration templates
* ```cd harvest.geoconnex.us/confgis```
  
    We will now need to update the setenv.sh environment variables.  

* ```docker-compose -f compose.yaml up -d```
* ```caddy start```  



### Running Harvest

Source sitemap is at:  https://geoconnex.us/sitemap.xml  

Zip file is at:  https://github.com/internetofwater/geoconnex.us/blob/master/PID-server/backup/sitemap.zip  

### Checking Graph
