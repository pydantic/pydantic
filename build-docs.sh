#!/usr/bin/env bash

# This script is used to build the documentation on CloudFlare Pages, this is just used for build previews
# A different script with the same name exists on the `docs-site` branch (where pre-built docs live).

set -e
set -x

curl -LsSf https://astral.sh/uv/install.sh | sh
${HOME}/.cargo/bin/uv python install 3.12
${HOME}/.cargo/bin/uv sync --group docs --frozen
${HOME}/.cargo/bin/uv run python -c 'import docs.plugins.main'
${HOME}/.cargo/bin/uv run --no-sync mkdocs build
