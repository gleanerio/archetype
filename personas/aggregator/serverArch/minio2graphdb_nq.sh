#!/bin/bash
# A wrapper script for loading RDF into Blazegraph from Minio
# usage:  load2blaze.sh souceBucket

# usage: ./minio2graphdb_nq.sh oih/gleaner.oih/orgs http://local.dev:7200/repositories/Store/statements

mc_cmd() {
        ./mc ls $1 | awk '{print $6}'
}

# If you use this for ntriples, be sure to add in a graph in the URL target
for i in $(mc_cmd $1); do
      echo "-------------start-------------"
      echo Next: $i
      ./mc cat $1/$i | curl -X POST $2 -H 'Content-Type:text/x-nquads' -H 'Accept:text/plain' --data-binary  "@-"
      echo "-------------done--------------"
done