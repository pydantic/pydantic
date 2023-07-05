#! /usr/bin/env bash

set -x
set -e

cd fastapi
git fetch --tags

# TODO: Use the proper latest tag once FastAPI stable release is compatible with Pydantic V2.
# latest_tag=$(git describe --tags --abbrev=0)
# git switch -d "${latest_tag}"
git switch "main-pv2"

pip install -r requirements.txt

./scripts/test.sh
