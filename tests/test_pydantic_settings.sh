#! /usr/bin/env bash

set -x
set -e

cd pydantic-settings

python -m ensurepip --upgrade

make install

make test
