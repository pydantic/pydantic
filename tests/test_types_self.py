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
        SelfRef(data=1, ref={'data': 2, 'ref': 3}).model_dump() == {'data': 1, 'ref': {'data': 2, 'ref': None}}
