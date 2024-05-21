from typing import List

from pydantic import RootModel


class Pets1(RootModel[List[str]]):
    pass


pets_construct = Pets1.model_construct(['dog'])

Pets2 = RootModel[List[str]]


class Pets3(RootModel):
    root: List[str]


pets1 = Pets1(['dog', 'cat'])
pets2 = Pets2(['dog', 'cat'])
pets3 = Pets3(['dog', 'cat'])


class Pets4(RootModel[List[str]]):
    pets: List[str]
