from __future__ import annotations

import importlib
import os
import re
import sys
from collections.abc import Collection
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from _pytest.mark import Mark, MarkDecorator
from _pytest.mark.structures import ParameterSet
from typing_extensions import TypeAlias

# Pyright doesn't like try/expect blocks for imports:
if TYPE_CHECKING:
    from mypy import api as mypy_api
    from mypy.version import __version__ as mypy_version

    from pydantic.version import parse_mypy_version
else:
    try:
        from mypy import api as mypy_api
        from mypy.version import __version__ as mypy_version

        from pydantic.version import parse_mypy_version

    except ImportError:
        mypy_api = None
        mypy_version = None

        parse_mypy_version = lambda _: (0,)  # noqa: E731


MYPY_VERSION_TUPLE = parse_mypy_version(mypy_version)
PYDANTIC_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = PYDANTIC_ROOT / 'tests/mypy/outputs'

pytestmark = pytest.mark.skipif(
    '--test-mypy' not in sys.argv
    and os.environ.get('PYCHARM_HOSTED') != '1',  # never skip when running via the PyCharm runner
    reason='Test only with "--test-mypy" flag',
)

# This ensures mypy can find the test files, no matter where tests are run from:
os.chdir(Path(__file__).parent.parent.parent)


# Type hint taken from the signature of `pytest.param`:
Marks: TypeAlias = 'MarkDecorator | Collection[MarkDecorator | Mark]'


def build_cases(
    configs: list[str],
    modules: list[str],
    marks: Marks = (),
) -> list[ParameterSet]:
    """Produces the cartesian product of the configs and modules, optionally with marks."""

    return [pytest.param(config, module, marks=marks) for config in configs for module in modules]


cases: list[ParameterSet | tuple[str, str]] = [
    # No plugin
    *build_cases(
        ['mypy-default.ini', 'pyproject-default.toml'],
        ['pydantic_settings.py'],
    ),
    *build_cases(
        ['mypy-default.ini', 'pyproject-default.toml'],
        ['root_models.py'],
    ),
    *build_cases(
        ['mypy-default.ini'],
        ['plugin_success.py', 'plugin_success_baseConfig.py', 'metaclass_args.py'],
    ),
    # Default plugin config
    *build_cases(
        ['mypy-plugin.ini', 'pyproject-plugin.toml'],
        [
            'plugin_success.py',
            'plugin_fail.py',
            'plugin_success_baseConfig.py',
            'plugin_fail_baseConfig.py',
            'pydantic_settings.py',
            'decorator_implicit_classmethod.py',
        ],
    ),
    # Strict plugin config
    *build_cases(
        ['mypy-plugin-strict.ini', 'pyproject-plugin-strict.toml'],
        [
            'plugin_success.py',
            'plugin_fail.py',
            'fail_defaults.py',
            'plugin_success_baseConfig.py',
            'plugin_fail_baseConfig.py',
        ],
    ),
    # One-off cases
    *[
        ('mypy-plugin.ini', 'custom_constructor.py'),
        ('mypy-plugin.ini', 'config_conditional_extra.py'),
        ('mypy-plugin.ini', 'covariant_typevar.py'),
        ('mypy-plugin.ini', 'frozen_field.py'),
        ('mypy-plugin.ini', 'plugin_optional_inheritance.py'),
        ('mypy-plugin.ini', 'generics.py'),
        ('mypy-plugin.ini', 'root_models.py'),
        ('mypy-plugin.ini', 'plugin_strict_fields.py'),
        ('mypy-plugin.ini', 'final_with_default.py'),
        ('mypy-plugin-strict-no-any.ini', 'dataclass_no_any.py'),
        ('mypy-plugin-very-strict.ini', 'metaclass_args.py'),
        ('pyproject-plugin-no-strict-optional.toml', 'no_strict_optional.py'),
        ('pyproject-plugin-strict-equality.toml', 'strict_equality.py'),
        ('pyproject-plugin.toml', 'from_orm_v1_noconflict.py'),
    ],
]


def get_expected_return_code(source_code: str) -> int:
    """Return 1 if at least one `# MYPY:` comment was found, else 0."""
    if re.findall(r'^\s*# MYPY:', source_code, flags=re.MULTILINE):
        return 1
    return 0


