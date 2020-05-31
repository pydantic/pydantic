# output-json
from enum import Enum
from pydantic import BaseModel, Field


class FooBar(BaseModel):
    count: int
    size: float = None


class Gender(str, Enum):
    male = 'male'
    female = 'female'
    other = 'other'
    not_given = 'not_given'


class MainModel(BaseModel):
    """
    This is the description of the main model
    """

    foo_bar: FooBar = Field(...)
    gender: Gender = Field(None, alias='Gender')
    snap: int = Field(
        42,
        title='The Snap',
        description='this is the value of snap',
        gt=30,
        lt=50,
    )

    class Config:
        title = 'Main'


# this is equivalent to json.dumps(MainModel.schema(), indent=2):
print(MainModel.schema_json(indent=2))
