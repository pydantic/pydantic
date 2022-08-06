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
from typing import Any, List, Tuple
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
        if sys.version_info >= (3, 8):
            frame = frame.f_back
        if not self.file.samefile(frame.f_code.co_filename):
            # happens when index_error.py imports index_main.py
            return
        s = ' '.join(map(to_string, args))

        self.statements.append((frame.f_lineno, s))


class MockPath:

    def read_text(self, *args, **kwargs) -> str:
        return '{"foobar": "spam"}'


def build_print_lines(s: str, max_len_reduction: int = 0):
    print_lines = []
    max_len = MAX_LINE_LENGTH - 3 - max_len_reduction
    for line in s.split('\n'):
        if len(line) > max_len:
            print_lines += textwrap.wrap(line, width=max_len)
        else:
            print_lines.append(line)
    return print_lines


def build_print_statement(line_no: int, s: str, lines: List[str]) -> None:
    indent = ''
    for back in range(1, 100):
        m = re.search(r'^( *)print\(', lines[line_no - back])
        if m:
            indent = m.group(1)
            break
    print_lines = build_print_lines(s, len(indent))

    if len(print_lines) > 2:
        text = textwrap.indent('"""\n{}\n"""'.format('\n'.join(print_lines)), indent)
    else:
        text = '\n'.join(f'{indent}#> {line}' for line in print_lines)
    lines.insert(line_no, text)


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


dont_execute_re = re.compile(r'^# dont-execute\n', flags=re.M | re.I)
dont_upgrade_re = re.compile(r'^# dont-upgrade\n', flags=re.M | re.I)
required_py_re = re.compile(r'^# *requires *python *(\d+).(\d+)', flags=re.M)


def should_execute(file_name: str, file_text: str) -> Tuple[str, bool, Tuple[str, str]]:
    m = required_py_re.search(file_text)
    if m:
        if sys.version_info >= tuple(map(int, m.groups())):
            return required_py_re.sub('', file_text), True, m.groups()
        else:
            v = '.'.join(m.groups())
            print(f'WARNING: {file_name} requires python {v}, not running')
            return (
                required_py_re.sub(f'# requires python {v}, NOT EXECUTED!', file_text),
                False,
                m.groups(),
            )
    elif dont_execute_re.search(file_text):
        return dont_execute_re.sub('', file_text), False, ("3", "7")
    return file_text, True, ("3", "7")


def should_upgrade(file_text: str) -> Tuple[str, bool]:
    if dont_upgrade_re.search(file_text):
        return dont_upgrade_re.sub('', file_text), False
    return file_text, True


def exec_file(file, file_text, error, new_files):
    no_print_intercept_re = re.compile(r'^# no-print-intercept\n', flags=re.M)
    print_intercept = not bool(no_print_intercept_re.search(file_text))
    if not print_intercept:
        file_text = no_print_intercept_re.sub('', file_text)

    if file.stem in sys.modules:
        del sys.modules[file.stem]
    mp = MockPrint(file)
    mod = None

    with patch.object(Path, "read_text", MockPath.read_text), patch(
        'builtins.print'
    ) as patch_print:
        if print_intercept:
            patch_print.side_effect = mp
        try:
            mod = importlib.import_module(file.stem)
        except Exception:
            tb = traceback.format_exception(*sys.exc_info())
            error(
                ''.join(
                    e
                    for e in tb
                    if '/pydantic/docs/examples/' in e or not e.startswith('  File ')
                )
            )

    if mod and Path(mod.__file__) != file:
        error(
            f'module path "{mod.__file__}" is not same as "{file}", name may shadow another module?'
        )

    lines = file_text.split('\n')

    to_json_line = '# output-json'
    if to_json_line in lines:
        lines = [line for line in lines if line != to_json_line]
        if len(mp.statements) != 1:
            error('should have exactly one print statement')
        print_lines = build_print_lines(mp.statements[0][1])
        return lines, '\n'.join(print_lines) + '\n'
    else:
        for line_no, print_string in reversed(mp.statements):
            build_print_statement(line_no, print_string, lines)
        return lines, None


def filter_lines(lines: List[str], error: Any) -> Tuple[List[str], bool]:
    changed = False
    try:
        ignore_above = lines.index('# ignore-above')
    except ValueError:
        pass
    else:
        changed = True
        lines = lines[ignore_above + 1 :]

    try:
        ignore_below = lines.index('# ignore-below')
    except ValueError:
        pass
    else:
        changed = True
        lines = lines[:ignore_below]

    lines = '\n'.join(lines).split('\n')
    if any(len(l) > MAX_LINE_LENGTH for l in lines):
        error(f'lines longer than {MAX_LINE_LENGTH} characters')
    return lines, changed


def upgrade_code(content: str, min_version=(3, 10)) -> str:
    from pyupgrade._main import Settings, _fix_plugins
    from autoflake import fix_code

    upgraded = _fix_plugins(
        content,
        settings=Settings(
            min_version=min_version,
            keep_percent_format=True,
            keep_mock=False,
            keep_runtime_typing=False,
        ),
    )

    upgraded = fix_code(upgraded, remove_all_unused_imports=True)
    return upgraded


