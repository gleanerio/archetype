#!/bin/bash

#  ./load2oxigraph.sh -f "./set1/*.json" -s "http://localhost:7878/store?default"

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--files)
            FILES="$2"
            shift # past argument
            shift # past value
        ;;
        -s|--sparql)
            SPARQL="$2"
            shift # past argument
            shift # past value
        ;;
        -*|--*)
            echo "Unknown option $1"
            exit 1
        ;;
        *)
            POSITIONAL_ARGS+=("$1") # save positional arg
            shift # past argument
        ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

echo "Directory  = ${FILES}"
echo "SPARQL URL = ${SPARQL}"

# If you use this for ntriples, be sure to compute and/or add in a graph in the URL target
for i in $FILES; do
    echo "-------------------"
    echo Next: $i
     cat $i | jsonld format -q |  rapper -i nquads -o turtle  -q -I https://example.org/ - |  curl -X POST -H 'Content-Type:text/turtle' --data-binary  @- $SPARQL
done

