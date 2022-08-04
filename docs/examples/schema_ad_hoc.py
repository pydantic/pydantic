from typing import Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Field, schema_json_of


class Cat(BaseModel):
    pet_type: Literal['cat']
    cat_name: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    dog_name: str


Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]

print(schema_json_of(Pet, title='The Pet Schema', indent=2))
