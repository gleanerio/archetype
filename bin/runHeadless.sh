#!/bin/bash

#  Shell script to launch a headless instance for use with the Gelaner script

#podman run -d --privileged --group-add keep-groups -e GRANT_SUDO=yes --user root  -p 9222:9222 chromedp/headless-shell:latest

docker run -d -e GRANT_SUDO=yes --user root  -p 9222:9222 chromedp/headless-shell:latest


