#!/bin/bash
set -e

# Sync lockfiles with requirements files.

command -v pip-compile >/dev/null 2>&1 || {
  echo >&2 "pip-compile is not installed. Install with 'pip install pip-tools'."
  exit 1
}

echo "Recreating requirements/*.txt files using pip-compile"

# delete the lockfiles
find requirements -name "*.txt" -type f -delete
# rebuild them
./requirements/refresh.sh