@pytest.mark.parametrize(
    ['config_filename', 'python_filename'],
    cases,
)
def test_mypy_results(config_filename: str, python_filename: str, request: pytest.FixtureRequest) -> None:
    input_path = PYDANTIC_ROOT / 'tests/mypy/modules' / python_filename
    config_path = PYDANTIC_ROOT / 'tests/mypy/configs' / config_filename
    output_path = OUTPUTS_DIR / config_path.name.replace('.', '_') / input_path.name

    # Specifying a different cache dir for each configuration dramatically speeds up subsequent execution
    # It also prevents cache-invalidation-related bugs in the tests
    cache_dir = f'.mypy_cache/test-{os.path.splitext(config_filename)[0]}'
    command = [
        str(input_path),
        '--config-file',
        str(config_path),
        '--cache-dir',
        cache_dir,
        '--show-error-codes',
        '--show-traceback',
    ]
    print(f'\nExecuting: mypy {" ".join(command)}')  # makes it easier to debug as necessary
    mypy_out, mypy_err, mypy_returncode = mypy_api.run(command)

    # Need to strip filenames due to differences in formatting by OS
    mypy_out = '\n'.join(['.py:'.join(line.split('.py:')[1:]) for line in mypy_out.split('\n') if line]).strip()
    mypy_out = re.sub(r'\n\s*\n', r'\n', mypy_out)
    if mypy_out:
        print('{0}\n{1:^100}\n{0}\n{2}\n{0}'.format('=' * 100, f'mypy {mypy_version} output', mypy_out))
    assert mypy_err == ''

    input_code = input_path.read_text()

    existing_output_code: str | None = None
    if output_path.is_file():
        existing_output_code = output_path.read_text()
        print(f'Comparing output with {output_path}')
    else:
        print(f'Comparing output with {input_path} (expecting no mypy errors)')

    merged_output = merge_python_and_mypy_output(input_code, mypy_out)

    if merged_output == (existing_output_code or input_code):
        # Test passed, no changes needed
        pass
    elif request.config.getoption('update_mypy'):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(merged_output)
    else:
        print('**** Merged Output ****')
        print(merged_output)
        print('***********************')
        assert existing_output_code is not None, 'No output file found, run `make test-mypy-update` to create it'
        assert merged_output == existing_output_code
        expected_returncode = get_expected_return_code(existing_output_code)
        assert mypy_returncode == expected_returncode


def test_bad_toml_config() -> None:
    full_config_filename = 'tests/mypy/configs/pyproject-plugin-bad-param.toml'
    full_filename = 'tests/mypy/modules/generics.py'  # File doesn't matter

    command = [full_filename, '--config-file', full_config_filename, '--show-error-codes']
    print(f'\nExecuting: mypy {" ".join(command)}')  # makes it easier to debug as necessary
    with pytest.raises(ValueError) as e:
        mypy_api.run(command)

    assert str(e.value) == 'Configuration value must be a boolean for key: init_forbid_extra'


@pytest.mark.parametrize('module', ['dataclass_no_any', 'plugin_success', 'plugin_success_baseConfig'])
def test_success_cases_run(module: str) -> None:
    """
    Ensure the "success" files can actually be executed
    """
    module_name = f'tests.mypy.modules.{module}'
    try:
        importlib.import_module(module_name)
    except Exception:
        pytest.fail(reason=f'Unable to execute module {module_name}')


@pytest.mark.parametrize(
    ['v_str', 'v_tuple'],
    [
        ('1.11.0', (1, 11, 0)),
        ('1.11.0+dev.d6d9d8cd4f27c52edac1f537e236ec48a01e54cb.dirty', (1, 11, 0)),
    ],
)
def test_parse_mypy_version(v_str: str, v_tuple: tuple[int, int, int]) -> None:
    assert parse_mypy_version(v_str) == v_tuple


def merge_python_and_mypy_output(source_code: str, mypy_output: str) -> str:
    merged_lines = [(line, False) for line in source_code.splitlines()]

    for line in mypy_output.splitlines()[::-1]:
        if not line:
            continue
        try:
            line_number, message = re.split(r':(?:\d+:)?', line, maxsplit=1)
            merged_lines.insert(int(line_number), (f'# MYPY: {message.strip()}', True))
        except ValueError:
            # This could happen due to lack of a ':' in `line`, or the pre-':' contents not being a number
            # Either way, put all such lines at the top of the file
            merged_lines.insert(0, (f'# MYPY: {line.strip()}', True))

    merged_lines = [line for line, is_mypy in merged_lines if is_mypy or not line.strip().startswith('# MYPY: ')]
    return '\n'.join(merged_lines) + '\n'
