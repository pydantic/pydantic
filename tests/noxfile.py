"""
Logic required for running tests with webassembly/emscripten
"""
import json
import os
from pathlib import Path

import nox

PYODIDE_VERSION = os.getenv('PYODIDE_VERSION', '0.21.0-alpha.2')
GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS')
GITHUB_ENV = os.getenv('GITHUB_ENV')


def append_to_github_env(name: str, value: str):
    if not GITHUB_ACTIONS or not GITHUB_ENV:
        return

    with open(GITHUB_ENV, 'w+') as f:
        f.write(f'{name}={value}\n')


@nox.session(name='setup-pyodide')
def setup_pyodide(session: nox.Session):
    tests_dir = Path(__file__).resolve().parent
    with session.chdir(tests_dir):
        session.run('npm', 'i', '--no-save', f'pyodide@{PYODIDE_VERSION}', 'prettier', external=True)
        with session.chdir(tests_dir / 'node_modules' / 'pyodide'):
            session.run('node', '../prettier/bin-prettier.js', '-w', 'pyodide.asm.js', external=True)
            with open('repodata.json') as f:
                emscripten_version = json.load(f)['info']['platform'].split('_', 1)[1].replace('_', '.')
                append_to_github_env('EMSCRIPTEN_VERSION', emscripten_version)


@nox.session(name='test-emscripten')
def test_emscripten(session: nox.Session):
    tests_dir = Path(__file__).resolve().parent
    crate = tests_dir.parent
    with session.chdir(tests_dir):
        session.run('node', 'emscripten_runner.js', str(crate), external=True)
