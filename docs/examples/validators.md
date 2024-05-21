!!! warning '🚧 Work in Progress'
    This page is a work in progress.

## Validate `tzinfo` passed to an Annotated `datetime` type

A use case often arises where a user will want to add a timezone constraint in an annotated `datetime` type validation.

In this example, we want to use a string to specify the `tzinfo` of the `datetime` object.

We will use a customized validation with `__get_pydantic_core_schema__`:

```py
import datetime as dt
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Optional

import pytz
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import GetCoreSchemaHandler, TypeAdapter


def my_validator_function(
    tz_constraint: str | None,
    value: dt.datetime,
    handler: Callable,
):
    """validate tz_constraint and tz_info"""

    # handle naive datetimes
    if tz_constraint is None:
        assert value.tzinfo is None
        return handler(value)

    # validate tz_constraint and tz-aware tzinfo
    assert tz_constraint in pytz.all_timezones
    assert tz_constraint == str(value.tzinfo)

    return handler(value)


@dataclass(frozen=True)
class MyDatetimeValidator:
    tz_constraint: Optional[str] = None

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            partial(my_validator_function, self.tz_constraint),
            handler(source_type),
        )


# We can then use the validator like so
LA = 'America/Los_Angeles'
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
ta.validate_python(dt.datetime.now(pytz.timezone(LA)))
```
