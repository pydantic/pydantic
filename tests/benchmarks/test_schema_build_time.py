from typing import Literal, Union

from typing_extensions import Annotated

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
    animal: Annotated[Union[Cat, Dog], Discriminator('type')]


class NestedModel(BaseModel):
    animal: Annotated[Union[Cat, Dog], Discriminator('type')]


def test_construct_schema():
    @dataclass(frozen=True, kw_only=True)
    class Root:
        data_class: NestedDataClass
        model: NestedModel
