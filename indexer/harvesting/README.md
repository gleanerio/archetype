Updating Docker cli

In order for this docker image to work with Google Cloud Run we need
the container to read from ENV vars for the secret keys and also for
the source override for the default config the image is made with.

Also, our Dockerfile now needs to load in the need context files
and also the general config file with the all the sources.  This will
then be overridden with the source ENV value.

Example command

```bash
./gleanerDocker.sh -cfg /gleaner/wd/rundir/oih_queue.yaml  --source emodnet
./gleanerDocker.sh -cfg /gleaner/wd/iow_local.yaml  --source refstates -rude
```

