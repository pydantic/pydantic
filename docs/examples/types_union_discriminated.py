from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class Cat(BaseModel):
    pet_type: Literal['cat']
    name: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    name: str


class Lizard(BaseModel):
    pet_type: Literal['reptile', 'lizard']
    name: str


class Model(BaseModel):
    pet: Union[Cat, Dog, Lizard] = Field(..., discriminator='pet_type')
    n: int


print(Model.parse_obj({'pet': {'pet_type': 'dog', 'name': 'woof'}, 'n': '1'}))
try:
    Model.parse_obj({'pet': {'pet_type': 'dog'}, 'n': '1'})
except ValidationError as e:
    print(e)
