from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", covariant=True)


class Foo(BaseModel, Generic[T]):
    value: T


class Bar(Foo[T]): ...
