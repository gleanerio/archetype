#!/bin/bash

# Object store keys
export MINIO_ACCESS_KEY=worldsbestaccesskey
export MINIO_SECRET_KEY=worldsbestsecretkey

# local data volumes
export GLEANER_BASE=/tmp/gleaner
export GLEANER_OBJECTS=${GLEANER_BASE}/datavol/s3
export GLEANER_GRAPH=${GLEANER_BASE}/datavol/graph
export GLEANER_GRAPH_CONF=${GLEANER_BASE}/config
export GLEANER_TRAEFIK=${GLEANER_BASE}/config

# dev exports, you may not need these
export GLEANER_TEXTINDEX=${GLEANER_BASE}/datavol/textindex/data.ms
export GLEANER_GEOHASH=${GLEANER_BASE}/datavol/geohash

# build the directories if they are not present
# some of these packages will do this, some will not, so do them all
mkdir --parents ${GLEANER_BASE}
mkdir --parents ${GLEANER_OBJECTS}
mkdir --parents ${GLEANER_GRAPH}
mkdir --parents ${GLEANER_GRAPH_CONF}
mkdir --parents ${GLEANER_TRAEFIK}
mkdir --parents ${GLEANER_TEXTINDEX}
mkdir --parents ${GLEANER_GEOHASH}

# domains, if routing external to compose, you may not need these
export GLEANER_ADMIN_DOMAIN=admin.local.dev
export GLEANER_OSS_DOMAIN=oss.local.dev
export GLEANER_GRAPH_DOMAIN=graph.local.dev
export GLEANER_WEB_DOMAIN=web.local.dev
export GLEANER_WEB2_DOMAIN=web2.local.dev


