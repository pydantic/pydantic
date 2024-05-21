!!! warning "🚧 Work in Progress"
    This page is a work in progress.

## Validate `tzinfo` passed to an Annotated `datetime` type

A use case often arises where a user will want to add a timezone constraint in an annotated `datetime` type validation.

In this example, we want to use a string to specify the `tzinfo` of the `datetime` object.

We will use a customized validation with `__get_pydantic_core_schema__`:

```py
import datetime as dt
import pytz
from dataclasses import dataclass
from functools import partial
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

def my_validator_function(tz_constraint, value, handler):
    """validate tz_constraint and tz_info"""

    # handle naive datetimes
    if tz_constraint == None:
        assert value.tzinfo == None
        return handler(value)

    # validate tz_constraint and tz-aware tzinfo
    assert tz_constraint in pytz.all_timezones
    assert tz_constraint == str(value.tzinfo)

    return handler(value)

@dataclass(frozen=True)
class MyDatetimeValidator:
    tz_constraint: Optional[str] = None

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            partial(my_validator_function, self.tz_constraint), handler(source_type)
        )
```

We can then use the validator like so:

```py
LA = "America/Los_Angeles"

# passing naive test
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator()])
ta.validate_python(dt.datetime.now())

# failing naive test
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator()])
with pytest.raises(Exception):
    ta.validate_python(dt.datetime.now(pytz.timezone(LA)))

# passing tz-aware test
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
ta.validate_python(dt.datetime.now(pytz.timezone(LA)))

# failing bad tz
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator("foo")])
with pytest.raises(Exception):
    ta.validate_python(dt.datetime.now())

# failing tz-aware test
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
with pytest.raises(Exception):
    ta.validate_python(dt.datetime.now())
```
