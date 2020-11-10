import dataclasses
from datetime import datetime
from typing import Optional

import pydantic


@dataclasses.dataclass
class Meta:
    modified_date: Optional[datetime]
    seen_count: int


@dataclasses.dataclass
class File(Meta):
    filename: str


File = pydantic.dataclasses.dataclass(File)

file = File(
    filename=b'thefilename',
    modified_date='2020-01-01T00:00',
    seen_count='7',
)
print(file)

try:
    File(
        filename=['not', 'a', 'string'],
        modified_date=None,
        seen_count=3,
    )
except pydantic.ValidationError as e:
    print(e)
