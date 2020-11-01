import asyncio
import importlib
import os
import re
import sys
from pathlib import Path

import pytest

from tests.mypy.async_test_runner import run_async

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
]
executable_modules = list({fname[:-3] for _, fname, out_fname in cases if out_fname is None})

TEST_DIR = Path(__file__).parent
CONFIGS_DIR = TEST_DIR / 'configs'
MODULES_DIR = TEST_DIR / 'modules'
OUTPUT_DIR = TEST_DIR / 'outputs'


def get_run_mypy_cmd(module_path: Path, config_path: Path):
    # Specifying a different cache dir for each configuration dramatically speeds up subsequent execution
    # It also prevents cache-invalidation-related bugs in the tests
    cache_dir = f'.mypy_cache/test-{str(config_path)[:-4]}'
    mypy = f'{sys.executable} -m mypy'
    return f'{mypy} {module_path} --config-file {config_path} --cache-dir {cache_dir} --show-error-codes'


@run_async
@pytest.mark.skipif(not (typing_extensions and mypy_api), reason='typing_extensions or mypy are not installed')
@pytest.mark.parametrize('config_filename,module_filename,output_filename', cases)
async def test_mypy_results(config_filename, module_filename, output_filename):
    cmd = get_run_mypy_cmd(MODULES_DIR / module_filename, CONFIGS_DIR / config_filename)
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    assert stderr.strip() == b''
    assert stdout is not None

    # Need to strip filenames due to differences in formatting by OS
    actual_out = '\n'.join(
        ['.py:'.join(line.split('.py:')[1:]) for line in stdout.decode().split('\n') if line]
    ).strip()
    actual_out = re.sub(r'\n\s*\n', r'\n', actual_out)

    if actual_out:
        params = map(str, (config_filename, module_filename, output_filename))
        print(
            '{0}\n'
            '{1:^100}\n'
            '{0}\n'
            '{2}\n'
            '{0}\n'.format('=' * 100, f'{test_mypy_results.__name__}({", ".join(params)})', actual_out)
        )

    if output_filename is not None:
        output_path = OUTPUT_DIR / output_filename
        if not output_path.exists():
            output_path.write_text(actual_out)
            raise RuntimeError(f'wrote actual output to {output_path} since file did not exist')
        expected_out = output_path.read_text()
        expected_returncode = 1
    else:
        expected_out = ''
        expected_returncode = 0

    assert proc.returncode == expected_returncode
    assert actual_out == expected_out


@pytest.mark.parametrize('module', executable_modules)
def test_success_cases_run(module):
    """
    Ensure the 'success' files can actually be executed
    """
    importlib.import_module(f'tests.mypy.modules.{module}')


def test_explicit_reexports():
    from pydantic import __all__ as root_all
    from pydantic.main import __all__ as main
    from pydantic.networks import __all__ as networks
    from pydantic.tools import __all__ as tools
    from pydantic.types import __all__ as types

    for name, export_all in [('main', main), ('network', networks), ('tools', tools), ('types', types)]:
        for export in export_all:
            assert export in root_all, f'{export} is in {name}.__all__ but missing from re-export in __init__.py'
