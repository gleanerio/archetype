#!/bin/bash

# nabu-cli 
# A wrapper script for invoking nabu-cli with docker
# Put this script in $PATH as `nabu-cli`

# Set up mounted volumes, environment, and run our containerized command
# podman needs --privileged to mount /dev/shm
exec podman run \
  --privileged \
  --network=host \
  --interactive --tty --rm \
  --volume "$PWD":/nabu/wd \
  --workdir /nabu/wd \
  "docker.io/fils/nabu:2.0.3-developement" "$@"

#exec docker run \
    #--network=host \
    #--interactive --tty --rm \
    #--volume "$PWD":/wd \
    #--workdir /wd \
    #"docker.io/fils/nabu:2.0.3-developement" "$@"

