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
os.chdir(Path(__file__).parent.parent)

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

expected_successes = [('tests/mypy/success.py', ('', '', 0))]


@pytest.mark.skipif(not typing_extensions, reason='typing_extensions not installed')
@pytest.mark.parametrize('filename,expected_result', expected_successes + expected_fails)
def test_mypy_results(filename, expected_result):
    actual_result = api.run([filename, '--config-file', 'tests/mypy/mypy-default.ini', '--no-error-summary'])

    expected_out, expected_err, expected_returncode = expected_result
    actual_out, actual_err, actual_returncode = actual_result
    assert (expected_err, expected_returncode) == (actual_err, actual_returncode)

    # Need to remove filenames, as they render differently on mac/linux and windows:
    actual_out_lines = actual_out.split('\n')
    expected_out_lines = expected_out.split('\n')
    assert len(actual_out_lines) == len(expected_out_lines)
    for actual_line, expected_line in zip(actual_out_lines, expected_out_lines):
        actual_line_without_filename = '.py'.join(actual_line.split('.py')[1:])
        expected_line_without_filename = '.py'.join(expected_line.split('.py')[1:])
        assert actual_line_without_filename == expected_line_without_filename


success_imports = [re.sub('/', '.', filename)[:-3] for filename, _ in expected_successes]


@pytest.mark.parametrize('module', success_imports)
def test_mypy_successes_run(module):
    importlib.import_module(module)
