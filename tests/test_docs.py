from __future__ import annotations as _annotations

import os
import platform
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples

from pydantic.errors import PydanticErrorCodes

INDEX_MAIN = None
DOCS_ROOT = Path(__file__).parent.parent / 'docs'


def skip_docs_tests():
    if sys.platform not in {'linux', 'darwin'}:
        return 'not in linux or macos'

    if platform.python_implementation() != 'CPython':
        return 'not cpython'

    try:
        import hypothesis  # noqa: F401
    except ImportError:
        return 'hypothesis not installed'

    try:
        import devtools  # noqa: F401
    except ImportError:
        return 'devtools not installed'

    try:
        import sqlalchemy  # noqa: F401
    except ImportError:
        return 'sqlalchemy not installed'

    try:
        import ansi2html  # noqa: F401
    except ImportError:
        return 'ansi2html not installed'


class GroupModuleGlobals:
    def __init__(self) -> None:
        self.name = None
        self.module_dict: dict[str, str] = {}

    def get(self, name: str | None):
        if name is not None and name == self.name:
            return self.module_dict

    def set(self, name: str | None, module_dict: dict[str, str]):
        self.name = name
        if self.name is None:
            self.module_dict = None
        else:
            self.module_dict = module_dict


group_globals = GroupModuleGlobals()


class MockedDatetime(datetime):
    @classmethod
    def now(cls, *args, **kwargs):
        return datetime(2032, 1, 2, 3, 4, 5, 6)


skip_reason = skip_docs_tests()


def print_callback(print_statement: str) -> str:
    return re.sub(r'(https://errors.pydantic.dev)/.+?/', r'\1/2/', print_statement)


@pytest.mark.filterwarnings('ignore:(parse_obj_as|schema_json_of|schema_of) is deprecated.*:DeprecationWarning')
@pytest.mark.skipif(bool(skip_reason), reason=skip_reason or 'not skipping')
@pytest.mark.parametrize('example', find_examples(str(DOCS_ROOT), skip=sys.platform == 'win32'), ids=str)
def test_docs_examples(example: CodeExample, eval_example: EvalExample, tmp_path: Path, mocker):  # noqa: C901
    global INDEX_MAIN
    if example.path.name == 'index.md':
        if INDEX_MAIN is None:
            INDEX_MAIN = example.source
        else:
            (tmp_path / 'index_main.py').write_text(INDEX_MAIN)
            sys.path.append(str(tmp_path))

    if example.path.name == 'devtools.md':
        pytest.skip('tested below')

    eval_example.print_callback = print_callback

    prefix_settings = example.prefix_settings()
    test_settings = prefix_settings.get('test')
    lint_settings = prefix_settings.get('lint')
    if test_settings == 'skip' and lint_settings == 'skip':
        pytest.skip('both test and lint skipped')

    requires_settings = prefix_settings.get('requires')
    if requires_settings:
        major, minor = map(int, requires_settings.split('.'))
        if sys.version_info < (major, minor):
            pytest.skip(f'requires python {requires_settings}')

    group_name = prefix_settings.get('group')

    if '# ignore-above' in example.source:
        eval_example.set_config(ruff_ignore=['E402'])
    if group_name:
        eval_example.set_config(ruff_ignore=['F821'])

    if lint_settings != 'skip':
        if eval_example.update_examples:
            eval_example.format(example)
        else:
            eval_example.lint(example)

    if test_settings == 'skip':
        return

    group_name = prefix_settings.get('group')
    d = group_globals.get(group_name)

    mocker.patch('datetime.datetime', MockedDatetime)
    mocker.patch('random.randint', return_value=3)

    xfail = None
    if test_settings and test_settings.startswith('xfail'):
        xfail = test_settings[5:].lstrip(' -')

    rewrite_assertions = prefix_settings.get('rewrite_assert', 'true') == 'true'

    try:
        if test_settings == 'no-print-intercept':
            d2 = eval_example.run(example, module_globals=d, rewrite_assertions=rewrite_assertions)
        elif eval_example.update_examples:
            d2 = eval_example.run_print_update(example, module_globals=d, rewrite_assertions=rewrite_assertions)
        else:
            d2 = eval_example.run_print_check(example, module_globals=d, rewrite_assertions=rewrite_assertions)
    except BaseException as e:  # run_print_check raises a BaseException
        if xfail:
            pytest.xfail(f'{xfail}, {type(e).__name__}: {e}')
        raise
    else:
        if xfail:
            pytest.fail('expected xfail')
        group_globals.set(group_name, d2)


@pytest.mark.skipif(bool(skip_reason), reason=skip_reason or 'not skipping')
@pytest.mark.parametrize(
    'example', find_examples(str(DOCS_ROOT / 'integrations/devtools.md'), skip=sys.platform == 'win32'), ids=str
)
def test_docs_devtools_example(example: CodeExample, eval_example: EvalExample, tmp_path: Path):
    from ansi2html import Ansi2HTMLConverter

    if eval_example.update_examples:
        eval_example.format(example)
    else:
        eval_example.lint(example)

    with NamedTemporaryFile(mode='w', suffix='.py') as f:
        f.write(example.source)
        f.flush()
        os.environ['PY_DEVTOOLS_HIGHLIGHT'] = 'true'
        p = subprocess.run((sys.executable, f.name), stdout=subprocess.PIPE, check=True, encoding='utf8')

    conv = Ansi2HTMLConverter()

    # replace ugly file path with "devtools_example.py"
    output = re.sub(r'/.+?\.py', 'devtools_example.py', p.stdout)
    output_html = conv.convert(output, full=False)
    output_html = (
        '<!-- DO NOT EDIT MANUALLY: '
        'Generated by tests/test_docs.py::test_docs_devtools_example for use in docs -->\n'
        f'{output_html}'
    )
    output_file = DOCS_ROOT / 'plugins/devtools_output.html'

    if eval_example.update_examples:
        output_file.write_text(output_html)
    elif not output_file.exists():
        pytest.fail(f'output file {output_file} does not exist')
    else:
        assert output_html == output_file.read_text()


def test_error_codes():
    error_text = (DOCS_ROOT / 'usage/errors.md').read_text()

    code_error_codes = PydanticErrorCodes.__args__

    documented_error_codes = tuple(re.findall(r'^## .+ \{#(.+?)}$', error_text, flags=re.MULTILINE))

    assert code_error_codes == documented_error_codes, 'Error codes in code and docs do not match'
