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

from pydantic_core import ArgsKwargs, SchemaValidator, ValidationError
from pydantic_core.core_schema import CoreConfig

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


def json_default(obj):
    if isinstance(obj, ArgsKwargs):
        raise pytest.skip('JSON skipping ArgsKwargs')
    else:
        raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')


class PyAndJsonValidator:
    def __init__(
        self, schema, config: CoreConfig | None = None, *, validator_type: Literal['json', 'python'] | None = None
    ):
        self.validator = SchemaValidator(schema, config)
        self.validator_type = validator_type

    def validate_python(self, py_input, strict: bool | None = None, context: Any = None):
        return self.validator.validate_python(py_input, strict=strict, context=context)

    def validate_test(self, py_input, strict: bool | None = None, context: Any = None):
        if self.validator_type == 'json':
            return self.validator.validate_json(
                json.dumps(py_input, default=json_default), strict=strict, context=context
            )
        else:
            assert self.validator_type == 'python', self.validator_type
            return self.validator.validate_python(py_input, strict=strict, context=context)

    def isinstance_test(self, py_input, strict: bool | None = None, context: Any = None):
        if self.validator_type == 'json':
            try:
                self.validator.validate_json(json.dumps(py_input), strict=strict, context=context)
                return True
            except ValidationError:
                return False
        else:
            assert self.validator_type == 'python', self.validator_type
            return self.validator.isinstance_python(py_input, strict=strict, context=context)


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


@pytest.fixture
def pydantic_version():
    try:
        import pydantic

        return pydantic.__version__
    except ImportError:
        return 'latest'


def infinite_generator():
    i = 0
    while True:
        yield i
        i += 1
