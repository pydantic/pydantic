!!! warning "🚧 Work in Progress"
    This page is a work in progress.

This page provides example snippets for creating more complex, custom validators in Pydantic.

## Using Custom Validators with [`Annotated`][typing.Annotated] Metadata

In this example, we'll construct a custom validator, attached to an [`Annotated`][typing.Annotated] type,
that ensures a [`datetime`][datetime.datetime] object adheres to a given timezone constraint.

The custom validator supports string specification of the timezone, and will raise an error if the [`datetime`][datetime.datetime] object does not have the correct timezone.

We use `__get_pydantic_core_schema__` in the validator to customize the schema of the annotated type (in this case, [`datetime`][datetime.datetime]), which allows us to add custom validation logic. Notably, we use a `wrap` validator function so that we can perform operations both before and after the default `pydantic` validation of a [`datetime`][datetime.datetime].

```py
import datetime as dt
from dataclasses import dataclass
from pprint import pprint
from typing import Any, Callable, Optional

import pytz
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated

from pydantic import (
    GetCoreSchemaHandler,
    PydanticUserError,
    TypeAdapter,
    ValidationError,
)


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
            assert (
                value.tzinfo is None
            ), 'tz_constraint is None, but provided value is tz-aware.'
            return handler(value)

        # validate tz_constraint and tz-aware tzinfo
        if self.tz_constraint not in pytz.all_timezones:
            raise PydanticUserError(
                f'Invalid tz_constraint: {self.tz_constraint}',
                code='unevaluable-type-annotation',
            )
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
print(
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
)
#> 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    ta.validate_python(
        dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON))
    )
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
        assert (
            self.lower_bound <= hours_offset <= self.upper_bound
        ), 'Value out of bounds'

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
print(
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
)
#> 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    print(
        ta.validate_python(
            dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON))
        )
    )
except ValidationError as e:
    pprint(e.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Value out of bounds')},
    'input': datetime.datetime(2023, 1, 1, 0, 0, tzinfo=<DstTzInfo 'Europe/London' LMT-1 day, 23:59:00 STD>),
    'loc': (),
    'msg': 'Assertion failed, Value out of bounds',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```

## Validating Nested Model Fields with [`ValidationInfo`][pydantic_core.core_schema.ValidationInfo]

Here, we demonstrate two ways to validate a field in a nested model, where the validator utilizes field data from the parent model.

In this example, we construct a validator that chooses a single value from a list-like field, where the chosen value is determined by the index data specified by the parent model.

One way to do this is to place the validator in the parent model, with the field data from the nested model being accessible via a parameter of the validator.

```py
from pydantic import BaseModel, field_validator, ValidationInfo

class Foo(BaseModel):
    field1: str
    field2: int | None = None

class Item(BaseModel):
    idx: int
    foo_fields: Foo

    @field_validator("foo_fields", mode='before')
    def select_single_value(cls, fields: dict, info: ValidationInfo) -> dict:
        """Choose single value from space separated list based on specified index."""
        index = info.data.get("idx")
        field2_val_lst = fields['field2'].split()
        fields['field2'] = field2_val_lst[index] # select value and update field
        return fields

data = {
    "idx": 1,
    "foo_fields": {
        "field1": "woohoo",
        "field2": "74 97 29"
    }
}
print(Item.model_validate(data))
#> idx=1 foo_fields=Foo(field1='woohoo', field2=97)
```

If multiple fields in the ```Foo``` class need the single-value selection validation, then the above implementation can be tweaked in the ```select_single_value``` function to loop through all the relevant fields and apply the updates.

Alternatively, a validator can be placed in the nested model class (```Foo```), with the index data from the parent model being passed in via context from ```ValidationInfo```. This is demonstrated below.

```py
from pydantic import BaseModel, field_validator, ValidationInfo

class Foo(BaseModel):
    field1: str
    field2: int | None = None

    @field_validator("field2", mode='before')
    def select_single_value(cls, field2_val: str, info: ValidationInfo) -> dict:
        """Choose single value from space separated list based on specified index."""
        index = info.context.get("idx") # obtain index from validation context
        field2_val_lst = field2_val.split()
        return field2_val_lst[index]

class Item(BaseModel):
    idx: int
    foo_fields: Foo

    @field_validator("idx", mode='after')
    def add_context(cls, v: int, info: ValidationInfo):
        info.context.update({"idx": v}) # update the initially empty context with the idx
        return v

data = {
    "idx": 1,
    "foo_fields": {
        "field1": "woohoo",
        "field2": "74 97 29"
    }
}
print(Item.model_validate(data, context={}))
#> idx=1 foo_fields=Foo(field1='woohoo', field2=97)
```

Note that the context property must be initialized with ```model_validate``` in order to be used during the validation process.

More details about [field validators](https://docs.pydantic.dev/latest/concepts/validators/#field-validators) and [validation context](https://docs.pydantic.dev/latest/concepts/validators/#validation-context) can be found on the validators page.
