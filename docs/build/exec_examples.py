#!/usr/bin/env python3
import importlib
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Any
from unittest.mock import patch

from ansi2html import Ansi2HTMLConverter
from devtools import PrettyFormat

THIS_DIR = Path(__file__).parent
DOCS_DIR = (THIS_DIR / '..').resolve()
EXAMPLES_DIR = DOCS_DIR / 'examples'
TMP_EXAMPLES_DIR = DOCS_DIR / '.tmp_examples'
MAX_LINE_LENGTH = int(re.search(r'max_line_length = (\d+)', (EXAMPLES_DIR / '.editorconfig').read_text()).group(1))
LONG_LINE = 50
pformat = PrettyFormat(simple_cutoff=LONG_LINE)


def to_string(value: Any) -> str:
    # attempt to build a pretty equivalent of the print output
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

    def __call__(self, *args, file=None, flush=None):
        frame = inspect.currentframe().f_back.f_back.f_back
        if not self.file.samefile(frame.f_code.co_filename):
            # happens when index_error import index_main
            return
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


def gen_ansi_output():

    conv = Ansi2HTMLConverter()

    input_file = EXAMPLES_DIR / 'devtools_main.py'
    os.environ['PY_DEVTOOLS_HIGHLIGHT'] = 'true'
    p = subprocess.run((sys.executable, str(input_file)), stdout=subprocess.PIPE, check=True, encoding='utf8')
    html = conv.convert(p.stdout, full=False).strip('\r\n')
    full_html = f'<div class="terminal">\n<pre class="terminal-content">\n{html}\n</pre>\n</div>'
    path = TMP_EXAMPLES_DIR / f'{input_file.stem}.html'
    path.write_text(full_html)
    print(f'generated ansi output to {path}')


def exec_examples():
    errors = []
    all_md = all_md_contents()
    new_files = {}
    os.environ.clear()
    os.environ.update({'my_auth_key': 'xxx', 'my_api_key': 'xxx'})

    sys.path.append(str(EXAMPLES_DIR))
    for file in sorted(EXAMPLES_DIR.iterdir()):

        def error(desc: str):
            errors.append((file, desc))
            sys.stderr.write(f'error in {file.name}: {desc}\n')

        if not file.is_file():
            # __pycache__, maybe others
            continue

        if file.suffix != '.py':
            # just copy
            new_files[file.name] = file.read_text()
            continue

        if f'{{!.tmp_examples/{file.name}!}}' not in all_md:
            error('file not used anywhere')

        file_text = file.read_text()
        if '\n\n\n' in file_text:
            error('too many new lines')
        if not file_text.endswith('\n'):
            error('no trailing new line')
        if re.search('^ *# *>', file_text, flags=re.M):
            error('contains comments with print output, please remove')

        dont_execute_re = re.compile(r'^# dont-execute\n', flags=re.M)
        if dont_execute_re.search(file_text):
            lines = dont_execute_re.sub('', file_text).split('\n')
        else:
            no_print_intercept_re = re.compile(r'^# no-print-intercept\n', flags=re.M)
            no_print_intercept = bool(no_print_intercept_re.search(file_text))
            if no_print_intercept:
                file_text = no_print_intercept_re.sub('', file_text)

            mp = MockPrint(file)
            mod = None
            with patch('builtins.print') as mock_print:
                if not no_print_intercept:
                    mock_print.side_effect = mp
                try:
                    mod = importlib.import_module(file.stem)
                except Exception:
                    tb = traceback.format_exception(*sys.exc_info())
                    error(''.join(e for e in tb if '/pydantic/docs/examples/' in e or not e.startswith('  File ')))

            if mod and not mod.__file__.startswith(str(EXAMPLES_DIR)):
                error(f'module path "{mod.__file__}" not inside "{EXAMPLES_DIR}", name may shadow another module?')

            lines = file_text.split('\n')

            to_json_line = '# output-json'
            if to_json_line in lines:
                lines = [line for line in lines if line != to_json_line]
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
            ignore_above = lines.index('# ignore-above')
        except ValueError:
            pass
        else:
            lines = lines[ignore_above + 1 :]

        lines = '\n'.join(lines).split('\n')
        if any(len(l) > MAX_LINE_LENGTH for l in lines):
            error(f'lines longer than {MAX_LINE_LENGTH} characters')

        new_files[file.name] = '\n'.join(lines)

    if errors:
        print(f'\n{len(errors)} errors, not writing files\n')
        return 1

    if TMP_EXAMPLES_DIR.exists():
        shutil.rmtree(TMP_EXAMPLES_DIR)

    print(f'writing {len(new_files)} example files to {TMP_EXAMPLES_DIR}')
    TMP_EXAMPLES_DIR.mkdir()
    for file_name, content in new_files.items():
        (TMP_EXAMPLES_DIR / file_name).write_text(content)
    gen_ansi_output()
    return 0


if __name__ == '__main__':
    sys.exit(exec_examples())
