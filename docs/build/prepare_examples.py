#!/usr/bin/env python3
import importlib
import inspect
import re
import sys
import traceback
from pathlib import Path
from typing import Callable, List
from unittest.mock import patch


class MockPrint:
    def __init__(self, file: Path):
        self.file = file
        self.statements = []

    def __call__(self, *args):
        frame = inspect.currentframe().f_back.f_back.f_back
        if not self.file.samefile(frame.f_code.co_filename):
            # sys.stdout.write(' '.join(map(str, args)))
            raise RuntimeError("what's wrong here?")
        self.statements.append((frame.f_lineno, ' '.join(map(str, args))))


THIS_DIR = Path(__file__).parent
DOCS_DIR = THIS_DIR / '..'
EXAMPLES_ROOT = DOCS_DIR / 'examples'


def all_md_contents() -> str:
    file_contents = []
    for f in DOCS_DIR.glob('**/*.md'):
        file_contents.append(f.read_text())
    return '\n\n\n'.join(file_contents)


def main():
    errors = []
    all_md = all_md_contents()

    sys.path.append(str(EXAMPLES_ROOT))
    for file in sorted(EXAMPLES_ROOT.glob('*.py')):
        def error(desc: str):
            errors.append((file, desc))
            print(file.name, 'Error:', desc, file=sys.stderr)

        if file.name in {'settings.py', 'constrained_types.py', 'example2.py'}:
            # TODO fix these files
            continue

        if f'{{!./examples/{file.name}!}}' not in all_md:
            error('file not used anywhere')
        # print(file.name)
        mp = MockPrint(file)
        exc = None
        with patch('builtins.print') as mock_print:
            mock_print.side_effect = mp
            try:
                importlib.import_module(file.stem)
            except Exception:
                exc = traceback.format_exc()

        if exc is not None:
            error(exc)

        file_text = file.read_text()
        # if '\n\n\n':
        #     error('too many new lines')
        lines = file_text.split('\n')

        max_len = 80
        if max(len(l) for l in lines) > 80:
            error(f'lines longer than {max_len} characters')

        # check for print statements

        for line_no, text in reversed(mp.statements):
            insert_text = '#> ' + text.replace('\n', '\n#> ')
            lines.insert(line_no, insert_text)
        # debug(lines)
        # break  # while testing


if __name__ == '__main__':
    main()
