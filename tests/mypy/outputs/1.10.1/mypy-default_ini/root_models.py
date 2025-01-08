from typing import Generic, List, TypeVar

from pydantic import BaseModel, RootModel


class Pets1(RootModel[List[str]]):
    pass


pets_construct = Pets1.model_construct(['dog'])

Pets2 = RootModel[List[str]]


class Pets3(RootModel):
# MYPY: error: Missing type parameters for generic type "RootModel"  [type-arg]
    root: List[str]


pets1 = Pets1(['dog', 'cat'])
pets2 = Pets2(['dog', 'cat'])
pets3 = Pets3(['dog', 'cat'])


class Pets4(RootModel[List[str]]):
    pets: List[str]


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
# MYPY: error: Argument "m1" to "Model" has incompatible type "int"; expected "Maybe[int]"  [arg-type]
# MYPY: error: Argument "m2" to "Model" has incompatible type "str"; expected "Maybe[str]"  [arg-type]
# MYPY: error: Argument "m3" to "Model" has incompatible type "List[Never]"; expected "Maybe[Any]"  [arg-type]
Model[str](m1=Maybe(None), m2=Maybe('dog'), m3=Maybe([]))
Model(m1=None, m2={}, m3=[])
# MYPY: error: Argument "m1" to "Model" has incompatible type "None"; expected "Maybe[int]"  [arg-type]
# MYPY: error: Argument "m2" to "Model" has incompatible type "Dict[Never, Never]"; expected "Maybe[Never]"  [arg-type]
# MYPY: error: Argument "m3" to "Model" has incompatible type "List[Never]"; expected "Maybe[Any]"  [arg-type]
