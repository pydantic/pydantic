#!/usr/bin/env bash

# This script is used to build the documentation on CloudFlare Pages,
# here on the `docs-site` branch we just move files in to place.
# A different script with the same name exists on the `main` branch to build docs previews.

set -e
set -x

ls -lha

mkdir -p site

shopt -s extglob
mv !(site|build-docs.sh) site

ls -lha site
