import json
import platform
from typing import Any, List, Union

import pytest

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


class BaseModel:
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class RootModel:
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
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


@pytest.mark.parametrize('order', ['BR', 'RB'])
def test_root_model_dump_with_base_model(order):
    class BModel(BaseModel):
        value: str

    b_schema = core_schema.model_schema(
        BModel, core_schema.model_fields_schema({'value': core_schema.model_field(core_schema.str_schema())})
    )

    class RModel(RootModel):
        root: int

    r_schema = core_schema.model_schema(RModel, core_schema.int_schema(), root_model=True)

    if order == 'BR':

        class Model(RootModel):
            root: List[Union[BModel, RModel]]

        choices = [b_schema, r_schema]

    elif order == 'RB':

        class Model(RootModel):
            root: List[Union[RModel, BModel]]

        choices = [r_schema, b_schema]

    s = SchemaSerializer(
        core_schema.model_schema(
            Model, core_schema.list_schema(core_schema.union_schema(choices=choices)), root_model=True
        )
    )

    m = Model([RModel(1), RModel(2), BModel(value='abc')])

    assert s.to_python(m) == [1, 2, {'value': 'abc'}]
    assert s.to_json(m) == b'[1,2,{"value":"abc"}]'


def test_construct_nested():
    class RModel(RootModel):
        root: int

    class BModel(BaseModel):
        value: RModel

    s = SchemaSerializer(
        core_schema.model_schema(
            BModel,
            core_schema.model_fields_schema(
                {
                    'value': core_schema.model_field(
                        core_schema.model_schema(RModel, core_schema.int_schema(), root_model=True)
                    )
                }
            ),
        )
    )

    m = BModel(value=42)

    with pytest.raises(AttributeError, match="'int' object has no attribute 'root'"):
        s.to_python(m)
