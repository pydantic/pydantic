import importlib
import os
import stat
import sys
import traceback
from pathlib import Path
from zipfile import ZipFile

import micropip
import pyodide
import tomllib


def extract_repo(zip_path: str) -> None:
    """Extract the GitHub repository archive in the current directory, stripping the top-level directory."""
    with ZipFile(zip_path) as zip_file:
        for info in zip_file.infolist():
            _, _, name = info.filename.partition('/')
            if not name or info.is_dir():
                continue
            path = Path(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            if stat.S_ISLNK(info.external_attr >> 16):
                # e.g. `tests/pydantic_core` -> `../pydantic-core/tests`:
                os.symlink(zip_file.read(info).decode(), path)
            else:
                path.write_bytes(zip_file.read(info))


async def main(repo_zip_path: str, pydantic_core_wheel_url: str) -> None:
    print(f'Using pyodide version: {pyodide.__version__}')
    print('Extracting repo archive...')
    extract_repo(repo_zip_path)

    # Install the test dependencies the same way as in CI (see the `test-pyemscripten` job):
    py_version = f'{sys.version_info.major}{sys.version_info.minor}'
    pylock = tomllib.loads(Path(f'.github/pyodide/pylock.{py_version}.toml').read_text())
    wheel_urls = [package['wheels'][0]['url'] for package in pylock['packages']]
    print(f'Installing {len(wheel_urls)} dependencies and pydantic-core...')
    await micropip.install([*wheel_urls, pydantic_core_wheel_url], deps=False)
    importlib.invalidate_caches()

    # pydantic is imported from the repo archive (like `python -m pytest` would):
    sys.path.insert(0, os.getcwd())
    print('Running tests...')
    import pytest

    pytest.main(['--color=yes'])


try:
    await main(repo_zip_path, pydantic_core_wheel_url)  # noqa: F821,F704
except Exception:
    traceback.print_exc()
    raise
