#! /usr/bin/env bash

set -x
set -e

cd pydantic-settings
git fetch --tags
latest_tag_commit=$(git rev-list --tags --max-count=1)
latest_tag=$(git describe --tags "${latest_tag_commit}")
git checkout "${latest_tag}"

python -m ensurepip --upgrade

make install

make test
