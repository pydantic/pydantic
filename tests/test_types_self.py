import typing

import pytest
import typing_extensions

from pydantic import BaseModel, ValidationError


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
    """
    Self refs should be valid and should reference the correct class in covariant direction
    """

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
    """
    Self refs are invalid in contravariant direction
    """

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
