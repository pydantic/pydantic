import dataclasses
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError


@dataclasses.dataclass
class File:
    filename: str
    last_modification_time: Optional[datetime]


class Foo(BaseModel):
    file: File


file = File(
    filename=['not', 'a', 'string'],
    last_modification_time='2020-01-01T00:00',
)  # nothing is validated as expected
print(file)

try:
    Foo(file=file)
except ValidationError as e:
    print(e)
