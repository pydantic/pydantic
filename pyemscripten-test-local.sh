#!/usr/bin/env bash
# Bootstrap a local pyemscripten toolchain into .pyodide-toolchain/, build
# the pyemscripten + pure-Python wheels, and run the test suite under Pyodide.
# Idempotent: re-running skips already-installed components.
#
# Prereqs: Python 3.14, rustup, git, curl. Override versions via env vars
# (EMSDK_VERSION, PYODIDE_VERSION, PYTHON_BIN).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLCHAIN_DIR="${REPO_ROOT}/.pyodide-toolchain"
EMSDK_VERSION="${EMSDK_VERSION:-5.0.3}"
PYODIDE_VERSION="${PYODIDE_VERSION:-314.0.0a2}"
PYTHON_BIN="${PYTHON_BIN:-python3.14}"

require() {
    command -v "$1" >/dev/null 2>&1 || { echo "missing prerequisite: $1" >&2; exit 1; }
}
require "${PYTHON_BIN}"
require rustup
require git
require curl

mkdir -p "${TOOLCHAIN_DIR}"

echo "[pyemscripten-test-local] ensuring Rust wasm32-unknown-emscripten target"
rustup target add wasm32-unknown-emscripten >/dev/null

EMSDK_DIR="${TOOLCHAIN_DIR}/emsdk"
if [ ! -x "${EMSDK_DIR}/emsdk" ]; then
    echo "[pyemscripten-test-local] cloning emsdk ${EMSDK_VERSION}"
    git clone --depth 1 --branch "${EMSDK_VERSION}" \
        https://github.com/emscripten-core/emsdk.git "${EMSDK_DIR}"
fi
if ! "${EMSDK_DIR}/emsdk" list --installed 2>/dev/null | grep -q "INSTALLED.*${EMSDK_VERSION}"; then
    echo "[pyemscripten-test-local] installing emsdk ${EMSDK_VERSION}"
    "${EMSDK_DIR}/emsdk" install "${EMSDK_VERSION}"
    "${EMSDK_DIR}/emsdk" activate "${EMSDK_VERSION}"
fi
# shellcheck disable=SC1091
source "${EMSDK_DIR}/emsdk_env.sh" >/dev/null

VENV_DIR="${TOOLCHAIN_DIR}/venv"
if [ ! -x "${VENV_DIR}/bin/pyodide" ]; then
    echo "[pyemscripten-test-local] creating venv at ${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
    "${VENV_DIR}/bin/pip" install --quiet "pyodide-build[resolve]>=0.34.3" build twine
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

if ! pyodide xbuildenv versions 2>/dev/null | grep -q "${PYODIDE_VERSION}"; then
    echo "[pyemscripten-test-local] installing Pyodide xbuildenv ${PYODIDE_VERSION}"
    pyodide xbuildenv install "${PYODIDE_VERSION}"
fi

cd "${REPO_ROOT}"
echo "[pyemscripten-test-local] building pydantic-core pyemscripten wheel"
make -C pydantic-core build-pyemscripten

echo "[pyemscripten-test-local] building pure-Python pydantic wheel"
python -m build --wheel --outdir dist

echo "[pyemscripten-test-local] running test suite"
exec bash pyemscripten-run-tests.sh
