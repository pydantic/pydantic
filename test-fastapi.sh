#! /usr/bin/env bash

set -x
set -e

if [ ! -d "./fastapi/" ]
then
    git clone https://github.com/tiangolo/fastapi.git
fi
cd fastapi
git fetch --tags
latest_tag_commit=$(git rev-list --tags --max-count=1)
latest_tag=$(git describe --tags "${latest_tag_commit}")
git checkout "${latest_tag}"
pip install flit
flit install
pip install -e ..
bash scripts/test.sh
