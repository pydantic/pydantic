import datetime
from pathlib import Path
from typing import Annotated

from pydantic import FilePath, NewPath
from pydantic.experimental.pipeline import validate_as

# TODO: since Pyright 1.1.384, support for PEP 746 was disabled.
# `a1` and `a2` should have a `pyright: ignore[reportInvalidTypeArguments]` comment.
a1 = Annotated[str, validate_as(int)]
a2 = Annotated[str, validate_as(str).transform(lambda x: int(x))]
a3 = Annotated[float, validate_as(float).gt(0)]  # should be able to compare float to int

a4 = Annotated[datetime.datetime, validate_as(datetime.datetime).datetime_tz_naive()]
a5 = Annotated[datetime.datetime, validate_as(str).datetime_tz_naive()]  # pyright: ignore[reportAttributeAccessIssue]
a6 = Annotated[
    datetime.datetime,
    (
        validate_as(str).transform(str.strip).validate_as(datetime.datetime).datetime_tz_naive()
        | validate_as(int).transform(datetime.datetime.fromtimestamp).datetime_tz_aware()
    ),
]

# Annotated types (e.g. NewPath, FilePath) should be accepted by validate_as.
# Fixes https://github.com/pydantic/pydantic/issues/12845
a7 = Annotated[Path, validate_as(NewPath)]
a8 = Annotated[Path, validate_as(FilePath)]
