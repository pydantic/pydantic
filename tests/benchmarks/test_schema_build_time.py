from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator
from pydantic.dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Cat:
    type: Literal['cat'] = 'cat'


@dataclass(frozen=True, kw_only=True)
class Dog:
    type: Literal['dog'] = 'dog'


@dataclass(frozen=True, kw_only=True)
class NestedDataClass:
    animal: Annotated[Cat | Dog, Discriminator('type')]


class NestedModel(BaseModel):
    animal: Annotated[Cat | Dog, Discriminator('type')]


def test_construct_schema():
    @dataclass(frozen=True, kw_only=True)
    class Root:
        data_class: NestedDataClass
        model: NestedModel
