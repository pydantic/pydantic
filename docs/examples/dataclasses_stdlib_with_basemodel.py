import dataclasses
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError


@dataclasses.dataclass(frozen=True)
class User:
    name: str


@dataclasses.dataclass
class File:
    filename: str
    last_modification_time: Optional[datetime] = None


class Foo(BaseModel):
    file: File
    user: Optional[User] = None


file = File(
    filename=['not', 'a', 'string'],
    last_modification_time='2020-01-01T00:00',
)  # nothing is validated as expected
print(file)

try:
    Foo(file=file)
except ValidationError as e:
    print(e)

foo = Foo(file=File(filename='myfile'), user=User(name='pika'))
try:
    foo.user.name = 'bulbi'
except dataclasses.FrozenInstanceError as e:
    print(e)
