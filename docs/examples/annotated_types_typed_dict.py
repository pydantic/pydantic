from typing import TypedDict

from pydantic import BaseModel, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: str
    surname: str


class User(TypedDict):
    identity: UserIdentity
    age: int


class Model(BaseModel):
    u: User


print(Model(u={'identity': {'name': 'Smith', 'surname': 'John'}, 'age': '37'}))

print(Model(u={'identity': {'name': None, 'surname': 'John'}, 'age': '37'}))

print(Model(u={'identity': {}, 'age': '37'}))


try:
    Model(u={'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': '24'})
except ValidationError as e:
    print(e)
