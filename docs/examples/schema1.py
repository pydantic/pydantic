from enum import IntEnum
from pydantic import BaseModel, Schema

class FooBar(BaseModel):
    count: int
    size: float = None

class Gender(IntEnum):
    male = 1
    female = 2
    other = 3
    not_given = 4

class MainModel(BaseModel):
    """
    This is the description of the main model
    """
    foo_bar: FooBar = Schema(...)
    gender: Gender = Schema(
        None,
        alias='Gender',
        choice_names={3: 'Other Gender', 4: "I'd rather not say"}
    )
    snap: int = Schema(
        42,
        title='The Snap',
        description='this is the value of snap'
    )

    class Config:
        title = 'Main'

print(MainModel.schema_json(indent=2))
