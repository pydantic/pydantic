import base64
import re
import sys
import importlib
import traceback
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import micropip
import pytest

# this seems to be required for me on M1 Mac
sys.setrecursionlimit(200)

# compiled manually an uploaded to smokeshow, there seems to be no nice way of getting a file from a CI build
pydantic_core_wheel = (
    'https://smokeshow.helpmanual.io'
    '/4o4l4x0t2m6z1w4n6u4b/pydantic_core-0.0.1-cp310-cp310-emscripten_3_1_14_wasm32.whl'
)


async def main(tests_zip: str):
    print(f'Extracting test files (size: {len(tests_zip):,})...')
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

    await micropip.install(['dirty-equals', 'hypothesis', 'pytest-speed', pydantic_core_wheel])
    importlib.invalidate_caches()

    # print('installed packages:')
    # print(micropip.list())
    print('Running tests...')
    pytest.main()

try:
    await main(tests_zip)
except Exception as e:
    traceback.print_exc()
    raise
