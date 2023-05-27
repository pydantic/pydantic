#! /usr/bin/env bash

set -x
set -e

pushd "$(dirname $0)/../pydantic-settings"

make install

pip install -e ../

make test

popd
