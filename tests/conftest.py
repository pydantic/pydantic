import importlib
import inspect
import os
import secrets
import sys
import textwrap
from types import FunctionType

import pytest
from _pytest.assertion.rewrite import AssertionRewritingHook

# See https://hypothesis.readthedocs.io/en/latest/strategies.html#interaction-with-pytest-cov
try:
    from hypothesis import given  # noqa
except ImportError:
    pytest_plugins = []
else:
    pytest_plugins = ['hypothesis.extra.pytestplugin']


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


def _create_module_file(code, tmp_path, name):
    name = f'{name}_{secrets.token_hex(5)}'
    path = tmp_path / f'{name}.py'
    path.write_text(code)
    return name, str(path)


class SetEnv:
    def __init__(self):
        self.envars = set()

    def set(self, name, value):
        self.envars.add(name)
        os.environ[name] = value

    def clear(self):
        for n in self.envars:
            os.environ.pop(n)


@pytest.fixture
def env():
    setenv = SetEnv()

    yield setenv

    setenv.clear()


@pytest.fixture
def create_module(tmp_path, request):
    def run(source_code_or_function, rewrite_assertions=True):
        """
        Create module object, execute it and return
        Can be used as a decorator of the function from the source code of which the module will be constructed

        :param source_code_or_function string or function with body as a source code for created module
        :param rewrite_assertions: whether to rewrite assertions in module or not

        """
        if isinstance(source_code_or_function, FunctionType):
            source_code = _extract_source_code_from_function(source_code_or_function)
        else:
            source_code = source_code_or_function

        module_name, filename = _create_module_file(source_code, tmp_path, request.node.name)

        if rewrite_assertions:
            loader = AssertionRewritingHook(config=request.config)
            loader.mark_rewrite(module_name)
        else:
            loader = None

        spec = importlib.util.spec_from_file_location(module_name, filename, loader=loader)
        sys.modules[module_name] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return run
