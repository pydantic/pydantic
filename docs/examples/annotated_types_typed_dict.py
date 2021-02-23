from typing_extensions import TypedDict

from pydantic import BaseModel, Extra, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: str
    surname: str


class User(TypedDict):
    identity: UserIdentity
    age: int


class Model(BaseModel):
    u: User

    class Config:
        extra = Extra.forbid


print(Model(u={'identity': {'name': 'Smith', 'surname': 'John'}, 'age': '37'}))

print(Model(u={'identity': {'name': None, 'surname': 'John'}, 'age': '37'}))

print(Model(u={'identity': {}, 'age': '37'}))


try:
    Model(u={'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': '24'})
except ValidationError as e:
    print(e)

try:
    Model(
        u={
            'identity': {'name': 'Smith', 'surname': 'John'},
            'age': '37',
            'email': 'john.smith@me.com',
        }
    )
except ValidationError as e:
    print(e)
