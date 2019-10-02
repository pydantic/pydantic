#!/usr/bin/env python3
import re
import sys
from pathlib import Path

THIS_DIR = Path(__file__).parent

PROJECT_ROOT = THIS_DIR / '..' / '..'


def main():
    history = (PROJECT_ROOT / 'HISTORY.md').read_text()
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/samuelcolvin/pydantic/issues/\1)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)

    (PROJECT_ROOT / 'docs/changelog.md').write_text(history)

    sys.path.append(str(THIS_DIR.resolve()))
    from schema_mapping import build_schema_mappings

    build_schema_mappings()


if __name__ == '__main__':
    main()
