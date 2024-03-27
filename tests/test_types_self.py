import dataclasses
import typing
from typing import List, Optional, Union

import pytest
import typing_extensions
from typing_extensions import NamedTuple, TypedDict

from pydantic import BaseModel, Field, TypeAdapter, ValidationError


@pytest.fixture(
    name='Self',
    params=[
        pytest.param(typing, id='typing.Self'),
        pytest.param(typing_extensions, id='t_e.Self'),
    ],
)
def fixture_self_all(request):
    try:
        return request.param.Self
    except AttributeError:
        pytest.skip(f'Self is not available from {request.param}')


def test_recursive_model(Self):
    class SelfRef(BaseModel):
        data: int
        ref: typing.Optional[Self] = None

    assert SelfRef(data=1, ref={'data': 2}).model_dump() == {'data': 1, 'ref': {'data': 2, 'ref': None}}


def test_recursive_model_invalid(Self):
    class SelfRef(BaseModel):
        data: int
        ref: typing.Optional[Self] = None

    with pytest.raises(
        ValidationError,
        match=r'ref\.ref\s+Input should be a valid dictionary or instance of SelfRef \[type=model_type,',
    ):
        SelfRef(data=1, ref={'data': 2, 'ref': 3}).model_dump()


def test_recursive_model_with_subclass(Self):
    """Self refs should be valid and should reference the correct class in covariant direction"""

    class SelfRef(BaseModel):
        x: int
        ref: Self | None = None

    class SubSelfRef(SelfRef):
        y: int

    assert SubSelfRef(x=1, ref=SubSelfRef(x=3, y=4), y=2).model_dump() == {
        'x': 1,
        'ref': {'x': 3, 'ref': None, 'y': 4},  # SubSelfRef.ref: SubSelfRef
        'y': 2,
    }
    assert SelfRef(x=1, ref=SubSelfRef(x=2, y=3)).model_dump() == {
        'x': 1,
        'ref': {'x': 2, 'ref': None},
    }  # SelfRef.ref: SelfRef


def test_recursive_model_with_subclass_invalid(Self):
    """Self refs are invalid in contravariant direction"""

    class SelfRef(BaseModel):
        x: int
        ref: Self | None = None

    class SubSelfRef(SelfRef):
        y: int

    with pytest.raises(
        ValidationError,
        match=r'ref\s+Input should be a valid dictionary or instance of SubSelfRef \[type=model_type,',
    ):
        SubSelfRef(x=1, ref=SelfRef(x=2), y=3).model_dump()


def test_recursive_model_with_subclass_override(Self):
    """Self refs should be overridable"""

    class SelfRef(BaseModel):
        x: int
        ref: Self | None = None

    class SubSelfRef(SelfRef):
        y: int
        ref: Optional[Union[SelfRef, Self]] = None

    assert SubSelfRef(x=1, ref=SubSelfRef(x=3, y=4), y=2).model_dump() == {
        'x': 1,
        'ref': {'x': 3, 'ref': None, 'y': 4},
        'y': 2,
    }
    assert SubSelfRef(x=1, ref=SelfRef(x=3, y=4), y=2).model_dump() == {
        'x': 1,
        'ref': {'x': 3, 'ref': None},
        'y': 2,
    }


def test_self_type_with_field(Self):
    with pytest.raises(TypeError, match=r'The following constraints cannot be applied.*\'gt\''):

        class SelfRef(BaseModel):
            x: int
            refs: typing.List[Self] = Field(..., gt=0)


def test_self_type_json_schema(Self):
    class SelfRef(BaseModel):
        x: int
        refs: Optional[List[Self]] = []

    assert SelfRef.model_json_schema() == {
        '$defs': {
            'SelfRef': {
                'properties': {
                    'x': {'title': 'X', 'type': 'integer'},
                    'refs': {
                        'anyOf': [{'items': {'$ref': '#/$defs/SelfRef'}, 'type': 'array'}, {'type': 'null'}],
                        'default': [],
                        'title': 'Refs',
                    },
                },
                'required': ['x'],
                'title': 'SelfRef',
                'type': 'object',
            }
        },
        'allOf': [{'$ref': '#/$defs/SelfRef'}],
    }


def test_self_type_in_named_tuple(Self):
    class SelfRefNamedTuple(NamedTuple):
        x: int
        ref: Self | None

    ta = TypeAdapter(SelfRefNamedTuple)
    assert ta.validate_python({'x': 1, 'ref': {'x': 2, 'ref': None}}) == (1, (2, None))


def test_self_type_in_typed_dict(Self):
    class SelfRefTypedDict(TypedDict):
        x: int
        ref: Self | None

    ta = TypeAdapter(SelfRefTypedDict)
    assert ta.validate_python({'x': 1, 'ref': {'x': 2, 'ref': None}}) == {'x': 1, 'ref': {'x': 2, 'ref': None}}


def test_self_type_in_dataclass(Self):
    @dataclasses.dataclass(frozen=True)
    class SelfRef:
        x: int
        ref: Self | None

    class Model(BaseModel):
        item: SelfRef

    m = Model.model_validate({'item': {'x': 1, 'ref': {'x': 2, 'ref': None}}})
    assert m.item.x == 1
    assert m.item.ref.x == 2
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.item.ref.x = 3
