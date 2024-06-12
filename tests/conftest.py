import importlib
import inspect
import os
import re
import secrets
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from types import FunctionType
from typing import Any, Optional

import pytest
from _pytest.assertion.rewrite import AssertionRewritingHook

from pydantic import GenerateSchema


def pytest_addoption(parser: pytest.Parser):
    parser.addoption('--test-mypy', action='store_true', help='run mypy tests')
    parser.addoption('--update-mypy', action='store_true', help='update mypy tests')


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


@pytest.fixture(scope='session', autouse=True)
def disable_error_urls():
    # Don't add URLs during docs tests when printing
    # Otherwise we'll get version numbers in the URLs that will update frequently
    os.environ['PYDANTIC_ERRORS_INCLUDE_URL'] = 'false'


@pytest.fixture
def create_module(tmp_path, request):
    def run(source_code_or_function, rewrite_assertions=True, module_name_prefix=None):
        """
        Create module object, execute it and return
        Can be used as a decorator of the function from the source code of which the module will be constructed

        :param source_code_or_function string or function with body as a source code for created module
        :param rewrite_assertions: whether to rewrite assertions in module or not
        :param module_name_prefix: string prefix to use in the name of the module, does not affect the name of the file.

        """
        if isinstance(source_code_or_function, FunctionType):
            source_code = _extract_source_code_from_function(source_code_or_function)
        else:
            source_code = source_code_or_function

        module_name, filename = _create_module_file(source_code, tmp_path, request.node.name)
        if module_name_prefix:
            module_name = module_name_prefix + module_name

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


@pytest.fixture
def subprocess_run_code(tmp_path: Path):
    def run_code(source_code_or_function) -> str:
        if isinstance(source_code_or_function, FunctionType):
            source_code = _extract_source_code_from_function(source_code_or_function)
        else:
            source_code = source_code_or_function

        py_file = tmp_path / 'test.py'
        py_file.write_text(source_code)

        return subprocess.check_output([sys.executable, str(py_file)], cwd=tmp_path, encoding='utf8')

    return run_code


@dataclass
class Err:
    message: str
    errors: Optional[Any] = None

    def __repr__(self):
        if self.errors:
            return f'Err({self.message!r}, errors={self.errors!r})'
        else:
            return f'Err({self.message!r})'

    def message_escaped(self):
        return re.escape(self.message)


@dataclass
class CallCounter:
    count: int = 0

    def reset(self) -> None:
        self.count = 0


@pytest.fixture
def generate_schema_calls(monkeypatch) -> CallCounter:
    orig_generate_schema = GenerateSchema.generate_schema
    counter = CallCounter()
    depth = 0  # generate_schema can be called recursively

    def generate_schema_call_counter(*args: Any, **kwargs: Any) -> Any:
        nonlocal depth
        counter.count += 1 if depth == 0 else 0
        depth += 1
        try:
            return orig_generate_schema(*args, **kwargs)
        finally:
            depth -= 1

    monkeypatch.setattr(GenerateSchema, 'generate_schema', generate_schema_call_counter)
    return counter
