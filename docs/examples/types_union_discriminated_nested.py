from typing import Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['black']
    black_name: str


class WhiteCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['white']
    white_name: str


class Cat(BaseModel):
    __root__: Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]


class Dog(BaseModel):
    pet_type: Literal['dog']
    name: str


class Model(BaseModel):
    pet: Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]
    n: int


print(
    Model.parse_obj(
        {
            'pet': {'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'},
            'n': '1',
        }
    )
)
try:
    Model.parse_obj({'pet': {'pet_type': 'cat', 'color': 'red'}, 'n': '1'})
except ValidationError as e:
    print(e)
try:
    Model.parse_obj({'pet': {'pet_type': 'cat', 'color': 'black'}, 'n': '1'})
except ValidationError as e:
    print(e)
