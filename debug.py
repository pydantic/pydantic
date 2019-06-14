from typing import TypeVar, Dict, List

from pydantic import BaseModel
from pydantic.generics import GenericModel


T = TypeVar("T")
S = TypeVar("S")
R = TypeVar("R")


# class OuterModel(GenericModel[T, S, R]):
#     a: Dict[R, Optional[List[T]]]
#     b: Optional[Union[S, R]]
#     c: R
#     d: float
class OuterModel(GenericModel[T]):
    a: Dict[int, List[T]]


class InnerModel(GenericModel[T, R]):
    c: T
    d: R


class NormalModel(BaseModel):
    e: int
    f: str


# generic_model = OuterModel[InnerModel[int, str], NormalModel, int]

inner_models = [InnerModel[int, str](c=1, d="a")]
# print(inner_models)
# print(inner_models)
# kwargs = dict(
#     a={1: inner_models, 2: None}, b=None, c=1, d=1.5
# )
# generic_model(**kwargs)

OuterModel[InnerModel[int, str]](a={1: inner_models})
# generic_model(a={}, b=NormalModel(e=1, f="a"), c=1, d=1.5)
# generic_model(a={}, b=1, c=1, d=1.5)
