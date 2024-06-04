!!! warning "🚧 Work in Progress"
    This page is a work in progress.

This page provides example snippets for creating more complex, custom validators in Pydantic.

## Using Custom Validators with Annotated Metadata

In this example, we'll construct a custom validator, attached to an `Annotated` type,
that ensures a `datetime` object adheres to a given timezone constraint.

The custom validator supports string specification of the timezone, and will raise an error if the `datetime` object does not have the correct timezone.

We use `__get_pydantic_core_schema__` in the validator to customize the schema of the annotated type (in this case, `datetime`), which allows us to add custom validation logic. Notably, we use a `wrap` validator function so that we can perform operations both before and after the default `pydantic` validation of a `datetime`.

```py
import datetime as dt
from pprint import pprint
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Optional

import pytz
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import GetCoreSchemaHandler, PydanticUserError, TypeAdapter, ValidationError


@dataclass(frozen=True)
class MyDatetimeValidator:
    tz_constraint: Optional[str] = None

    def tz_constraint_validator(
        self,
        value: dt.datetime,
        handler: Callable,  # (1)!
    ):
        """Validate tz_constraint and tz_info."""
        # handle naive datetimes
        if self.tz_constraint is None:
            assert value.tzinfo is None, 'tz_constraint is None, but provided value is tz-aware.'
            return handler(value)

        # validate tz_constraint and tz-aware tzinfo
        if self.tz_constraint not in pytz.all_timezones:
            raise PydanticUserError(f'Invalid tz_constraint: {self.tz_constraint}', code='unevaluable-type-annotation')
        result = handler(value)  # (2)!
        assert self.tz_constraint == str(
            result.tzinfo
        ), f'Invalid tzinfo: {str(result.tzinfo)}, expected: {self.tz_constraint}'

        return result

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.tz_constraint_validator,
            handler(source_type),
        )


LA = 'America/Los_Angeles'
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
print(ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA))))
# > 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON)))
except ValidationError as ve:
    pprint(ve.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Invalid tzinfo: Europe/London, expected: America/Los_Angeles')},
    'input': datetime.datetime(2023, 1, 1, 0, 0, tzinfo=<DstTzInfo 'Europe/London' LMT-1 day, 23:59:00 STD>),
    'loc': (),
    'msg': 'Assertion failed, Invalid tzinfo: Europe/London, expected: America/Los_Angeles',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```

1. The `handler` function is what we call to validate the input with standard `pydantic` validation
2. We call the `handler` function to validate the input with standard `pydantic` validation in this wrap validator

We can also enforce UTC offset constraints in a similar way.  Assuming we have a `lower_bound` and an `upper_bound`, we can create a custom validator to ensure our `datetime` has a UTC offset that is inclusive within the boundary we define:


```py
import datetime as dt
from dataclasses import dataclass
from pprint import pprint
from typing import Any, Callable

import pytz
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import GetCoreSchemaHandler, TypeAdapter, ValidationError


@dataclass(frozen=True)
class MyDatetimeValidator:
    lower_bound: int
    upper_bound: int

    def validate_tz_bounds(self, value: dt.datetime, handler: Callable):
        """Validate and test bounds"""
        assert value.utcoffset() is not None, 'UTC offset must exist'
        assert self.lower_bound <= self.upper_bound, 'Invalid bounds'

        result = handler(value)

        hours_offset = value.utcoffset().total_seconds() / 3600
        assert self.lower_bound <= hours_offset <= self.upper_bound, 'Value out of bounds'

        return result

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.validate_tz_bounds,
            handler(source_type),
        )


LA = 'America/Los_Angeles'  # UTC-7 or UTC-8
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(-10, -5)])
print(ta.validate_python(dt.datetime.now(pytz.timezone(LA))))
# > 2024-06-04 10:49:44.053313-07:00

LONDON = 'Europe/London'
try:
    print(ta.validate_python(dt.datetime.now(pytz.timezone(LONDON))))
except ValidationError as e:
    pprint(e.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Value out of bounds')},
    'input': datetime.datetime(2024, 6, 4, 18, 49, 44, 54720, tzinfo=<DstTzInfo 'Europe/London' BST+1:00:00 DST>),
    'loc': (),
    'msg': 'Assertion failed, Value out of bounds',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```
