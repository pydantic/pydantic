#!/usr/bin/env bash

# This script is used to build the documentation on CloudFlare Pages, this is just used for build previews
# A different script with the same name exists on the `docs-site` branch (where pre-built docs live).

set -e
set -x

python3 -V

python3 -m pip install --user pdm

python3 -m install -G docs

python3 -m run python -c 'import docs.plugins.main'

python3 -m run mkdocs build
