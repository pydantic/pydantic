from __future__ import annotations as _annotations

import functools
import gc
import importlib.util
import json
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from time import sleep, time
from typing import Any, Literal

import hypothesis
import pytest

from pydantic_core import ArgsKwargs, CoreSchema, SchemaSerializer, SchemaValidator, ValidationError
from pydantic_core.core_schema import CoreConfig, ExtraBehavior

__all__ = 'Err', 'PyAndJson', 'assert_gc', 'is_free_threaded', 'plain_repr', 'infinite_generator'

hypothesis.settings.register_profile('fast', max_examples=2)
hypothesis.settings.register_profile('slow', max_examples=1_000)
hypothesis.settings.load_profile(os.getenv('HYPOTHESIS_PROFILE', 'fast'))

try:
    is_free_threaded = not sys._is_gil_enabled()
except AttributeError:
    is_free_threaded = False


# --- GC traversal completeness check -----------------------------------------------------------------------
# Every `SchemaValidator`/`SchemaSerializer` construction during tests verifies that the Python objects
# retained from the core schema are reported to the garbage collector by `__traverse__`. A missing field in
# an `impl_py_gc_traverse!()` call in the Rust sources results in reference cycles through the validator or
# serializer never being collected (see https://github.com/pydantic/pydantic/issues/13625).

_gc_traverse_check_active = False


def _collect_gc_check_candidates(obj: Any, candidates: dict[int, Any], seen: set[int]) -> None:
    """Collect Python objects from a core schema that pydantic-core is likely to retain.

    Restricted to classes, callables and enum members: plain values may be converted (and not
    referenced) on the Rust side, in which case they don't need to be traversed.
    """
    if isinstance(obj, dict):
        if id(obj) in seen:
            return
        seen.add(id(obj))
        for key, value in obj.items():
            # Core schema `metadata` is opaque to pydantic-core and never retained on its own:
            if key != 'metadata':
                _collect_gc_check_candidates(value, candidates, seen)
    elif isinstance(obj, (list, tuple)):
        if id(obj) in seen:
            return
        seen.add(id(obj))
        for value in obj:
            _collect_gc_check_candidates(value, candidates, seen)
    elif callable(obj) or hasattr(obj, '__objclass__'):
        candidates.setdefault(id(obj), obj)


def _gc_traverse_reachable(obj: Any, exclude_id: int) -> dict[int, Any]:
    """Objects reported to the garbage collector by ``obj``'s ``tp_traverse``.

    ``gc.get_referents()`` returns exactly what ``tp_traverse`` reports. Plain Python containers are
    recursed into, as the GC tracks their contents through the containers' own ``tp_traverse``. The
    retained core schema (``exclude_id``) is deliberately ignored: reachability through ``py_schema``
    isn't enough for cycles to be collectable -- CPython requires every strong reference held by the
    Rust structures to be reported individually.
    """
    reachable: dict[int, Any] = {}
    stack = [obj]
    while stack:
        current = stack.pop()
        for referent in gc.get_referents(current):
            if id(referent) != exclude_id and id(referent) not in reachable:
                reachable[id(referent)] = referent
                if isinstance(referent, (dict, list, tuple)):
                    stack.append(referent)
    return reachable


class _GcTraverseChecked:
    """Callable standing in for `SchemaValidator`/`SchemaSerializer` during tests.

    On every construction, Python objects from the core schema retained by the instance (detected
    with `sys.getrefcount()` deltas) are checked to be reported to the garbage collector.
    """

    def __init__(self, cls: type) -> None:
        self._cls = cls

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cls, name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        schema = args[0] if args else kwargs.get('schema')
        if not _gc_traverse_check_active or not isinstance(schema, dict):
            return self._cls(*args, **kwargs)

        candidates: dict[int, Any] = {}
        _collect_gc_check_candidates(schema, candidates, set())
        refcounts = {obj_id: sys.getrefcount(obj) for obj_id, obj in candidates.items()}
        instance = self._cls(*args, **kwargs)
        retained = [obj for obj_id, obj in candidates.items() if sys.getrefcount(obj) > refcounts[obj_id]]
        if retained:
            reachable = _gc_traverse_reachable(instance, exclude_id=id(schema))
            missing = [obj for obj in retained if id(obj) not in reachable]
            if missing:
                missing_reprs = ', '.join(repr(obj) for obj in missing[:5])
                pytest.fail(
                    f'{self._cls.__name__} retains the following Python object(s) without reporting them '
                    f'to the garbage collector, which can result in memory leaks: {missing_reprs}. '
                    'This most likely means a field is missing from an `impl_py_gc_traverse!()` call in '
                    'the pydantic-core Rust sources. If this is a false positive, apply the '
                    '`skip_gc_traverse_check` marker to the test.'
                )
        return instance


