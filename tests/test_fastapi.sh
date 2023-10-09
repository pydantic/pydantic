#! /usr/bin/env bash

set -x
set -e

cd fastapi
git fetch --tags
git checkout 0.99.1

# temp fix for flask dependency issue
# see: https://stackoverflow.com/questions/77213053/importerror-cannot-import-name-url-quote-from-werkzeug-urls
pip install Werkzeug==2.2.2
pip install -r requirements.txt

./scripts/test.sh
