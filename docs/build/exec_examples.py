#!/usr/bin/env python3
import importlib
import inspect
import json
import os
import re
import shutil
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Any
from unittest.mock import patch

from devtools import PrettyFormat
from pydantic import BaseModel

THIS_DIR = Path(__file__).parent
DOCS_DIR = (THIS_DIR / '..').resolve()
EXAMPLES_ROOT = DOCS_DIR / 'examples'
TMP_EXAMPLES_ROOT = DOCS_DIR / '.tmp_examples'
MAX_LINE_LENGTH = int(re.search(r'max_line_length = (\d+)', (EXAMPLES_ROOT / '.editorconfig').read_text()).group(1))
LONG_LINE = 50
pformat = PrettyFormat(simple_cutoff=LONG_LINE)
PRINT_TO_JSON = {'example2.py', 'schema1.py', 'schema2.py', 'schema3.py', 'schema4.py'}
ENVIRON = {'my_auth_key': 'xxx', 'my_api_key': 'xxx'}


def to_string(value: Any) -> str:
    # attempt to build a pretty version
    if isinstance(value, BaseModel):
        s = str(value)
        if len(s) > LONG_LINE:
            indent = ' ' * (len(value.__class__.__name__) + 1)
            return value.__class__.__name__ + ' ' + f'\n{indent}'.join(f'{k}={v!r}' for k, v in value.__dict__.items())
        else:
            return s
    if isinstance(value, (dict, list, tuple, set)):
        return pformat(value)
    elif isinstance(value, str) and any(re.fullmatch(r, value, flags=re.DOTALL) for r in ['{".+}', r'\[.+\]']):
        try:
            obj = json.loads(value)
        except ValueError:
            # not JSON, not a problem
            pass
        else:
            s = json.dumps(obj)
            if len(s) > LONG_LINE:
                json.dumps(obj, indent=2)
            else:
                return s

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
        self.statements.append((frame.f_lineno, lines))


def all_md_contents() -> str:
    file_contents = []
    for f in DOCS_DIR.glob('**/*.md'):
        file_contents.append(f.read_text())
    return '\n\n\n'.join(file_contents)


def exec_examples():
    errors = []
    all_md = all_md_contents()
    new_files = {}
    os.environ.clear()
    os.environ.update(ENVIRON)

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

        if f'{{!.tmp_examples/{file.name}!}}' not in all_md:
            error('file not used anywhere')
        mp = MockPrint(file)
        with patch('builtins.print') as mock_print:
            mock_print.side_effect = mp
            try:
                importlib.import_module(file.stem)
            except Exception:
                tb = traceback.format_exception(*sys.exc_info())
                error(''.join(e for e in tb if '/pydantic/docs/examples/' in e or not e.startswith('  File ')))

        file_text = file.read_text()
        if '\n\n\n' in file_text:
            error('too many new lines')
        if not file_text.endswith('\n'):
            error('no trailing new line')
        lines = file_text.split('\n')

        if any(len(l) > MAX_LINE_LENGTH for l in lines):
            error(f'lines longer than {MAX_LINE_LENGTH} characters')

        if file.name in PRINT_TO_JSON:
            if len(mp.statements) != 1:
                error('should only have one print statement')
            new_files[file.stem + '.json'] = '\n'.join(mp.statements[0][1]) + '\n'

        else:
            for line_no, print_lines in reversed(mp.statements):
                if len(print_lines) > 2:
                    text = '"""\n{}\n"""'.format('\n'.join(print_lines))
                else:
                    text = '\n'.join('#> ' + l for l in print_lines)
                lines.insert(line_no, text)

        try:
            ignore_above = lines.index('# === ignore above')
        except ValueError:
            pass
        else:
            lines = lines[ignore_above + 1 :]

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