_TESTS_DIR = str(Path(__file__).parent)


def pytest_collection_finish(session: pytest.Session) -> None:
    """Swap `SchemaValidator`/`SchemaSerializer` for their GC checked versions in every test module.

    Only modules inside the tests directory are patched (and only names referring to the actual
    classes), so that other consumers of pydantic-core importable in the test environment (e.g.
    the `pydantic` package itself) are unaffected.
    """
    replacements = [
        ('SchemaValidator', SchemaValidator, _GcTraverseChecked(SchemaValidator)),
        ('SchemaSerializer', SchemaSerializer, _GcTraverseChecked(SchemaSerializer)),
    ]
    for module in list(sys.modules.values()):
        module_file = getattr(module, '__file__', None)
        if module_file is not None and module_file.startswith(_TESTS_DIR):
            for name, real, checked in replacements:
                if getattr(module, name, None) is real:
                    setattr(module, name, checked)


@pytest.fixture(autouse=True)
def _gc_traverse_check(request: pytest.FixtureRequest):
    global _gc_traverse_check_active

    _gc_traverse_check_active = (
        sys.implementation.name == 'cpython'
        # `sys.getrefcount()` isn't reliable with deferred reference counting:
        and not is_free_threaded
        and 'benchmark' not in request.fixturenames
        and request.node.get_closest_marker('skip_gc_traverse_check') is None
    )
    try:
        yield
    finally:
        _gc_traverse_check_active = False


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
        self,
        schema: CoreSchema,
        config: CoreConfig | None = None,
        *,
        validator_type: Literal['json', 'python'] | None = None,
    ):
        self.validator = SchemaValidator(schema, config)
        self.validator_type = validator_type

    def validate_python(self, py_input, strict: bool | None = None, context: Any = None):
        return self.validator.validate_python(py_input, strict=strict, context=context)

    def validate_json(self, json_str: str, strict: bool | None = None, context: Any = None):
        return self.validator.validate_json(json_str, strict=strict, context=context)

    def validate_test(
        self, py_input, strict: bool | None = None, context: Any = None, extra: ExtraBehavior | None = None
    ):
        if self.validator_type == 'json':
            return self.validator.validate_json(
                json.dumps(py_input, default=json_default),
                strict=strict,
                extra=extra,
                context=context,
            )
        else:
            assert self.validator_type == 'python', self.validator_type
            return self.validator.validate_python(py_input, strict=strict, context=context, extra=extra)

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


PyAndJson = type[PyAndJsonValidator]


@pytest.fixture(params=['python', 'json'])
def py_and_json(request) -> PyAndJson:
    class ChosenPyAndJsonValidator(PyAndJsonValidator):
        __init__ = functools.partialmethod(PyAndJsonValidator.__init__, validator_type=request.param)

    return ChosenPyAndJsonValidator


class StrictModeType:
    def __init__(self, schema: bool, extra: bool):
        assert schema or extra
        self.schema = schema
        self.validator_args = {'strict': True} if extra else {}


@pytest.fixture(
    params=[
        StrictModeType(schema=True, extra=False),
        StrictModeType(schema=False, extra=True),
        StrictModeType(schema=True, extra=True),
    ],
    ids=['strict-schema', 'strict-extra', 'strict-both'],
)
def strict_mode_type(request) -> StrictModeType:
    return request.param


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
    def _import_execute(source: str, *, custom_module_name: str | None = None):
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

        # include major and minor version only
        return '.'.join(pydantic.__version__.split('.')[:2])
    except ImportError:
        return 'latest'


def infinite_generator():
    i = 0
    while True:
        yield i
        i += 1


def assert_gc(test: Callable[[], bool], timeout: float = 10) -> None:
    """Helper to retry garbage collection until the test passes or timeout is
    reached.

    This is useful on free-threading where the GC collect call finishes before
    all cleanup is done.
    """
    start = now = time()
    while now - start < timeout:
        if test():
            return
        gc.collect()
        sleep(0.1)
        now = time()
    raise AssertionError('Timeout waiting for GC')
