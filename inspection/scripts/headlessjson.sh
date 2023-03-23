#!/bin/bash

url=$1

google-chrome --headless --disable-gpu --virtual-time-budget=5000  --dump-dom $1  \
    | sed -n '/<script type=\"application\/ld+json\">/,/<\/script>/p' \
    | sed 's/<\/script>//' | sed 's/<script type=\"application\/ld+json\">//' 


