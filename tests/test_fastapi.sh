#! /usr/bin/env bash

set -x
set -e

cd fastapi
git fetch --tags
latest_tag_commit=$(git rev-list --tags --max-count=1)
latest_tag=$(git describe --tags "${latest_tag_commit}")
git checkout "${latest_tag}"

# FIXME this is a temporary workaround while fastapi tests are broken with newer sqlalchemy
pip install SQLAlchemy==1.3.23

pip install -U flit
flit install

# ignore cryptography warning https://github.com/mpdavis/python-jose/issues/208
PYTHONPATH=./docs/src pytest -W 'ignore:int_from_bytes is deprecated, use int.from_bytes instead:cryptography.utils.CryptographyDeprecationWarning'
