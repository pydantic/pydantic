#!/usr/bin/env python3
import importlib
import inspect
import json
import re
import shutil
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Any
from unittest.mock import patch
from devtools import PrettyFormat


THIS_DIR = Path(__file__).parent
DOCS_DIR = (THIS_DIR / '..').resolve()
EXAMPLES_ROOT = DOCS_DIR / 'examples'
TMP_EXAMPLES_ROOT = DOCS_DIR / '.tmp_examples'
MAX_LINE_LENGTH = int(re.search(r'max_line_length = (\d+)', (EXAMPLES_ROOT / '.editorconfig').read_text()).group(1))
pformat = PrettyFormat(simple_cutoff=50)


def to_string(value: Any) -> str:
    # attempt to build a pretty version
    if isinstance(value, (dict, list, tuple, set)):
        return pformat(value)
    elif isinstance(value, str) and re.fullmatch('{".+"}', value, flags=re.DOTALL):
        return json.dumps(json.loads(value), indent=2)
    else:
        return str(value)


class MockPrint:
    def __init__(self, file: Path):
        self.file = file
        self.statements = []

    def __call__(self, *args):
        frame = inspect.currentframe().f_back.f_back.f_back
        if not self.file.samefile(frame.f_code.co_filename):
            # sys.stdout.write(' '.join(map(str, args)))
            raise RuntimeError("what's wrong here?")
        s = ' '.join(map(to_string, args))

        lines = []
        for line in s.split('\n'):
            if len(line) > MAX_LINE_LENGTH - 3:
                lines += textwrap.wrap(line, width=MAX_LINE_LENGTH - 3)
            else:
                lines.append(line)
        if len(lines) > 2:
            text = '"""\n{}\n"""'.format('\n'.join(lines))
        else:
            text = '\n'.join('#> ' + l for l in lines)
        self.statements.append((frame.f_lineno, text))


def all_md_contents() -> str:
    file_contents = []
    for f in DOCS_DIR.glob('**/*.md'):
        file_contents.append(f.read_text())
    return '\n\n\n'.join(file_contents)


def exec_examples():
    errors = []
    all_md = all_md_contents()
    new_files = {}

    sys.path.append(str(EXAMPLES_ROOT))
    for file in sorted(EXAMPLES_ROOT.iterdir()):

        def error(desc: str):
            errors.append((file, desc))
            sys.stderr.write(f'{file.name} Error: {desc}\n')

        if not file.is_file():
            # __pycache__, maybe others
            continue

        if file.suffix != '.py':
            # just copy
            new_files[file.name] = file.read_text()
            continue

        if file.name in {'settings.py', 'constrained_types.py', 'example2.py'}:
            # TODO fix these files
            # just copy for now
            new_files[file.name] = file.read_text()
            continue

        if f'{{!.tmp_examples/{file.name}!}}' not in all_md:
            error('file not used anywhere')
        # print(file.name)
        mp = MockPrint(file)
        with patch('builtins.print') as mock_print:
            mock_print.side_effect = mp
            try:
                importlib.import_module(file.stem)
            except Exception:
                error(traceback.format_exc())

        file_text = file.read_text()
        # if '\n\n\n':
        #     error('too many new lines')
        lines = file_text.split('\n')

        if any(len(l) > MAX_LINE_LENGTH for l in lines):
            error(f'lines longer than {MAX_LINE_LENGTH} characters')

        # check for print statements

        for line_no, text in reversed(mp.statements):
            lines.insert(line_no, text)
        # debug(lines)
        # break  # while testing
        new_files[file.name] = '\n'.join(lines)

    if errors:
        return 1

    if TMP_EXAMPLES_ROOT.exists():
        shutil.rmtree(TMP_EXAMPLES_ROOT)

    print(f'writing {len(new_files)} example files to {TMP_EXAMPLES_ROOT}')
    TMP_EXAMPLES_ROOT.mkdir()
    for file_name, content in new_files.items():
        (TMP_EXAMPLES_ROOT / file_name).write_text(content)
    return 0


if __name__ == '__main__':
    sys.exit(exec_examples())
