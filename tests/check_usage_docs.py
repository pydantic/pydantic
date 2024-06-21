"""
Check that all `Usage docs` tags in docstrings link to the latest version of pydantic.
"""

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
PYDANTIC_DIR = ROOT_DIR / 'pydantic'
version_file = PYDANTIC_DIR / 'version.py'


version = re.search(rb"VERSION = '(.*)'", version_file.read_bytes()).group(1)
version_major_minor = b'.'.join(version.split(b'.')[:2])
expected_base = b'https://docs.pydantic.dev/' + version_major_minor + b'/'

paths = sys.argv[1:]
error_count = 0
for path_str in paths:
    path = ROOT_DIR / path_str
    b = path.read_bytes()

    changed = 0

    def sub(m: re.Match) -> bytes:
        global changed
        if m.group(2) != expected_base:
            changed += 1
            return m.group(1) + expected_base
        else:
            return m.group(0)

    b = re.sub(rb'(""" *usage.docs: *)(https://.+?/.+?/)', sub, b, flags=re.I)
    if changed:
        error_count += changed
        path.write_bytes(b)
        plural = 's' if changed > 1 else ''
        print(f'{path_str:50} {changed} usage docs link{plural} updated')

if error_count:
    sys.exit(1)
