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


# `ValidatedFile` will be a proxy around `File`
ValidatedFile = pydantic.dataclasses.dataclass(File)

# the original dataclass is the `__dataclass__` attribute
assert ValidatedFile.__dataclass__ is File


validated_file = ValidatedFile(
    filename=b'thefilename',
    modified_date='2020-01-01T00:00',
    seen_count='7',
)
print(validated_file)

try:
    ValidatedFile(
        filename=['not', 'a', 'string'],
        modified_date=None,
        seen_count=3,
    )
except pydantic.ValidationError as e:
    print(e)

# `File` is not altered and still does no validation by default
print(File(
    filename=['not', 'a', 'string'],
    modified_date=None,
    seen_count=3,
))
