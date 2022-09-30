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
export GLEANER_INDEX_DOMAIN=index.${GLEANER_DOMAIN}
