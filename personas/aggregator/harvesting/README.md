# Rundir

## About

This is the main directory for the action of indexing.

## Prequisits

### curl

Curl is used in some modes in the scripts to pull down example or support files.
This is not being heavily exploited at this time so if you get a warning that
curl is not installed simply comment out the

```
check_cmd_in_path curl
```

line in the script.

### Docker

You will need either docker or podman installed in order to run the containers.
The script has a flag to allow the selection of either podman or docker.  Typcially
these are command compliant with each other, but there can be small differences
with permissions from time to time.

### S3 compliant object store

Gleaner and other tools in the GleanerIO suite of programs use a Minio object
store to assemble and operate on the results of a harvest.

To do this you need to setup and run or have access to an S3 compliant object
store like AWS S3, Google Cloud Strorage or the open source Minio server.

The [Minio quick start](https://min.io/docs/minio/linux/index.html?ref=docs-redirect)
provides a good guide for setting up this service if you
choose to.

Whatever approach you select you need to put this information into the
configuration file in the section:

```yaml
minio:
    address: 192.168.202.114
    port: 49153
    accessKey:
    secretKey:
    ssl: False
    bucket: gleaner.oih
```

The accessKey and secretKey can also be set in environment variables and these
will be read and passed to the container.  Set the variables:

```bash
export MINIO_SECRET_KEY=MYSECRET
export MINIO_ACCESS_KEY=MYACCESS
```

Note if you use AWS or Google other services the node is
still names _minio_ and you simple put in the information in the parameters.

So when using AWS S3 it might look like:


```yaml
minio:
    address: s3.amazonaws.com
    port:
    accessKey:
    secretKey:
    ssl: True
    bucket: your.bucket
```

### Headless Chrome

In cases where the JSON-LD is placed into the page DOM via a javascript call, it
is necessary to render the page and run the javascript in order to gain access to the
JSON-LD.

This is only needed in cases where this service is needed.  If your code does not
use this approach then you do not need to run the service described in this section.

To do this a headless browser, in this case Chrome, needs to be run.  This
is an instance of Chrome with no UI and accessed via API calls.  The entry in the
config file that supports this is in the summoner section as the headless entry
as seen following.

```yaml
summoner:
    after: ""      # "21 May 20 10:00 UTC"
    mode: full  # full || diff:  If diff compare what we have currently in gleaner to sitemap, get only new, delete missing
    threads: 5
    delay:  # milliseconds (1000 = 1 second) to delay between calls (will FORCE threads to 1)
    headless: http://0.0.0.0:9222  # URL for headless see docs/headless
```

Chance this entry to match where you are running headless.

```
podman run -d --privileged --group-add keep-groups -e GRANT_SUDO=yes --user root  -p 9222:9222 chromedp/headless-shell:latest
```

If you use docker you should be able to simply replace podman in the above command
with docker.


## Set the ENV variables

For this approach the secrets will be in a environment file kept out
of the repository and holding your secrets.  Mostly these will be the
access keys for your S3 object store.


## Example command

As noted above you need to set the accessKey and secretKey in environment variables and these
will be read and passed to the container.  Set the variables:

```bash
export MINIO_SECRET_KEY=MYSECRET
export MINIO_ACCESS_KEY=MYACCESS
```

to align

For docker
```bash
../scripts/cliGleaner.sh -a docker --cfg 09022023_iow.yml --source cioos --rude 
```

For podman
```bash
../scripts/cliGleaner.sh -a podman --cfg 09022023_iow.yml --source cioos --rude 
```
