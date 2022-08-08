import dataclasses

from pydantic import ValidationError
from pydantic.dataclasses import dataclass as pydantic_dataclass, set_validation


@dataclasses.dataclass
class User:
    id: int
    name: str


# Enhance stdlib dataclass
pydantic_dataclass(User)


user1 = User(id='whatever', name='I want')

# validate data of `user1`
try:
    user1.__pydantic_validate_values__()
except ValidationError as e:
    print(e)

# Enforce validation
try:
    with set_validation(User, True):
        User(id='whatever', name='I want')
except ValidationError as e:
    print(e)
