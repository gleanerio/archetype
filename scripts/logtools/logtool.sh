#!/bin/bash

# Note, this script requires the installation of the minio mc client binary
# found at https://min.io/docs/minio/linux/reference/minio-mc.html?ref=docs-redirect

#PREFIX="oih/gleaner.oih/scheduler/logs"
PREFIX=$GLEANERIO_LOGDIR

# Function to display usage information
function usage() {
    echo "Usage: $0 [-h] [-a] [-b] [-c]"
    echo ""
    echo "Options:"
    echo "  -h  Display this help message"
    echo "  -l  list object in prefix GLEANERIO_LOGDIR"
    echo "  -c  X  view object X in prefix GLEANERIO_LOGDIR "
    echo ""
}

# Parse command line arguments
while getopts ":hlc" opt; do
  case ${opt} in
    h )
      usage
      exit 0
      ;;
    l )
      # Command l, list
         mc ls $PREFIX | sort | awk '{print $6}'
      ;;
    c )
      # Command c, cat
         mc cat $PREFIX/$2 | grep -o "{[^{}]*}" $filename | grep "\"file\":" | jq .
      ;;
    \? )
      echo "Invalid option: -$OPTARG" 1>&2
      usage
      exit 1
      ;;
  esac
done

# Shift command line arguments to ignore the processed options
shift $((OPTIND -1))
