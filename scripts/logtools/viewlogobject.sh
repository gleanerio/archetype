#!/bin/bash
# A log review script

PREFIX="oih/gleaner.oih/scheduler/logs/"


# TODO
# mc ls oih/gleaner.oih/scheduler/logs | sort | awk '{print $6}'

#mc_cmd() {
#    mc ls $1 | sort | awk '{print $6}'
#}

# If you use this for ntriples, be sure to compute and/or add in a graph in the URL target
#for i in $(mc_cmd $1); do
#    mc cat $1/$i | grep -o "{[^{}]*}" $filename | grep "\"file\":" | jq .
#done

mc cat $1 | grep -o "{[^{}]*}" $filename | grep "\"file\":" | jq .

