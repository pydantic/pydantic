from enum import Enum
from pydantic import BaseModel, Schema

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
    foo_bar: FooBar = Schema(...)
    gender: Gender = Schema(
        None,
        alias='Gender',
    )
    snap: int = Schema(
        42,
        title='The Snap',
        description='this is the value of snap',
        gt=30,
        lt=50,
    )

    class Config:
        title = 'Main'

print(MainModel.schema())
# > {
#       'type': 'object',
#       'title': 'Main',
#       'properties': {
#           'foo_bar': {
#           ...
print(MainModel.schema_json(indent=2))
