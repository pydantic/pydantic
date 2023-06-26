#! /usr/bin/env bash

set -x
set -e

cd fastapi
git fetch --tags
# TODO: Remove the comments once FastAPI 0.100.0 is released.
# latest_tag_commit=$(git rev-list --tags --max-count=1)
# latest_tag=$(git describe --tags "${latest_tag_commit}")
latest_tag="0.100.0-beta1"
git checkout "${latest_tag}"

pip install -r requirements.txt

./scripts/test.sh
