import json
import platform
from typing import Any

try:
    from functools import cached_property
except ImportError:
    cached_property = None


from pydantic_core import SchemaSerializer, core_schema

from ..conftest import plain_repr

on_pypy = platform.python_implementation() == 'PyPy'
# pypy doesn't seem to maintain order of `__dict__`
if on_pypy:
    IsStrictDict = dict
else:
    pass


class RootModel:
    __slots__ = 'root'
    root: str

    def __init__(self, data):
        self.root = data


class RootSubModel(RootModel):
    pass


def test_model_root():
    s = SchemaSerializer(core_schema.model_schema(RootModel, core_schema.int_schema(), root_model=True))
    print(plain_repr(s))
    # TODO: assert 'mode:RootModel' in plain_repr(s)
    assert 'has_extra:false' in plain_repr(s)
    assert s.to_python(RootModel(1)) == 1
    assert s.to_python(RootSubModel(1)) == 1

    j = s.to_json(RootModel(1))
    if on_pypy:
        assert json.loads(j) == 1
    else:
        assert j == b'1'

    assert json.loads(s.to_json(RootSubModel(1))) == 1


def test_function_plain_field_serializer_to_python():
    class Model(RootModel):
        def ser_root(self, v: Any, _) -> str:
            assert self.root == 1_000
            return f'{v:_}'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.int_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(
                    Model.ser_root, is_field_serializer=True, info_arg=True
                )
            ),
            root_model=True,
        )
    )
    assert s.to_python(Model(1000)) == '1_000'


def test_function_wrap_field_serializer_to_python():
    class Model(RootModel):
        def ser_root(self, v: Any, serializer: core_schema.SerializerFunctionWrapHandler, _) -> str:
            root = serializer(v)
            assert self.root == 1_000
            return f'{root:_}'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.int_schema(
                serialization=core_schema.wrap_serializer_function_ser_schema(
                    Model.ser_root, is_field_serializer=True, info_arg=True, schema=core_schema.any_schema()
                )
            ),
            root_model=True,
        )
    )
    assert s.to_python(Model(1000)) == '1_000'


def test_function_plain_field_serializer_to_json():
    class Model(RootModel):
        def ser_root(self, v: Any, _) -> str:
            assert self.root == 1_000
            return f'{v:_}'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.int_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(
                    Model.ser_root, is_field_serializer=True, info_arg=True
                )
            ),
            root_model=True,
        )
    )
    assert json.loads(s.to_json(Model(1000))) == '1_000'


def test_function_wrap_field_serializer_to_json():
    class Model(RootModel):
        def ser_root(self, v: Any, serializer: core_schema.SerializerFunctionWrapHandler, _) -> str:
            assert self.root == 1_000
            root = serializer(v)
            return f'{root:_}'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.int_schema(
                serialization=core_schema.wrap_serializer_function_ser_schema(
                    Model.ser_root, is_field_serializer=True, info_arg=True, schema=core_schema.any_schema()
                )
            ),
            root_model=True,
        )
    )
    assert json.loads(s.to_json(Model(1000))) == '1_000'
