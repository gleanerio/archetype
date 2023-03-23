# Loading

## About

A few useful approaches to loading tripls into graph databases.


echo "test" | curl -X PUT --header "Content-Type:application/n-quads" -d @- http://coreos.lan:3030/testing/data

curl http://ossapi.oceaninfohub.org/public/graphs/summonedcioos_v1_release.rdf | curl -X PUT --header "Content-Type:application/n-quads" -d @- http://coreos.lan:3030/testing/data


