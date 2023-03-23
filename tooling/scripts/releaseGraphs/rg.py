#!/usr/bin/env python

# Imports
import warnings
import logging, sys, re, os
import distutils
import argparse
from minio import Minio
from minio.commonconfig import REPLACE, CopySource


warnings.simplefilter(action='ignore', category=FutureWarning)  ## remove pandas future warning
logging.disable(sys.maxsize)  # suppress logging output


def main():
    # Initialize args  parser for host, port, secure (bool), bucket, prefix
    # modes   list, md (markdown) and update (requires auth for last one)
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", help="address to host plus port like  example.org:1234")
    parser.add_argument("-s", "--secure", help="SSL:  True or False")
    parser.add_argument("-b", "--bucket", help="bucket")
    parser.add_argument("-p", "--prefix", help="prefix")
    parser.add_argument("-m", "--mode", help="one of: list, markdown, release (requires auth)")
    parser.add_argument("-sb", "--sourcebucket", help="source bucket for admin feature")
    parser.add_argument("-sp", "--sourceprefix", help="source prefix for admin feature")

    # look for keys in the environment to support release function
    MINIO_SECRET = os.environ.get('GLEANER_MINIO_SECRET')
    MINIO_KEY = os.environ.get('GLEANER_MINIO_KEY')

    args = parser.parse_args()
    host = args.address
    secure = args.secure
    bucket = args.bucket
    prefix = args.prefix
    sbucket = args.sourcebucket
    sprefix = args.sourceprefix
    mode = args.mode

    # Create client with anonymous access.
    if mode == "release":
        client = Minio(
            host,
            secure=bool(distutils.util.strtobool(secure)),
            access_key=os.environ.get('GLEANER_MINIO_KEY'),
            secret_key=os.environ.get('GLEANER_MINIO_SECRET'),
        )
    else:
        client = Minio(host, secure=bool(distutils.util.strtobool(secure)), )

    match mode:
        case "markdown":
            markdown(client, bucket, prefix)
        case "list":
            list(client, bucket, prefix)
        case "release":
            release(client, bucket, prefix, sbucket, sprefix)

        # If an exact match is not confirmed, this last case will be used if provided
        case _:
            print("mode not found")


# admin needs to copy all objects from a bucket prefix to a new bucket prefix
def release(client, bucket, prefix, sbucket, sprefix):
    print("copy from {}:{}".format(sbucket, sprefix))
    print("copy to   {}:{}".format(bucket, prefix))

    # pattern = r"summoned(.*?)_2"
    pattern = r"_(.*?)_"  # matches the data in our naming convention

    objects = client.list_objects(sbucket, prefix=sprefix, recursive=True)
    for obj in objects:
        p = str(obj.object_name)
        np = ""
        print(" ------- ")
        print("from {}  {}".format(sbucket, p))
        match = re.search(pattern, p)
        if match:
            if obj.size > 0:
                np = p.replace(match.group(1), "v1", 1)
                np = np.replace("/latest", "", 1)
                print("to {} {}".format(bucket, np))
                # copy an object from a bucket to another.
                result = client.copy_object(bucket,  np, CopySource(sbucket, p))
                print(result.object_name, result.version_id)
            else:
                print("no data in graph file")
        else:
            print("no match")
        print(" ------- ")



def markdown(client, bucket, prefix):
    ## need to switch on the modes here..
    # make a main and then call functions based on swithc

    print("| provider   |      size      |  date | URL")
    print("|----------|:-------------:|------:|------:|")

    # List objects information whose names starts with "my/prefix/".
    objects = client.list_objects(bucket, prefix=prefix, recursive=True)
    for obj in objects:
        result = client.stat_object(bucket, obj.object_name)

        if result.size > 0:  # how to tell if an objet   obj.is_public  ?????
            # Use presigned_get_object() to get a presigned URL for the object
            url = client.presigned_get_object(bucket, obj.object_name)

            #  need to parse out the name from the release graph and the base name of the shacl shape used
            # Define the regular expression pattern
            pattern = r"summoned(.*?)_v1"

            # Use re.search() to extract the text between "summoned" and "_v1"
            match = re.search(pattern, url)
            source = "unknown"

            if match:
                # Access the matched text using group(1)
                source = match.group(1)
            else:
                print("No match found.")
                raise "unable to match on provider name via regex"

            print("| {3} | {2}  | {1}  | [{0}]({0}) |".format(url, result.last_modified, result.size,
                                                              source))
            # print("{3} \t URL: {0}  \t size: {2}\t  last-modified: {1}".format(url, result.last_modified, result.size,
            #                                                                    source))


def list(client, bucket, prefix):
    ## need to switch on the modes here..
    # make a main and then call functions based on swithc

    # List objects information whose names starts with "my/prefix/".
    objects = client.list_objects(bucket, prefix=prefix, recursive=True)
    for obj in objects:
        result = client.stat_object(bucket, obj.object_name)

        if result.size > 0:  # how to tell if an objet   obj.is_public  ?????
            # Use presigned_get_object() to get a presigned URL for the object
            url = client.presigned_get_object(bucket, obj.object_name)
            print("URL: {0}  \t size: {2}\t  last-modified: {1}".format(url, result.last_modified, result.size))


if __name__ == '__main__':
    main()
