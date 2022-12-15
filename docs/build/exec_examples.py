#!/usr/bin/env python3
from __future__ import annotations
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from ansi2html import Ansi2HTMLConverter
from devtools import PrettyFormat

THIS_DIR = Path(__file__).parent
DOCS_DIR = (THIS_DIR / '..').resolve()
EXAMPLES_DIR = DOCS_DIR / 'examples'
TMP_EXAMPLES_DIR = DOCS_DIR / '.tmp_examples'
UPGRADED_TMP_EXAMPLES_DIR = TMP_EXAMPLES_DIR / 'upgraded'

MAX_LINE_LENGTH = int(
    re.search(r'max_line_length = (\d+)', (EXAMPLES_DIR / '.editorconfig').read_text()).group(1)  # type: ignore
)
LONG_LINE = 50
LOWEST_VERSION = (3, 7)
HIGHEST_VERSION = (3, 10)
pformat = PrettyFormat(simple_cutoff=LONG_LINE)
Error = Callable[..., None]
Version = tuple[int, int]

PYTHON_CODE_MD_TMPL = """
=== "Python {version} and above"

    ```py
{code}
    ```
""".strip()
JSON_OUTPUT_MD_TMPL = """

Outputs:
```json
{output}
```
"""


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
    def __init__(self, file: Path) -> None:
        self.file = file
        self.statements: list[tuple[int, str]] = []

    def __call__(self, *args: Any, sep: str = ' ', **kwargs: Any) -> None:
        frame = sys._getframe(4) if sys.version_info >= (3, 8) else sys._getframe(3)

        if not self.file.samefile(frame.f_code.co_filename):
            # happens when index_error.py imports index_main.py
            return
        s = sep.join(map(to_string, args))

        self.statements.append((frame.f_lineno, s))


class MockPath:
    def read_text(self, *args: Any, **kwargs: Any) -> str:
        return '{"foobar": "spam"}'


def build_print_lines(s: str, max_len_reduction: int = 0) -> list[str]:
    print_lines = []
    max_len = MAX_LINE_LENGTH - 3 - max_len_reduction
    for line in s.split('\n'):
        if len(line) > max_len:
            print_lines += textwrap.wrap(line, width=max_len)
        else:
            print_lines.append(line)
    return print_lines


def build_print_statement(line_no: int, s: str, lines: list[str]) -> None:
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


def gen_ansi_output() -> None:

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
requires_re = re.compile(r'^# requires: *(.+)\n', flags=re.M | re.I)
required_py_re = re.compile(r'^# *requires *python *(\d+).(\d+)', flags=re.M)


def should_execute(file_name: str, file_text: str) -> tuple[str, bool, Version]:
    m = required_py_re.search(file_text)
    if m:
        lowest_version = (int(m.groups()[0]), int(m.groups()[1]))
        if sys.version_info >= lowest_version:
            return required_py_re.sub('', file_text), True, lowest_version
        else:
            v = '.'.join(m.groups())
            print(f'WARNING: {file_name} requires python {v}, not running')
            return (
                required_py_re.sub(f'# requires python {v}, NOT EXECUTED!', file_text),
                False,
                lowest_version,
            )
    elif dont_execute_re.search(file_text):
        return dont_execute_re.sub('', file_text), False, LOWEST_VERSION
    return file_text, True, LOWEST_VERSION


def should_upgrade(file_text: str) -> tuple[str, bool]:
    if dont_upgrade_re.search(file_text):
        return dont_upgrade_re.sub('', file_text), False
    return file_text, True


def get_requirements(file_text: str) -> tuple[str, str | None]:
    m = requires_re.search(file_text)
    if m:
        return requires_re.sub('', file_text), m.groups()[0]
    return file_text, None


def exec_file(file: Path, file_text: str, error: Error) -> tuple[list[str], str | None]:
    no_print_intercept_re = re.compile(r'^# no-print-intercept\n', flags=re.M)
    print_intercept = not bool(no_print_intercept_re.search(file_text))
    if not print_intercept:
        file_text = no_print_intercept_re.sub('', file_text)

    if file.stem in sys.modules:
        del sys.modules[file.stem]
    mp = MockPrint(file)
    mod = None

    with patch.object(Path, 'read_text', MockPath.read_text), patch('builtins.print') as patch_print:
        if print_intercept:
            patch_print.side_effect = mp
        try:
            mod = importlib.import_module(file.stem)
        except Exception:
            tb = traceback.format_exception(*sys.exc_info())
            error(''.join(e for e in tb if '/pydantic/docs/examples/' in e or not e.startswith('  File ')))

    if mod and mod.__file__ != str(file):
        error(f'module path "{mod.__file__}" is not same as "{file}", name may shadow another module?')

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


def filter_lines(lines: list[str], error: Any) -> tuple[list[str], bool]:
    ignored_above = False
    try:
        ignore_above = lines.index('# ignore-above')
    except ValueError:
        pass
    else:
        ignored_above = True
        lines = lines[ignore_above + 1 :]

    try:
        ignore_below = lines.index('# ignore-below')
    except ValueError:
        pass
    else:
        lines = lines[:ignore_below]

    lines = '\n'.join(lines).split('\n')
    if any(len(line) > MAX_LINE_LENGTH for line in lines):
        error(f'lines longer than {MAX_LINE_LENGTH} characters')
    return lines, ignored_above


