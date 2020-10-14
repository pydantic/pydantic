from typing import TypeVar, Generic
from pydantic.generics import GenericModel

TypeX = TypeVar('TypeX')
TypeY = TypeVar('TypeY')


class BaseClass(GenericModel, Generic[TypeX]):
    x: TypeX


class ChildClass(BaseClass[int], Generic[TypeY]):
    y: TypeY


# Replace TypeY by str
print(ChildClass[str](x=1, y='y'))
