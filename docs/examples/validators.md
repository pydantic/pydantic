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
from typing import Any, Callable, Optional, Union

import pytz
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import GetCoreSchemaHandler, TypeAdapter


def my_validator_function(
    tz_constraint: Union[str, None],
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
    result = handler(value)
    assert tz_constraint == str(result.tzinfo)

    return result


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
ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
```

We can also create UTC offset constraints in a similar way.  Assuming we have a `lower_bound` and an `upper_bound`, we can create a custom validator to ensure our `datetime` has a UTC offset that is inclusive within the boundary we define:

```py
import datetime as dt
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable

import pytz
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import GetCoreSchemaHandler, TypeAdapter


def test_utcoffset_validator_example_pattern() -> None:
    """test that utcoffset custom validator pattern works as explained"""

    def my_validator_function(
        lower_bound: int,
        upper_bound: int,
        value: dt.datetime,
        handler: Callable,
    ):
        """validate and test bounds"""
        # validate utcoffset exists
        assert value.utcoffset() is not None

        # validate bound range
        assert lower_bound <= upper_bound

        result = handler(value)

        # validate value is in range
        hours_offset = value.utcoffset().total_seconds() / 3600

        assert hours_offset >= lower_bound
        assert hours_offset <= upper_bound

        return result

    @dataclass(frozen=True)
    class MyDatetimeValidator:
        lower_bound: int
        upper_bound: int

        def __get_pydantic_core_schema__(
            self,
            source_type: Any,
            handler: GetCoreSchemaHandler,
        ) -> CoreSchema:
            return core_schema.no_info_wrap_validator_function(
                partial(
                    my_validator_function,
                    self.lower_bound,
                    self.upper_bound,
                ),
                handler(source_type),
            )

    # We can then use the validator like so
    LA = 'America/Los_Angeles'

    # LA has a utcoffset of -7, which falls in the bounds of -10,10
    ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(-10, 10)])
    ta.validate_python(dt.datetime.now(pytz.timezone(LA)))
```
