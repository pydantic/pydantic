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
print(Response[str](data='value'))
print(Response[str](data='value').dict())
print(Response[DataModel](data=data).dict())
print(Response[DataModel](error=error).dict())
try:
    Response[int](data='value')
except ValidationError as e:
    print(e)
