import importlib
import os
import re
from pathlib import Path

import pytest
from mypy import api

try:
    import typing_extensions
except ImportError:
    typing_extensions = None

# This ensures mypy can find the test files, no matter where tests are run from:
os.chdir(Path(__file__).parent.parent.parent)

expected_fails = [
    (
        'tests/mypy/fail1.py',
        ('tests/mypy/fail1.py:20: error: Unsupported operand types for + ("int" and "str")\n', '', 1),
    ),
    ('tests/mypy/fail2.py', ('tests/mypy/fail2.py:20: error: "Model" has no attribute "foobar"\n', '', 1)),
    (
        'tests/mypy/fail3.py',
        (
            'tests/mypy/fail3.py:22: error: '
            'Argument 1 to "append" of "list" has incompatible type "str"; expected "int"\n',
            '',
            1,
        ),
    ),
]

expected_successes = [('tests/mypy/success.py', ('', '', 0)), ('tests/mypy/plugin-success.py', ('', '', 0))]


@pytest.mark.skipif(not typing_extensions, reason='typing_extensions not installed')
@pytest.mark.parametrize('filename,expected_result', expected_successes + expected_fails)
def test_mypy_results(filename, expected_result):
    actual_result = api.run([filename, '--config-file', 'tests/mypy/mypy-default.ini', '--no-error-summary'])
    validate_mypy_results(actual_result, expected_result)


plugin_fail_output = (
    'tests/mypy/plugin-fail.py:22: error: Unexpected keyword argument "z" for "Model"\n'
    'tests/mypy/plugin-fail.py:23: error: Missing named argument "y" for "Model"\n'
    'tests/mypy/plugin-fail.py:24: error: Property "y" defined in "Model" is read-only\n'
    'tests/mypy/plugin-fail.py:25: error: "Model" does not have orm_mode=True in its Config [pydantic]\n'
    'tests/mypy/plugin-fail.py:33: error: Unexpected keyword argument "x" for "ForbidExtraModel"\n'
    'tests/mypy/plugin-fail.py:44: error: Unexpected keyword argument "x" for "ForbidExtraModel2"\n'
    'tests/mypy/plugin-fail.py:49: error: Invalid value specified for "Config.extra" [pydantic]\n'
    'tests/mypy/plugin-fail.py:54: error: Invalid value specified for "Config.orm_mode" [pydantic]\n'
    'tests/mypy/plugin-fail.py:59: error: Invalid value specified for "Config.orm_mode" [pydantic]\n'
    'tests/mypy/plugin-fail.py:70: error: '
    'Incompatible types in assignment (expression has type "ellipsis", variable has type "int")\n'
    'tests/mypy/plugin-fail.py:83: error: Missing named argument "a" for "DefaultTestingModel"\n'
    'tests/mypy/plugin-fail.py:83: error: Missing named argument "b" for "DefaultTestingModel"\n'
    'tests/mypy/plugin-fail.py:83: error: Missing named argument "c" for "DefaultTestingModel"\n'
    'tests/mypy/plugin-fail.py:83: error: Missing named argument "d" for "DefaultTestingModel"\n'
    'tests/mypy/plugin-fail.py:83: error: Missing named argument "e" for "DefaultTestingModel"\n'
    "tests/mypy/plugin-fail.py:87: error: Name 'Undefined' is not defined\n"
    'tests/mypy/plugin-fail.py:90: error: Missing named argument "undefined" for "UndefinedAnnotationModel"\n'
    'tests/mypy/plugin-fail.py:97: error: Missing named argument "y" for "construct" of "Model"\n'
    'tests/mypy/plugin-fail.py:99: error: '
    'Argument "x" to "construct" of "Model" has incompatible type "str"; expected "int"\n'
)
plugin_results = [
    ('tests/mypy/plugin-success.py', ('', '', 0)),
    ('tests/mypy/plugin-fail.py', (plugin_fail_output, '', 1)),
]


@pytest.mark.skipif(not typing_extensions, reason='typing_extensions not installed')
@pytest.mark.parametrize('filename,expected_result', plugin_results)
def test_mypy_plugin(filename, expected_result):
    actual_result = api.run([filename, '--config-file', 'tests/mypy/mypy-plugin.ini', '--no-error-summary'])
    validate_mypy_results(actual_result, expected_result)


strict_plugin_fail_output = (
    'tests/mypy/plugin-fail.py:104: error: '
    'Argument "x" to "InheritingModel" has incompatible type "str"; expected "int"\n'
    'tests/mypy/plugin-fail.py:105: error: Argument "x" to "Settings" has incompatible type "str"; expected "int"\n'
    'tests/mypy/plugin-fail.py:106: error: Argument "x" to "Model" has incompatible type "str"; expected "int"\n'
    'tests/mypy/plugin-fail.py:123: error: '
    'Argument "data" to "Response" has incompatible type "int"; expected "Model"\n'
)
strict_plugin_results = [
    (
        'tests/mypy/plugin-success.py',
        (
            'tests/mypy/plugin-success.py:29: error: Unexpected keyword argument "z" for "Model"\n'
            'tests/mypy/plugin-success.py:79: '
            'error: Argument "x" to "OverrideModel" has incompatible type "float"; expected "int"\n',
            '',
            1,
        ),
    ),
    ('tests/mypy/plugin-fail.py', (plugin_fail_output + strict_plugin_fail_output, '', 1)),
]


@pytest.mark.skipif(not typing_extensions, reason='typing_extensions not installed')
@pytest.mark.parametrize('filename,expected_result', strict_plugin_results)
def test_mypy_plugin_strict(filename, expected_result):
    actual_result = api.run([filename, '--config-file', 'tests/mypy/mypy-plugin-strict.ini', '--no-error-summary'])
    validate_mypy_results(actual_result, expected_result)


success_imports = [re.sub('/', '.', filename)[:-3] for filename, _ in expected_successes]


@pytest.mark.parametrize('module', success_imports)
def test_mypy_successes_run(module):
    importlib.import_module(module)


def validate_mypy_results(actual_result, expected_result):
    expected_out, expected_err, expected_returncode = expected_result
    actual_out, actual_err, actual_returncode = actual_result
    actual_out_lines = actual_out.split('\n')
    expected_out_lines = expected_out.split('\n')

    assert (expected_err, expected_returncode) == (actual_err, actual_returncode)
    assert len(actual_out_lines) == len(expected_out_lines)
    # Need to remove filenames, as they render differently on mac/linux and windows:
    for actual_line, expected_line in zip(actual_out_lines, expected_out_lines):
        actual_line_without_filename = '.py'.join(actual_line.split('.py')[1:])
        expected_line_without_filename = '.py'.join(expected_line.split('.py')[1:])
        assert actual_line_without_filename == expected_line_without_filename
