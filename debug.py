from typing import TypeVar, List, Generic

from pydantic.generics import GenericModel


T = TypeVar("T")
S = TypeVar("S")

data_type = TypeVar('data_type')


class Result(GenericModel, Generic[data_type]):
    data: data_type


assert Result[List[int]].__name__ == 'Result[typing.List[int]]'
print(Result[List[int]](data=[1, 2]))
