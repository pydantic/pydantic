import ast
import importlib
import inspect
import os
import pickle
import re
import sys
from functools import wraps
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Dict
from unittest import TestCase

import pytest
from _pytest import assertion

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
    ('mypy-default. ini', 'fail4.py', 'fail4.txt'),
    ('mypy-default.ini', 'plugin_success.py', 'plugin_success.txt'),
]
executable_modules = list({fname[:-3] for _, fname, out_fname in cases if out_fname is None})

RUN_MYPY_MODULE = Path(__file__).parent / 'run_mypy.py'


def get_run_mypy_cmd(args):
    return [sys.executable, RUN_MYPY_MODULE, *args]


def run_parallel(test_case):
    parametrized = False
    argnames = argvalues = ()

    def skip(fn):
        return fn

    for mark in getattr(test_case, 'pytestmark', []):
        if mark.name == 'parametrize':
            parametrized = True
            argnames, argvalues, *other = mark.args
            if other or mark.kwargs:
                raise ValueError('Only positional argnames and argvalues implemented')
            if isinstance(argnames, str):
                argnames = argnames.split(',')
        elif mark.name == 'skipif':
            def skip(fn):
                return pytest.mark.skipif(*mark.args, **mark.kwargs)(fn)
        else:
            raise ValueError(f'@pytest.mark.{mark.name} is unsupported')

    if not parametrized:
        raise RuntimeError("Won't run one and only test case parallel, sorry...")

    decoys = {}
    tests_to_run = {}
    test_name = test_case.__name__

    # Pytest rewrite reference
    # https://stackoverflow.com/questions/51839452/can-i-patch-pythons-assert-to-get-the-output-that-py-test-provides
    source = ''
    decorators_skipped = False
    lines, defined_on_line = inspect.getsourcelines(test_case)
    lines_before_definition = defined_on_line - 1
    for line in lines:
        if line.startswith('def '):
            decorators_skipped = True
            source += line
        elif decorators_skipped:
            source += line
        else:
            lines_before_definition += 1

    if not decorators_skipped:
        raise RuntimeError(f'Unable to find function definition')

    source = '\n' * lines_before_definition + source  # prepend lines before function to get accurate traceback

    tree = ast.parse(source)
    assertion.rewrite.rewrite_asserts(tree, source)
    new_code_obj = compile(tree, test_case.__code__.co_filename, 'exec')
    exec(new_code_obj, test_case.__globals__)
    test_case = test_case.__globals__[test_case.__name__]

    for i, values in enumerate(argvalues):
        if len(values) != len(argnames):
            raise ValueError(
                f"Wrong number of values, expected {len(argnames)}, "
                f"got {len(values)}: {i}, {values}"
            )

        parameters = dict(zip(argnames, values))
        parameters_str = f'[{"-".join(map(str, values))}]'
        parametrized_name = 'test_parallel' + parameters_str

        @wraps(test_case)
        @pytest.mark.skipif(skip, reason=reason)
        def decoy_method(key=parametrized_name):
            if key in exceptions:
                raise exceptions[key]

        def parametrized_method(*args, __parametrize_params__=parameters, **kwargs):
            return test_case(*args, **kwargs, **__parametrize_params__)

        decoy_method.__name__ = parametrized_name
        decoy_method.__qualname__ = parametrized_name

        # set global reference as multiprocessing needs to be able to pickle this
        global_lookup_name = f'_{test_name}{parameters_str.replace(".", "_")}'
        parametrized_method.__qualname__ = global_lookup_name
        setattr(sys.modules[parametrized_method.__module__], global_lookup_name, parametrized_method)

        decoys[parametrized_name] = decoy_method
        tests_to_run[parametrized_name] = parametrized_method
        pickle.dumps(parametrized_method)

    exceptions: Dict[str, Exception] = {}

    class Test(TestCase):
        locals().update(decoys)

        @classmethod
        def setUpClass(cls) -> None:
            cls.run_methods()

        @classmethod
        def run_methods(cls):
            pool = ThreadPool(cpu_count())
            for task in [
                pool.apply_async(test, error_callback=lambda e: exceptions.__setitem__('name', e))
                for name, test in tests_to_run.items()
            ]:
                task.get()
            pool.close()
            pool.join()

    Test.__name__ = Test.__qualname__ = test_case.__name__
    return Test


@run_parallel
@pytest.mark.skipif(not (typing_extensions and mypy_api), reason='typing_extensions or mypy are not installed')
@pytest.mark.parametrize('config_filename,python_filename,output_filename', cases)
def test_mypy_results(config_filename, python_filename, output_filename):
    full_config_filename = f'tests/mypy/configs/{config_filename}'
    full_filename = f'tests/mypy/modules/{python_filename}'
    output_path = None if output_filename is None else Path(f'tests/mypy/outputs/{output_filename}')

    # Specifying a different cache dir for each configuration dramatically speeds up subsequent execution
    # It also prevents cache-invalidation-related bugs in the tests
    cache_dir = f'.mypy_cache/test-{config_filename[:-4]}'
    args = [full_filename, '--config-file', full_config_filename, '--cache-dir', cache_dir, '--show-error-codes']
    print(f"\nExecuting: mypy {' '.join(args)}")  # makes it easier to debug as necessary

    # result = subprocess.run(get_run_mypy_cmd(args), stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    actual_result = mypy_api.run(args)

    actual_out, actual_err, actual_returncode = actual_result
    # sub_err = result.stderr is not None and result.stderr.decode().strip()
    # sub_out = result.stdout is not None and result.stdout.decode().strip()
    # assert sub_err == actual_err
    # assert sub_out == actual_out
    # assert result.returncode == actual_returncode

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
    assert actual_out == expected_out, actual_out


@pytest.mark.parametrize('module', executable_modules)
def test_success_cases_run(module):
    """
    Ensure the "success" files can actually be executed
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
