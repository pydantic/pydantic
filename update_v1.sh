#! /usr/bin/env bash

set -x
set -e

echo "cloning pydantic V1"
git clone -b 1.10.X-fixes https://github.com/pydantic/pydantic.git pydantic-v1

pushd "$(dirname $0)/pydantic-v1"

# Find latest tag in v1
latest_tag=$(git describe --tags --abbrev=0)
echo "latest tag in V1 is '${latest_tag}'"
git checkout "${latest_tag}"

# Remove current V1
rm -rf ../pydantic/v1

# Copy new V1 into pydantic/v1
cp -r pydantic ../pydantic/v1

popd

# Remove V1 clone
rm -rf pydantic-v1
