#!/usr/bin/env python3
import re
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

THIS_DIR = Path(__file__).parent
PROJECT_ROOT = THIS_DIR / '..' / '..'


def main():
    history = (PROJECT_ROOT / 'HISTORY.md').read_text()
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/pydantic/pydantic/issues/\1)', history)
    history = re.sub(r'(\s)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)

    (PROJECT_ROOT / 'docs/.changelog.md').write_text(history)

    version = SourceFileLoader('version', str(PROJECT_ROOT / 'pydantic/version.py')).load_module()
    (PROJECT_ROOT / 'docs/.version.md').write_text(f'Documentation for version: **v{version.VERSION}**\n')

    sys.path.append(str(THIS_DIR.resolve()))
    from schema_mapping import build_schema_mappings
    from exec_examples import exec_examples

    build_schema_mappings()
    return exec_examples()


if __name__ == '__main__':
    sys.exit(main())
