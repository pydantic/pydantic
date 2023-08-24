"""
Check that all `Usage docs` tags in docstrings link to the latest version of pydantic.
"""
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
PYDANTIC_DIR = ROOT_DIR / 'pydantic'
version_file = PYDANTIC_DIR / 'version.py'

version = re.search(br"VERSION = '(.*)'", version_file.read_bytes()).group(1)
version_major_minor = b'.'.join(version.split(b'.')[:2])

paths = sys.argv[1:]
errors = []
error_count = 0
for path_str in paths:
    path = ROOT_DIR / path_str
    if path.is_relative_to(PYDANTIC_DIR):
        file_errors = []
        b = path.read_bytes()
        for match in re.finditer(br'""" *usage.docs: ?https://docs\.pydantic\.dev/(.+?)/', b, flags=re.I):
            link_version = match.group(1)
            if link_version != version_major_minor:
                line_number = b[: match.start()].count(b'\n') + 1
                file_errors.append(f'    {line_number}: "{link_version.decode()}"')
                error_count += 1
        if file_errors:
            errors.append(f'  {path_str}:\n' + '\n'.join(file_errors))

if errors:
    expected = version_major_minor.decode()
    print(f'Found {error_count} usage docs links pointing to version that differ from "{expected}":')
    print('\n'.join(errors))
    sys.exit(1)
