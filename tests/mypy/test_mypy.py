import importlib
import os
from pathlib import Path

import pytest

try:
    from mypy import api as mypy_api
except ImportError:
    mypy_api = None

try:
    import typing_extensions
except ImportError:
    typing_extensions = None

# This ensures mypy can find the test files, no matter where tests are run from:
os.chdir(Path(__file__).parent.parent.parent)

# You can change the following variable to True during development to overwrite expected output with generated output
GENERATE = False

cases = [
    ('mypy-plugin.ini', 'plugin_success.py', None),
    ('mypy-plugin.ini', 'plugin_fail.py', 'plugin-fail.txt'),
    ('mypy-plugin-strict.ini', 'plugin_success.py', 'plugin-success-strict.txt'),
    ('mypy-plugin-strict.ini', 'plugin_fail.py', 'plugin-fail-strict.txt'),
    ('mypy-default.ini', 'success.py', None),
    ('mypy-default.ini', 'fail1.py', 'fail1.txt'),
    ('mypy-default.ini', 'fail2.py', 'fail2.txt'),
    ('mypy-default.ini', 'fail3.py', 'fail3.txt'),
    ('mypy-default.ini', 'plugin_success.py', None),
]
executable_modules = list({fname[:-3] for _, fname, out_fname in cases if out_fname is None})


@pytest.mark.skipif(not (typing_extensions and mypy_api), reason='typing_extensions or mypy are not installed')
@pytest.mark.parametrize('config_filename,python_filename,output_filename', cases)
def test_mypy_results(config_filename, python_filename, output_filename):
    full_config_filename = f'tests/mypy/configs/{config_filename}'
    full_filename = f'tests/mypy/modules/{python_filename}'
    full_output_filename = None if output_filename is None else f'tests/mypy/outputs/{output_filename}'

    expected_out = ''
    expected_err = ''
    expected_returncode = 0 if output_filename is None else 1
    if full_output_filename is not None:
        with open(full_output_filename, 'r') as f:
            expected_out = f.read()

    # Specifying a different cache dir for each configuration dramatically speeds up subsequent execution
    # It also prevents cache-invalidation-related bugs in the tests
    cache_dir = f'.mypy_cache/test-{config_filename[:-4]}'
    actual_result = mypy_api.run(
        [full_filename, '--config-file', full_config_filename, '--cache-dir', cache_dir, '--show-error-codes']
    )
    actual_out, actual_err, actual_returncode = actual_result
    # Need to strip filenames due to differences in formatting by OS
    actual_out = '\n'.join(['.py:'.join(line.split('.py:')[1:]) for line in actual_out.split('\n')]).strip()

    if GENERATE and output_filename is not None:
        with open(full_output_filename, 'w') as f:
            f.write(actual_out)
    else:
        assert actual_out == expected_out, actual_out

    assert actual_err == expected_err
    assert actual_returncode == expected_returncode


@pytest.mark.parametrize('module', executable_modules)
def test_success_cases_run(module):
    """
    Ensure the "success" files can actually be executed
    """
    importlib.import_module(f'tests.mypy.modules.{module}')


def test_generation_is_disabled():
    """
    Makes sure we don't accidentally leave generation on
    """
    assert not GENERATE
