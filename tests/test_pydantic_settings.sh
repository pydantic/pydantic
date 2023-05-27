#! /usr/bin/env bash

set -x
set -e

pushd "$(dirname $0)/../pydantic-settings"

python -m ensurepip --upgrade

make install

pip install -e ../

make test

popd
