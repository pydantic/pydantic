#! /usr/bin/env bash

set -x
set -e

cd fastapi
git fetch --tags
latest_tag_commit=$(git rev-list --tags --max-count=1)
latest_tag=$(git describe --tags "${latest_tag_commit}")
git checkout "${latest_tag}"

pip install .[all,dev,doc,test]

./scripts/test.sh
