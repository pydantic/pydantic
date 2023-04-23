import base64
import importlib
import re
import sys
import traceback
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import micropip
import pyodide
import pytest

# this seems to be required for me on M1 Mac
sys.setrecursionlimit(200)


async def main(tests_zip: str, tag_name: str):
    print(f'using pyodide version: {pyodide.__version__}')
    print(f'Extracting test files (size: {len(tests_zip):,})...')
    # File saved on the GH release
    pydantic_core_wheel = (
        'https://githubproxy.samuelcolvin.workers.dev/pydantic/pydantic-core/releases/'
        f'download/{tag_name}/pydantic_core-{tag_name.lstrip("v")}-cp311-cp311-emscripten_3_1_32_wasm32.whl'
    )
    zip_file = ZipFile(BytesIO(base64.b64decode(tests_zip)))
    count = 0
    for name in zip_file.namelist():
        if name.endswith('.py'):
            path, subs = re.subn(r'^pydantic-core-.+?/tests/', 'tests/', name)
            if subs:
                count += 1
                path = Path(path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with zip_file.open(name, 'r') as f:
                    path.write_bytes(f.read())

    print(f'Mounted {count} test files, installing dependencies...')

    await micropip.install(['dirty-equals', 'hypothesis', 'pytest-speed', 'pytest-mock', pydantic_core_wheel])
    importlib.invalidate_caches()

    # print('installed packages:')
    # print(micropip.list())
    print('Running tests...')
    pytest.main()


try:
    await main(tests_zip, pydantic_core_version)  # noqa: F821,F704
except Exception:
    traceback.print_exc()
    raise
