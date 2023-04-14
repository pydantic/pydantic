#!/bin/bash
set -e

# Rebuild lockfiles from scratch, updating all dependencies

command -v pip-compile >/dev/null 2>&1 || {
  echo >&2 "pip-compile is not installed. Install with 'pip install pip-tools'."
  exit 1
}

echo "Updating requirements/*.txt files using pip-compile"
# refresh the constraints / all lockfile
pip-compile -q --resolver backtracking -o requirements/all.txt --strip-extras requirements/all.in

# update all of the other lockfiles
pip-compile -q --resolver backtracking -o requirements/docs.txt requirements/docs-constrained.in
pip-compile -q --resolver backtracking -o requirements/linting.txt requirements/linting-constrained.in
pip-compile -q --resolver backtracking -o requirements/testing.txt  requirements/testing-constrained.in
pip-compile -q --resolver backtracking -o requirements/testing-mypy.txt  requirements/testing-mypy-constrained.in
pip-compile -q --resolver backtracking -o requirements/testing-extra.txt requirements/testing-extra-constrained.in
pip-compile -q --resolver backtracking -o requirements/pyproject-min.txt --pip-args '-c requirements/all.txt' pyproject.toml
pip-compile -q --resolver backtracking -o requirements/pyproject-all.txt --pip-args '-c requirements/all.txt' --all-extras pyproject.toml

# confirm we can do an install
pip install --dry-run -r requirements/all.txt
