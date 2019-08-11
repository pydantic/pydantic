import importlib
import os
import re
from pathlib import Path

import pytest
from mypy import api

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


@pytest.mark.parametrize('filename,expected_result', expected_successes + expected_fails)
def test_mypy_results(filename, expected_result):
    actual_result = api.run([filename, '--config-file', 'tests/mypy/mypy-default.ini'])
    assert actual_result == expected_result


success_imports = [re.sub('/', '.', filename)[:-3] for filename, _ in expected_successes]


@pytest.mark.parametrize('module', success_imports)
def test_mypy_successes_run(module):
    importlib.import_module(module)
