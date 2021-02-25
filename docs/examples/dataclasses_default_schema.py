import dataclasses
from typing import List, Optional

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: List[int] = dataclasses.field(default_factory=lambda: [0])
    age: Optional[int] = dataclasses.field(
        default=None,
        metadata=dict(title='The age of the user', description='do not lie!')
    )
    height: Optional[int] = Field(None, title='The height in cm', ge=50, le=300)


user = User(id='42')
print(user.__pydantic_model__.schema())
