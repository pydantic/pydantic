import importlib
import os
import re
from pathlib import Path

import pytest

try:
    from mypy import api as mypy_api
    from mypy.version import __version__ as mypy_version
except ImportError:
    mypy_api = None  # type: ignore
    mypy_version = '0'

try:
    import dotenv
except ImportError:
    dotenv = None  # type: ignore

# This ensures mypy can find the test files, no matter where tests are run from:
os.chdir(Path(__file__).parent.parent.parent)

cases = [
    ('mypy-plugin.ini', 'plugin_success.py', None),
    ('mypy-plugin.ini', 'plugin_fail.py', 'plugin-fail.txt'),
    ('mypy-plugin-strict.ini', 'plugin_success.py', 'plugin-success-strict.txt'),
    ('mypy-plugin-strict.ini', 'plugin_fail.py', 'plugin-fail-strict.txt'),
    ('mypy-default.ini', 'success.py', None),
    ('mypy-default.ini', 'fail1.py', 'fail1.txt'),
    ('mypy-default.ini', 'fail2.py', 'fail2.txt'),
    ('mypy-default.ini', 'fail3.py', 'fail3.txt'),
    ('mypy-default.ini', 'fail4.py', 'fail4.txt'),
    ('mypy-default.ini', 'plugin_success.py', 'plugin_success.txt'),
    ('pyproject-default.toml', 'success.py', None),
    ('pyproject-default.toml', 'fail1.py', 'fail1.txt'),
    ('pyproject-default.toml', 'fail2.py', 'fail2.txt'),
    ('pyproject-default.toml', 'fail3.py', 'fail3.txt'),
    ('pyproject-default.toml', 'fail4.py', 'fail4.txt'),
    ('pyproject-plugin.toml', 'plugin_success.py', None),
    ('pyproject-plugin.toml', 'plugin_fail.py', 'plugin-fail.txt'),
    ('pyproject-plugin-strict.toml', 'plugin_success.py', 'plugin-success-strict.txt'),
    ('pyproject-plugin-strict.toml', 'plugin_fail.py', 'plugin-fail-strict.txt'),
]
executable_modules = list({fname[:-3] for _, fname, out_fname in cases if out_fname is None})


@pytest.mark.skipif(not (dotenv and mypy_api), reason='dotenv or mypy are not installed')
@pytest.mark.parametrize('config_filename,python_filename,output_filename', cases)
def test_mypy_results(config_filename: str, python_filename: str, output_filename: str) -> None:
    full_config_filename = f'tests/mypy/configs/{config_filename}'
    full_filename = f'tests/mypy/modules/{python_filename}'
    output_path = None if output_filename is None else Path(f'tests/mypy/outputs/{output_filename}')

    # Specifying a different cache dir for each configuration dramatically speeds up subsequent execution
    # It also prevents cache-invalidation-related bugs in the tests
    cache_dir = f'.mypy_cache/test-{os.path.splitext(config_filename)[0]}'
    command = [full_filename, '--config-file', full_config_filename, '--cache-dir', cache_dir, '--show-error-codes']
    print(f"\nExecuting: mypy {' '.join(command)}")  # makes it easier to debug as necessary
    actual_result = mypy_api.run(command)
    actual_out, actual_err, actual_returncode = actual_result
    # Need to strip filenames due to differences in formatting by OS
    actual_out = '\n'.join(['.py:'.join(line.split('.py:')[1:]) for line in actual_out.split('\n') if line]).strip()
    actual_out = re.sub(r'\n\s*\n', r'\n', actual_out)

    if actual_out:
        print('{0}\n{1:^100}\n{0}\n{2}\n{0}'.format('=' * 100, 'mypy output', actual_out))

    assert actual_err == ''
    expected_returncode = 0 if output_filename is None else 1
    assert actual_returncode == expected_returncode

    if output_path and not output_path.exists():
        output_path.write_text(actual_out)
        raise RuntimeError(f'wrote actual output to {output_path} since file did not exist')

    expected_out = Path(output_path).read_text() if output_path else ''

    # fix for compatibility between mypy versions: (this can be dropped once we drop support for mypy<0.930)
    if actual_out and float(mypy_version) < 0.930:
        actual_out = actual_out.lower()
        expected_out = expected_out.lower()
        actual_out = actual_out.replace('variant:', 'variants:')
        actual_out = re.sub(r'^(\d+: note: {4}).*', r'\1...', actual_out, flags=re.M)
        expected_out = re.sub(r'^(\d+: note: {4}).*', r'\1...', expected_out, flags=re.M)

    assert actual_out == expected_out, actual_out


@pytest.mark.skipif(not (dotenv and mypy_api), reason='dotenv or mypy are not installed')
def test_bad_toml_config() -> None:
    full_config_filename = 'tests/mypy/configs/pyproject-plugin-bad-param.toml'
    full_filename = 'tests/mypy/modules/success.py'

    # Specifying a different cache dir for each configuration dramatically speeds up subsequent execution
    # It also prevents cache-invalidation-related bugs in the tests
    cache_dir = '.mypy_cache/test-pyproject-plugin-bad-param'
    command = [full_filename, '--config-file', full_config_filename, '--cache-dir', cache_dir, '--show-error-codes']
    print(f"\nExecuting: mypy {' '.join(command)}")  # makes it easier to debug as necessary
    with pytest.raises(ValueError) as e:
        mypy_api.run(command)

    assert str(e.value) == 'Configuration value must be a boolean for key: init_forbid_extra'


@pytest.mark.parametrize('module', executable_modules)
def test_success_cases_run(module: str) -> None:
    """
    Ensure the "success" files can actually be executed
    """
    importlib.import_module(f'tests.mypy.modules.{module}')


def test_explicit_reexports() -> None:
    from pydantic import __all__ as root_all
    from pydantic.main import __all__ as main
    from pydantic.networks import __all__ as networks
    from pydantic.tools import __all__ as tools
    from pydantic.types import __all__ as types

    for name, export_all in [('main', main), ('network', networks), ('tools', tools), ('types', types)]:
        for export in export_all:
            assert export in root_all, f'{export} is in {name}.__all__ but missing from re-export in __init__.py'
