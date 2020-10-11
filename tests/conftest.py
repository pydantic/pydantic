import inspect
import os
import secrets
import subprocess
import sys
import textwrap
from importlib.machinery import SourceFileLoader
from types import FunctionType

import pytest


def _extract_source_code_from_function(function):
    if function.__code__.co_argcount:
        raise RuntimeError(f'function {function.__qualname__} cannot have any arguments')

    code_lines = ''
    body_started = False
    for line in textwrap.dedent(inspect.getsource(function)).split('\n'):
        if line.startswith('def '):
            body_started = True
            continue
        elif body_started:
            code_lines += f'{line}\n'

    return textwrap.dedent(code_lines)


def _create_module(code, tmp_path, name):
    name = f'{name}_{secrets.token_hex(5)}'
    path = tmp_path / f'{name}.py'
    path.write_text(code)
    return name, path


class SetEnv:
    def __init__(self):
        self.envars = set()

    def set(self, name, value):
        self.envars.add(name)
        os.environ[name] = value

    def clear(self):
        for n in self.envars:
            os.environ.pop(n)


@pytest.yield_fixture
def env():
    setenv = SetEnv()

    yield setenv

    setenv.clear()


@pytest.fixture
def create_module(tmp_path, request):
    def run(module_source_code=None):
        """
        Creates module and loads it with SourceFileLoader().load_module()
        """
        if isinstance(module_source_code, FunctionType):
            module_source_code = _extract_source_code_from_function(module_source_code)
        name, path = _create_module(module_source_code, tmp_path, request.node.name)
        return SourceFileLoader(name, str(path)).load_module()

    return run


@pytest.fixture
def run_as_module(tmp_path, request):
    def run(module_source_code=None):
        """
        Creates module source and runs it in subprocess

        This way is much slower than SourceFileLoader().load_module(),
        but executes module as __main__ with a clear stack (https://docs.python.org/3/library/__main__.html)
        """
        if isinstance(module_source_code, FunctionType):
            module_source_code = _extract_source_code_from_function(module_source_code)
        _, path = _create_module(module_source_code, tmp_path, request.node.name)
        result = subprocess.run([sys.executable, str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        if result.returncode != 0:
            pytest.fail(
                f'Running {path} failed with non-zero return code: {result.returncode}\n'
                f'Captured stdout:\n{result.stdout.decode()}\n'
                f'Captured stderr:\n{result.stderr.decode()}'
            )

    return run
