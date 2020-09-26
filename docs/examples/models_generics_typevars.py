from typing import Generic, TypeVar

from pydantic import ValidationError
from pydantic.generics import GenericModel

AT = TypeVar('AT')
BT = TypeVar('BT')


class Model(GenericModel, Generic[AT, BT]):
    a: AT
    b: BT


print(Model(a='a', b='a'))

IntT = TypeVar('IntT', bound=int)
typevar_model = Model[int, IntT]
print(typevar_model(a=1, b=1))
try:
    typevar_model(a='a', b='a')
except ValidationError as exc:
    print(exc)

concrete_model = typevar_model[int]
print(concrete_model(a=1, b=1))
