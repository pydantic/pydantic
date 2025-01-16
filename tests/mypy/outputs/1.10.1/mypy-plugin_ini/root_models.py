from typing import Generic, TypeVar

from pydantic import BaseModel, RootModel


class Pets1(RootModel[list[str]]):
    pass


pets_construct = Pets1.model_construct(['dog'])

Pets2 = RootModel[list[str]]


class Pets3(RootModel):
# MYPY: error: Missing type parameters for generic type "RootModel"  [type-arg]
    root: list[str]


pets1 = Pets1(['dog', 'cat'])
pets2 = Pets2(['dog', 'cat'])
pets3 = Pets3(['dog', 'cat'])


class Pets4(RootModel[list[str]]):
    pets: list[str]
# MYPY: error: Only `root` is allowed as a field of a `RootModel`  [pydantic-field]


T = TypeVar('T')
V = TypeVar('V')


class Maybe(RootModel[T | None]):
    pass


class Model(BaseModel, Generic[V]):
    m1: Maybe[int]
    m2: Maybe[V]
    m3: Maybe
# MYPY: error: Missing type parameters for generic type "Maybe"  [type-arg]


Model[str](m1=1, m2='dog', m3=[])
Model[str](m1=Maybe(None), m2=Maybe('dog'), m3=Maybe([]))
Model(m1=None, m2={}, m3=[])
