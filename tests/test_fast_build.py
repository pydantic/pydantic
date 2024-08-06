"""Tests for our experimental."""

import re
import time
from typing import Generic, List, Optional, TypeVar

import pytest
from typing_extensions import TypedDict

from pydantic import BaseModel, ConfigDict, ValidationError


@pytest.mark.xfail(
    reason='Models defined in function require namespace operations not yet compatible with `experimental_fast_build`'
)
def test_nested_annotation(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel as BM, ConfigDict

class BaseModel(BM):
    model_config = ConfigDict(experimental_fast_build=True)

def nested():
    class Foo(BaseModel):
        a: int

    class Bar(BaseModel):
        b: Foo

    return Bar
"""
    )

    bar_model = module.nested()
    assert bar_model.__pydantic_complete__ is True
    assert bar_model(b={'a': 1}).model_dump() == {'b': {'a': 1}}


@pytest.mark.xfail(
    reason='Models defined in function require namespace operations not yet compatible with `experimental_fast_build`'
)
def test_nested_annotation_priority(create_module):
    @create_module
    def module():
        from annotated_types import Gt
        from typing_extensions import Annotated

        from pydantic import BaseModel, ConfigDict

        Foobar = Annotated[int, Gt(0)]  # noqa: F841

        def nested():
            Foobar = Annotated[int, Gt(10)]

            class Bar(BaseModel):
                b: 'Foobar'

                model_config = ConfigDict(experimental_fast_build=True)

            return Bar

    bar_model = module.nested()
    assert bar_model.model_fields['b'].metadata[0].gt == 10
    assert bar_model(b=11).model_dump() == {'b': 11}
    with pytest.raises(ValidationError, match=r'Input should be greater than 10 \[type=greater_than,'):
        bar_model(b=1)


@pytest.mark.xfail(reason='Invalid parametrization of custom types is not yet supported with `experimental_fast_build`')
def test_invalid_forward_ref() -> None:
    class CustomType:
        """A custom type that isn't subscriptable."""

    msg = "Unable to evaluate type annotation 'CustomType[int]'."

    with pytest.raises(TypeError, match=re.escape(msg)):

        class Model(BaseModel):
            foo: 'CustomType[int]'

            model_config = ConfigDict(experimental_fast_build=True)


@pytest.mark.xfail(reason='This type of forward reference is not yet supported with `experimental_fast_build`')
def test_extra_validator_named() -> None:
    class BaseModel_(BaseModel):
        model_config = ConfigDict(experimental_fast_build=True)

    class Foo(BaseModel_):
        x: int

    class Model(BaseModel_):
        model_config = ConfigDict(extra='allow')
        __pydantic_extra__: 'dict[str, Foo]'

    class Child(Model):
        y: int

    m = Child(a={'x': '1'}, y=2)
    assert m.__pydantic_extra__ == {'a': Foo(x=1)}

    # insert_assert(Child.model_json_schema())
    assert Child.model_json_schema() == {
        '$defs': {
            'Foo': {
                'properties': {'x': {'title': 'X', 'type': 'integer'}},
                'required': ['x'],
                'title': 'Foo',
                'type': 'object',
            }
        },
        'additionalProperties': {'$ref': '#/$defs/Foo'},
        'properties': {'y': {'title': 'Y', 'type': 'integer'}},
        'required': ['y'],
        'title': 'Child',
        'type': 'object',
    }


@pytest.mark.xfail(reason='Parametrized TypedDicts are not yet supported with `experimental_fast_build`', strict=False)
def test_recursive_generic_typeddict_in_function_1():
    T = TypeVar('T')

    class BaseModel_(BaseModel):
        model_config = ConfigDict(experimental_fast_build=True)

    # First ordering: typed dict first
    class RecursiveGenTypedDict(TypedDict, Generic[T]):
        foo: Optional['RecursiveGenTypedDict[T]']
        ls: List[T]

    class RecursiveGenTypedDictModel(BaseModel_, Generic[T]):
        rec: 'RecursiveGenTypedDict[T]'

    # Note: no model_rebuild() necessary here
    # RecursiveGenTypedDictModel.model_rebuild()

    int_data: RecursiveGenTypedDict[int] = {'foo': {'foo': None, 'ls': [1]}, 'ls': [1]}
    assert RecursiveGenTypedDictModel[int](rec=int_data).rec == int_data

    str_data: RecursiveGenTypedDict[str] = {'foo': {'foo': None, 'ls': ['a']}, 'ls': ['a']}
    with pytest.raises(ValidationError) as exc_info:
        RecursiveGenTypedDictModel[int](rec=str_data)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('rec', 'foo', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {
            'input': 'a',
            'loc': ('rec', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]


@pytest.mark.xfail(reason='Parametrized TypedDicts are not yet supported with `experimental_fast_build`', strict=False)
def test_recursive_generic_typeddict_in_function_2():
    T = TypeVar('T')

    class BaseModel_(BaseModel):
        model_config = ConfigDict(experimental_fast_build=True)

    # Second ordering: model first
    class RecursiveGenTypedDictModel(BaseModel_, Generic[T]):
        rec: 'RecursiveGenTypedDict[T]'

    class RecursiveGenTypedDict(TypedDict, Generic[T]):
        foo: Optional['RecursiveGenTypedDict[T]']
        ls: List[T]

    int_data: RecursiveGenTypedDict[int] = {'foo': {'foo': None, 'ls': [1]}, 'ls': [1]}
    assert RecursiveGenTypedDictModel[int](rec=int_data).rec == int_data

    str_data: RecursiveGenTypedDict[str] = {'foo': {'foo': None, 'ls': ['a']}, 'ls': ['a']}
    with pytest.raises(ValidationError) as exc_info:
        RecursiveGenTypedDictModel[int](rec=str_data)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('rec', 'foo', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {
            'input': 'a',
            'loc': ('rec', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]


def experimental_fast_build_success() -> None:
    """If this test ends up being flaky we can disable, though I'd doubt it will, the difference is often on the order of 10-100x."""
    start = time.time()

    class SlowModel(BaseModel):
        x: int

    checkpoint = time.time()

    class FastModel(BaseModel):
        model_config = ConfigDict(experimental_fast_build=True)

        x: int

    end = time.time()

    assert checkpoint - start > end - checkpoint
