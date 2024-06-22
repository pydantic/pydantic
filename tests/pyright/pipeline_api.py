import datetime
from typing import Annotated

from pydantic.experimental.pipeline import validate_as

# this test works by adding type ignores and having pyright fail with
# an unused type ignore error if the type checking isn't working
Annotated[str, validate_as(int)]  # type: ignore
Annotated[str, validate_as(str).transform(lambda x: int(x))]  # type: ignore
Annotated[float, validate_as(float).gt(0)]  # should be able to compare float to int
Annotated[datetime.datetime, validate_as(datetime.datetime).datetime_tz_naive()]
Annotated[datetime.datetime, validate_as(str).datetime_tz_naive()]  # type: ignore
Annotated[
    datetime.datetime,
    (
        validate_as(str).transform(str.strip).validate_as(datetime.datetime).datetime_tz_naive()
        | validate_as(int).transform(datetime.datetime.fromtimestamp).datetime_tz_aware()
    ),
]
