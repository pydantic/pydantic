from typing import TypeVar, Generic
from pydantic.generics import GenericModel

TypeX = TypeVar('TypeX')


class BaseClass(GenericModel, Generic[TypeX]):
    X: TypeX


class ChildClass(BaseClass[TypeX], Generic[TypeX]):
    # Inherit from Generic[TypeX]
    pass


# Replace TypeX by int
print(ChildClass[int](X=1))
