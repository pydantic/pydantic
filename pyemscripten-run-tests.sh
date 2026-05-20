#!/usr/bin/env bash
# Run the test suite inside a Pyodide venv against pyemscripten wheels in
# pydantic-core/dist/ and the pure-Python pydantic wheel in dist/.
set -euo pipefail

VENV_DIR=".venv-pyodide"

if [ ! -d "${VENV_DIR}" ]; then
    pyodide venv "${VENV_DIR}"
fi
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

shopt -s nullglob
core_wheels=(
    pydantic-core/dist/pydantic_core-*-cp*-pyemscripten_*_wasm32.whl
    pydantic-core/dist/pydantic_core-*-cp*-emscripten_*_wasm32.whl
)
pyd_wheels=(dist/pydantic-*-py3-none-any.whl)
shopt -u nullglob

if [ ${#core_wheels[@]} -eq 0 ]; then
    echo "no pydantic-core wasm wheel in pydantic-core/dist/" >&2
    exit 1
fi
if [ ${#pyd_wheels[@]} -eq 0 ]; then
    echo "no pydantic wheel in dist/" >&2
    exit 1
fi

# --force-reinstall so re-runs pick up freshly-built wheels with the same version.
pip install --force-reinstall --no-deps "${core_wheels[0]}" "${pyd_wheels[0]}"
pip install \
    pytest \
    pytest-mock \
    pytest-pretty \
    pytest-run-parallel \
    dirty-equals \
    hypothesis \
    inline-snapshot \
    typing-inspection \
    typing-extensions \
    annotated-types \
    eval-type-backport \
    jsonschema \
    pytz \
    tzdata

# `--override-ini=addopts=` drops the project's `--benchmark-*` defaults
# (pytest-benchmark is not installed here).
pytest_log=$(mktemp)
plain_log=$(mktemp)
trap 'rm -f "${pytest_log}" "${plain_log}"' EXIT
set +e
pytest \
    --override-ini='addopts=' \
    -p no:cacheprovider \
    -p no:timeout \
    --ignore=tests/pydantic_core/benchmarks \
    --ignore=tests/mypy \
    --ignore=tests/typechecking \
    --ignore=tests/benchmarks \
    --ignore=tests/test_docs.py \
    tests/pydantic_core \
    tests 2>&1 | tee "${pytest_log}"
pytest_exit=${PIPESTATUS[0]}
set -e

sed -E $'s/\x1b\\[[0-9;]*[a-zA-Z]//g' "${pytest_log}" > "${plain_log}"

# Pyodide 314.0.0a2's wasm runtime crashes during CPython interpreter teardown
# after pytest's summary prints. pytest's own exit code is 0 but the process
# exits 1 from the post-summary crash. Drop this once Pyodide 314.0.0 stable
# lands. Repro:  python -c "from jsonschema import Draft202012Validator"
# Working on fixing this upstream
if [ "${pytest_exit}" -ne 0 ] \
    && grep -q 'Pyodide has suffered a fatal error' "${plain_log}" \
    && grep -qE '^Results \([0-9.]+s\):' "${plain_log}" \
    && ! grep -qE '(^|[[:space:]])[0-9]+ (failed|error)' "${plain_log}" \
    && ! grep -qE '(error|errors) during collection' "${plain_log}"; then
    echo "[pyemscripten-run-tests] pytest clean; ignoring Pyodide teardown crash."
    exit 0
fi
exit "${pytest_exit}"
