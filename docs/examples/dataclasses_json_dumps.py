import dataclasses
import json
from typing import List

from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: List[int] = dataclasses.field(default_factory=lambda: [0])


user = User(id='42')
print(json.dumps(user, indent=4, default=pydantic_encoder))
