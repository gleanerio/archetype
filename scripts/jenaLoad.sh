#!/bin/bash
#!/bin/bash
# ref: https://jena.apache.org/documentation/io/rdf-input.html
# A wrapper script for loading RDF into Blazegraph from Minio
# example   jenaload nas/gleaner.oih/summoned/edmo
# example blazegraph endpoint: https://ts.collaborium.io/blazegraph/namespace/queue/sparql

mc_cmd() {
        mc ls $1 | awk '{print $6}'
}

# If you use this for ntriples, be sure to add in a graph in the URL target
for i in $(mc_cmd $1); do
      echo "-------------start-------------"
      echo Next: $i
#      mc cat $1/$i | jsonld format -q
      mc cat $1/$i | jsonld format -q | curl -X POST -H 'Content-Type:application/n-triples' --data-binary  @- http://coreos.lan:3030/oihdev/data

      echo "-------------done--------------"
done