def upgrade_code(content: str, min_version: Version = HIGHEST_VERSION) -> str:
    import pyupgrade._main  # type: ignore
    import autoflake  # type: ignore

    upgraded = pyupgrade._main._fix_plugins(
        content,
        settings=pyupgrade._main.Settings(
            min_version=min_version,
            keep_percent_format=True,
            keep_mock=False,
            keep_runtime_typing=True,
        ),
    )
    upgraded = autoflake.fix_code(upgraded, remove_all_unused_imports=True)
    return upgraded


def ensure_used(file: Path, all_md: str, error: Error) -> None:
    """Ensures that example is used appropriately"""
    file_tmpl = '{{!.tmp_examples/{}!}}'
    md_name = file.stem + '.md'
    if file_tmpl.format(md_name) not in all_md:
        if file_tmpl.format(file.name) in all_md:
            error(
                f'incorrect usage, change filename to {md_name!r} in docs.'
                "make sure you don't specify ```py code blocks around examples,"
                'they are automatically generated now.'
            )
        else:
            error(
                'file not used anywhere. correct usage:',
                file_tmpl.format(md_name),
            )


def check_style(file_text: str, error: Error) -> None:
    if '\n\n\n\n' in file_text:
        error('too many new lines')
    if not file_text.endswith('\n'):
        error('no trailing new line')
    if re.search('^ *# *>', file_text, flags=re.M):
        error('contains comments with print output, please remove')


def populate_upgraded_versions(file: Path, file_text: str, lowest_version: Version) -> list[tuple[Path, str, Version]]:
    versions = []
    major, minor = lowest_version
    assert major == HIGHEST_VERSION[0], 'Wow, Python 4 is out? Congrats!'
    upgraded_file_text = file_text
    while minor < HIGHEST_VERSION[1]:
        minor += 1
        new_file_text = upgrade_code(file_text, min_version=(major, minor))
        if upgraded_file_text != new_file_text:
            upgraded_file_text = new_file_text
            new_file = UPGRADED_TMP_EXAMPLES_DIR / (file.stem + f'_{major}_{minor}' + file.suffix)
            new_file.write_text(upgraded_file_text)
            versions.append((new_file, upgraded_file_text, (major, minor)))
    return versions


def exec_examples() -> int:  # noqa: C901 (I really don't want to decompose it any further)
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
    sys.path.append(str(EXAMPLES_DIR))
    if sys.version_info < HIGHEST_VERSION:
        print("WARNING: examples for 3.10+ requires python 3.10. They won't be executed")
    else:
        UPGRADED_TMP_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        sys.path.append(str(UPGRADED_TMP_EXAMPLES_DIR))

    for file in sorted(EXAMPLES_DIR.iterdir()):
        markdown_name = file.stem + '.md'

        def error(*desc: str) -> None:
            errors.append((file, desc))
            previous_frame = sys._getframe(1)
            filename = Path(previous_frame.f_globals['__file__']).relative_to(Path.cwd())
            location = f'{filename}:{previous_frame.f_lineno}'
            sys.stderr.write(f'{location}: error in {file.relative_to(Path.cwd())}:\n{" ".join(desc)}\n')

        if not file.is_file():
            # __pycache__, maybe others
            continue

        if file.suffix != '.py':
            # just copy
            new_files[file.name] = file.read_text()
            continue

        file_text = file.read_text('utf-8')
        ensure_used(file, all_md, error)
        check_style(file_text, error)

        file_text, execute, lowest_version = should_execute(file.name, file_text)
        file_text, upgrade = should_upgrade(file_text)
        file_text, requirements = get_requirements(file_text)

        if upgrade and upgrade_code(file_text, min_version=lowest_version) != file_text:
            error("pyupgrade would upgrade file. If it's not desired, add '# dont-upgrade' line at the top of the file")

        versions: list[tuple[Path, str, Version]] = [(file, file_text, lowest_version)]
        if upgrade:
            versions.extend(populate_upgraded_versions(file, file_text, lowest_version))

        json_outputs: set[str | None] = set()
        should_run_as_is = not requirements
        final_content: list[str] = []
        for file, file_text, lowest_version in versions:
            if execute and sys.version_info >= lowest_version:
                lines, json_output = exec_file(file, file_text, error)
                json_outputs.add(json_output)
            else:
                lines = file_text.split('\n')

            lines, ignored_lines_before_script = filter_lines(lines, error)
            should_run_as_is = should_run_as_is and not ignored_lines_before_script

            final_content.append(
                PYTHON_CODE_MD_TMPL.format(
                    version='.'.join(map(str, lowest_version)),
                    code=textwrap.indent('\n'.join(lines), '    '),
                )
            )

        if should_run_as_is:
            final_content.append('_(This script is complete, it should run "as is")_')
        elif requirements:
            final_content.append(f'_(This script requires {requirements})_')
        else:
            error(
                'script may not run as is, but requirements were not specified.',
                'specify `# requires: ` in the end of the script',
            )

        if len(json_outputs) > 1:
            error('json output should not differ between versions')

        if json_outputs:
            json_output, *_ = json_outputs
            if json_output:
                final_content.append(JSON_OUTPUT_MD_TMPL.format(output=json_output))

        new_files[markdown_name] = '\n'.join(final_content)

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
