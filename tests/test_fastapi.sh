#! /usr/bin/env bash

set -x
set -e

cd fastapi
git fetch --tags
git checkout 0.99.1

pip install -r requirements.txt

./scripts/test.sh
