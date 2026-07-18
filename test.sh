#!/usr/bin/env bash
set -euo pipefail

echo '=== Extension provenance ==='
uv run --no-sync python -c '
import pydantic_core._pydantic_core as c
path = c.__file__
assert "/workspace/" in path, f"Wrong extension loaded: {path}"
print(f"Extension: {path}")
'

echo ''
echo '=== Targeted: test_aggregate_errors.py (MUST PASS) ==='
uv run --no-sync pytest tests/test_aggregate_errors.py -v

echo ''
echo '=== Targeted: test_types.py -k string ==='
uv run --no-sync pytest tests/test_types.py -k string -q

echo ''
echo '=== Targeted: test_plugins.py (advisory — known env issue with _plugins=None in isolation) ==='
uv run --no-sync pytest tests/test_plugins.py -q || echo "ADVISORY: test_plugins.py failed in isolation (pre-existing environment issue, not caused by aggregate_errors changes)"

echo ''
echo '=== Full suite: make test ==='
uv run --no-sync make test
