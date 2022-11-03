from __future__ import annotations as _annotations

import functools
import importlib.util
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Type

import hypothesis
import pytest
from typing_extensions import Literal

from pydantic_core import SchemaValidator

__all__ = 'Err', 'PyAndJson', 'plain_repr', 'infinite_generator'

hypothesis.settings.register_profile('fast', max_examples=2)
hypothesis.settings.register_profile('slow', max_examples=1_000)
hypothesis.settings.load_profile(os.getenv('HYPOTHESIS_PROFILE', 'fast'))


def plain_repr(obj):
    r = repr(obj)
    r = re.sub(r',\s*([)}])', r'\1', r)
    r = re.sub(r'\s+', '', r)
    return r


@dataclass
class Err:
    message: str
    errors: Any | None = None

    def __repr__(self):
        if self.errors:
            return f'Err({self.message!r}, errors={self.errors!r})'
        else:
            return f'Err({self.message!r})'


class PyAndJsonValidator:
    def __init__(self, schema, validator_type: Literal['json', 'python'] | None = None):
        self.validator = SchemaValidator(schema)
        self.validator_type = validator_type

    def validate_python(self, py_input, strict: bool | None = None, context: Any = None):
        return self.validator.validate_python(py_input, strict, context)

    def validate_test(self, py_input, strict: bool | None = None, context: Any = None):
        if self.validator_type == 'json':
            return self.validator.validate_json(json.dumps(py_input), strict, context)
        else:
            assert self.validator_type == 'python', self.validator_type
            return self.validator.validate_python(py_input, strict, context)

    def isinstance_test(self, py_input, strict: bool | None = None, context: Any = None):
        if self.validator_type == 'json':
            return self.validator.isinstance_json(json.dumps(py_input), strict, context)
        else:
            assert self.validator_type == 'python', self.validator_type
            return self.validator.isinstance_python(py_input, strict, context)


PyAndJson = Type[PyAndJsonValidator]


@pytest.fixture(params=['python', 'json'])
def py_and_json(request) -> PyAndJson:
    class ChosenPyAndJsonValidator(PyAndJsonValidator):
        __init__ = functools.partialmethod(PyAndJsonValidator.__init__, validator_type=request.param)

    return ChosenPyAndJsonValidator


@pytest.fixture
def tmp_work_path(tmp_path: Path):
    """
    Create a temporary working directory.
    """
    previous_cwd = Path.cwd()
    os.chdir(tmp_path)

    yield tmp_path

    os.chdir(previous_cwd)


@pytest.fixture
def import_execute(request, tmp_work_path: Path):
    def _import_execute(source: str, *, custom_module_name: 'str | None' = None):
        module_name = custom_module_name or request.node.name

        module_path = tmp_work_path / f'{module_name}.py'
        module_path.write_text(source)
        spec = importlib.util.spec_from_file_location('__main__', str(module_path))
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
        else:
            return module

    return _import_execute


def infinite_generator():
    i = 0
    while True:
        yield i
        i += 1
