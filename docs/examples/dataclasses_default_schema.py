import dataclasses
from typing import List
from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: List[int] = dataclasses.field(default_factory=lambda: [0])


user = User(id='42')
print(user.__pydantic_model__.schema())