def exec_examples():
    errors = []
    all_md = all_md_contents()
    new_files = {}
    os.environ.update(
        {
            'my_auth_key': 'xxx',
            'my_api_key': 'xxx',
            'database_dsn': 'postgres://postgres@localhost:5432/env_db',
            'v0': '0',
            'sub_model': '{"v1": "json-1", "v2": "json-2"}',
            'sub_model__v2': 'nested-2',
            'sub_model__v3': '3',
            'sub_model__deep__v4': 'v4',
        }
    )
    if sys.version_info < (3, 10):
        execute_latest_version = False
        print(
            "WARNING: examples for 3.10+ requires python 3.10. They won't be executed"
        )
    else:
        example_3_10_dir = TMP_EXAMPLES_DIR / "3.10"
        example_3_10_dir.mkdir(exist_ok=True)
        sys.path.append(str(example_3_10_dir))
        execute_latest_version = True

    sys.path.append(str(EXAMPLES_DIR))
    for file in sorted(EXAMPLES_DIR.iterdir()):

        def error(*desc: str):
            errors.append((file, desc))
            previous_frame = sys._getframe(-2).f_back
            location = f'{Path(previous_frame.f_globals["__file__"]).relative_to(Path.cwd())}:{previous_frame.f_lineno}'
            sys.stderr.write(f'{location}: error in {file.name}: {" ".join(desc)}\n')

        if not file.is_file():
            # __pycache__, maybe others
            continue

        if file.suffix != '.py':
            # just copy
            new_files[file.name] = file.read_text()
            continue

        file_tmpl = '{{!.tmp_examples/{}!}}'
        if file_tmpl.format(file.stem + '.md') not in all_md:
            if file_tmpl.format(file.name) in all_md:
                error(
                    f'incorrect usage, change filename to {file.stem + ".md"!r} in docs'
                )
            else:
                error(
                    'file not used anywhere. correct usage:',
                    file_tmpl.format(file.stem + 'md'),
                )

        file_text = file.read_text('utf-8')
        if '\n\n\n\n' in file_text:
            error('too many new lines')
        if not file_text.endswith('\n'):
            error('no trailing new line')
        if re.search('^ *# *>', file_text, flags=re.M):
            error('contains comments with print output, please remove')

        file_text, execute, lowest_version = should_execute(file.name, file_text)
        file_text, upgrade = should_upgrade(file_text)
        if upgrade and upgrade_code(file_text, min_version=(3, 7)) != file_text:
            error(
                "pyupgrade would upgrade file. If it's not desired, add '# dont-upgrade' line at the top of the file"
            )

        if upgrade and tuple(map(int, lowest_version)) < (3, 10):
            upgraded = upgrade_code(file_text)
            upgraded_lines = upgraded.split('\n')
        else:
            upgraded = None
            upgraded_lines = []
            upgraded_json_output = None

        if execute:
            lines, json_output = exec_file(file, file_text, error, new_files)
            if upgraded and execute_latest_version:
                # create temp module to execute
                new_file = example_3_10_dir / (file.stem + "3_10" + file.suffix)
                new_file.write_text(upgraded)
                upgraded_lines, upgraded_json_output = exec_file(
                    new_file, upgraded, error, new_files
                )
        else:
            upgraded_json_output = None
            lines = file_text.split('\n')

        if json_output != upgraded_json_output:
            error('json output should not differ between versions')

        lines, changed = filter_lines(lines, error)
        upgraded_lines, _ = filter_lines(upgraded_lines, error)

        new_content = '\n'.join(lines)

        final_content = f"""
=== "Python {'.'.join(lowest_version)} and above"    
    ```py
{textwrap.indent(new_content, "    ")}
    ```
"""
        if upgraded_lines and upgraded_lines != lines:
            upgraded_content = '\n'.join(upgraded_lines)
            final_content += f"""
=== "Python 3.10 and above"

    ```py
{textwrap.indent(upgraded_content, "    ")}
    ```
"""
            if not changed:
                final_content += (
                    '_(These scripts are complete, it should run "as is")_\n'
                )
        else:
            if not changed:
                final_content += '_(This script is complete, it should run "as is")_\n'

        if json_output:
            final_content += f"""
Outputs:
```json
{json_output}
```
"""

        new_files[file.stem + '.md'] = final_content

    if errors:
        print(f'\n{len(errors)} errors, not writing files\n')
        return 1

    if TMP_EXAMPLES_DIR.exists():
        shutil.rmtree(TMP_EXAMPLES_DIR)

    print(f'writing {len(new_files)} example files to {TMP_EXAMPLES_DIR}')
    TMP_EXAMPLES_DIR.mkdir()
    for file_name, content in new_files.items():
        (TMP_EXAMPLES_DIR / file_name).write_text(content, 'utf-8')
    gen_ansi_output()
    return 0


if __name__ == '__main__':
    sys.exit(exec_examples())
