import sys
from typing import Any, Dict, Generic, List, Optional, TypeVar

import pytest

from pydantic import BaseModel, ValidationError, validator
from pydantic.generics import BaseGenericModel, generic_name


skip_not_37 = pytest.mark.skipif(not sys.version_info >= (3, 7), reason='generics only supported for python 3.7')


@skip_not_37
def test_generic_name():
    data_type = TypeVar("data_type")

    class Result(BaseGenericModel, Generic[data_type]):
        data: data_type

    assert Result[List[int]].__name__ == "Result[typing.List[int]]"


@skip_not_37
def test_generic_name_edge_case_error():
    with pytest.raises(ValueError):
        generic_name((1,))


@skip_not_37
def test_generic_config():
    data_type = TypeVar("data_type")

    class Result(BaseGenericModel, Generic[data_type]):
        data: data_type

        class Config:
            allow_mutation = False

    result = Result[int](data=1)
    with pytest.raises(TypeError):
        result.data = 2


@skip_not_37
def test_generic_instantiation_error():
    data_type = TypeVar("data_type")

    class Result(BaseGenericModel, Generic[data_type]):
        data: data_type

        class Config:
            allow_mutation = False

    with pytest.raises(TypeError) as exc_info:
        Result(data=1)
    assert str(exc_info.value) == "Type Result cannot be instantiated without providing generic parameters"


@skip_not_37
def test_generic():
    data_type = TypeVar("data_type")
    error_type = TypeVar("error_type")

    class Result(BaseGenericModel, Generic[data_type, error_type]):
        data: Optional[List[data_type]]
        error: Optional[error_type]
        positive_number: int

        @validator("error", always=True)
        def validate_error(cls, v: Optional[error_type], values: Dict[str, Any]) -> Optional[error_type]:
            if values.get("data", None) is None and v is None:
                raise ValueError("Must provide data or error")
            if values.get("data", None) is not None and v is not None:
                raise ValueError("Must not provide both data and error")
            return v

        @validator("positive_number")
        def validate_positive_number(cls, v: int) -> int:
            if v < 0:
                raise ValueError
            return v

    class Error(BaseModel):
        message: str

    class Data(BaseModel):
        number: int
        text: str

    success1 = Result[Data, Error](data=[Data(number=1, text="a")], positive_number=1)
    assert success1.dict() == {'data': [{'number': 1, 'text': 'a'}], 'error': None, 'positive_number': 1}
    assert str(success1) == "Result[Data, Error] data=[<Data number=1 text='a'>] error=None positive_number=1"

    success2 = Result[Data, Error](error=Error(message="error"), positive_number=1)
    assert success2.dict() == {'data': None, 'error': {'message': 'error'}, 'positive_number': 1}
    assert str(success2) == "Result[Data, Error] data=None error=<Error message='error'> positive_number=1"
    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](error=Error(message="error"), positive_number=-1)
    assert exc_info.value.errors() == [{'loc': ('positive_number',), 'msg': '', 'type': 'value_error'}]

    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](data=[Data(number=1, text="a")], error=Error(message="error"), positive_number=1)
    assert exc_info.value.errors() == [
        {'loc': ('error',), 'msg': 'Must not provide both data and error', 'type': 'value_error'},
        {'loc': ('error',), 'msg': 'value is not none', 'type': 'type_error.none.allowed'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](data=[Data(number=1, text="a")], error=Error(message="error"), positive_number=1)
    assert exc_info.value.errors() == [
        {'loc': ('error',), 'msg': 'Must not provide both data and error', 'type': 'value_error'},
        {'loc': ('error',), 'msg': 'value is not none', 'type': 'type_error.none.allowed'},
    ]
