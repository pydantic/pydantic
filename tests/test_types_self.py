import dataclasses
import re
import typing
from typing import Optional, Union

import pytest
import typing_extensions
from typing_extensions import NamedTuple, TypedDict

from pydantic import BaseModel, Field, PydanticUserError, TypeAdapter, ValidationError, computed_field, validate_call

self_types = [typing_extensions.Self]
if hasattr(typing, 'Self'):
    self_types.append(typing.Self)

pytestmark = pytest.mark.parametrize('Self', self_types)


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
    class SelfRef(BaseModel):
        x: int
        refs: list[Self] = Field(gt=0)

    with pytest.raises(TypeError, match=re.escape("Unable to apply constraint 'gt' to supplied value []")):
        SelfRef(x=1, refs=[SelfRef(x=2, refs=[])])


def test_self_type_json_schema(Self):
    class SelfRef(BaseModel):
        x: int
        refs: Optional[list[Self]] = []

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
        '$ref': '#/$defs/SelfRef',
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


def test_invalid_validate_call(Self):
    with pytest.raises(PydanticUserError, match='`typing.Self` is invalid in this context'):

        @validate_call
        def foo(self: Self):
            pass


def test_invalid_validate_call_of_method(Self):
    with pytest.raises(PydanticUserError, match='`typing.Self` is invalid in this context'):

        class A(BaseModel):
            @validate_call
            def foo(self: Self):
                pass


def test_type_of_self(Self):
    class A(BaseModel):
        self_type: type[Self]

        @computed_field
        def self_types1(self) -> list[type[Self]]:
            return [type(self), self.self_type]

        # make sure forward refs are supported:
        @computed_field
        def self_types2(self) -> list[type['Self']]:
            return [type(self), self.self_type]

        @computed_field
        def self_types3(self) -> 'list[type[Self]]':
            return [type(self), self.self_type]

        @computed_field
        def self_types4(self) -> 'list[type[Self]]':
            return [type(self), self.self_type]

        @computed_field
        def self_types5(self) -> list['type[Self]']:
            return [type(self), self.self_type]

    class B(A): ...

    A(self_type=A)
    A(self_type=B)
    B(self_type=B)

    a = A(self_type=B)
    for prop in (a.self_types1, a.self_types2, a.self_types3):
        assert prop == [A, B]

    for invalid_type in (type, int, A, object):
        with pytest.raises(ValidationError) as exc_info:
            B(self_type=invalid_type)

        assert exc_info.value.errors(include_url=False) == [
            {
                'type': 'is_subclass_of',
                'loc': ('self_type',),
                'msg': f'Input should be a subclass of {B.__qualname__}',
                'input': invalid_type,
                'ctx': {'class': B.__qualname__},
            }
        ]
