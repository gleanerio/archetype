#!/bin/bash

# nabu-cli 
# A wrapper script for invoking nabu-cli with docker
# Put this script in $PATH as `nabu-cli`


PROGNAME="$(basename $0)"
VERSION="v0.0.1"
NBIMAGE="fils/nabu:2.0.15-df-development"

# Pull down some of the needed docks if called with -init
if [[ $1 == "-init" ]];
then
    curl -O https://schema.org/version/latest/schemaorg-current-https.jsonld
    curl -O https://raw.githubusercontent.com/earthcubearchitecture-project418/gleaner/master/configs/demo.yaml
    curl -O https://raw.githubusercontent.com/earthcubearchitecture-project418/gleaner/master/deployment/setenvIS.sh
    curl -O https://raw.githubusercontent.com/earthcubearchitecture-project418/gleaner/master/deployment/gleaner-IS.yml
    docker pull fils/gleaner:latest
    echo "\n See notes at: https://github.com/gleanerio/gleaner/blob/dev/docs/cliDocker/README.md \n"
    exit 0
fi

# Helper functions for guards
error(){
  error_code=$1
  echo "ERROR: $2" >&2
  echo "($PROGNAME wrapper version: $VERSION, error code: $error_code )" &>2
  exit $1
}

check_cmd_in_path(){
  cmd=$1
  which $cmd > /dev/null 2>&1 || error 1 "$cmd not found!"
}

# Guards (checks for dependencies)
check_cmd_in_path docker
check_cmd_in_path curl

while getopts ":a:" opt; do
  case $opt in
    a)
      #echo "-a was triggered, Parameter: $OPTARG" >&2
      case $OPTARG in
          docker)
                # Docker:  current docker command to do local volume mounts
                shift 2  # drop the now unneed first two cli params
                exec docker run \
                  --interactive --tty --rm \
                  -e MINIO_USE_SSL \
                  -e MINIO_SECRET_KEY \
                  -e MINIO_ACCESS_KEY \
                  --network=host \
                  --volume "$PWD":/wd \
                  --workdir /wd \
                  $NBIMAGE "$@"
          ;;
          podman)
                # Podman:  podman needs --privileged to mount /dev/shm
                #  "docker.io/fils/gleaner:v3.0.11-development-df" "$@"
                shift 2  # drop the now unneed first two cli params
                exec podman run \
                  --privileged \
                  --group-add keep-groups \
                  -e MINIO_USE_SSL \
                  -e MINIO_SECRET_KEY \
                  -e MINIO_ACCESS_KEY \
                  --user root \
                  --network=host \
                  --interactive --tty --rm \
                  --volume "$PWD":/wd \
                  --workdir /wd \
                  $NBIMAGE "$@"
          ;;
      esac
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done


# stuff below can be removed..   just here for reference for a while


# Set up mounted volumes, environment, and run our containerized command
# podman needs --privileged to mount /dev/shm
#exec podman run \
#  --privileged \
#  --network=host \
#  --interactive --tty --rm \
#  --group-add keep-groups \
#  --volume "$PWD":/nabu/wd \
#  --workdir /nabu/wd \
#  $NBIMAGE "$@"

#exec docker run \
    #--network=host \
    #--interactive --tty --rm \
    #--group-add keep-groups \
    #--volume "$PWD":/wd \
    #--workdir /wd \
    #"docker.io/fils/nabu:2.0.9-df-development" "$@"

