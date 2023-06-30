"""
Test mypy failure with invalid types.
"""
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class Model(BaseModel):
    list_of_ints: List[int]


class WrapperModel(BaseModel, Generic[T]):
    payload: T


model_instance = Model(list_of_ints=[1])
wrapper_instance = WrapperModel[Model](payload=model_instance)
wrapper_instance.payload.list_of_ints.append('1')
