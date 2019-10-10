from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel, validator, ValidationError
from pydantic.generics import GenericModel


DataT = TypeVar('DataT')


class Error(BaseModel):
    code: int
    message: str


class DataModel(BaseModel):
    numbers: List[int]
    people: List[str]


class Response(GenericModel, Generic[DataT]):
    data: Optional[DataT]
    error: Optional[Error]

    @validator('error', always=True)
    def check_consistency(cls, v, values):
        if v is not None and values['data'] is not None:
            raise ValueError('must not provide both data and error')
        if v is None and values.get('data') is None:
            raise ValueError('must provide data or error')
        return v


data = DataModel(numbers=[1, 2, 3], people=[])
error = Error(code=404, message='Not found')

print(Response[int](data=1))
#> Response[int] data=1 error=None
print(Response[str](data='value'))
#> Response[str] data='value' error=None
print(Response[str](data='value').dict())
#> {'data': 'value', 'error': None}
print(Response[DataModel](data=data).dict())
#> {'data': {'numbers': [1, 2, 3], 'people': []}, 'error': None}
print(Response[DataModel](error=error).dict())
#> {'data': None, 'error': {'code': 404, 'message': 'Not found'}}

try:
    Response[int](data='value')
except ValidationError as e:
    print(e)
"""
4 validation errors
data
  value is not a valid integer (type=type_error.integer)
data
  value is not none (type=type_error.none.allowed)
error
  value is not a valid dict (type=type_error.dict)
error
  must provide data or error (type=value_error)
"""
