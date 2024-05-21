import datetime as dt
import pytest
import pytz
from dataclasses import dataclass
from functools import partial
from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated
from typing import Any, Callable, Optional


def test_tzinfo_validator_example_pattern() -> None:
    """test that tzinfo custom validator pattern works as explained"""

    def my_validator_function(tz_constraint: str | None, value: dt.datetime, handler: Callable):
        """validate tz_constraint and tz_info"""

        if tz_constraint == None:
            assert value.tzinfo == None
            return handler(value)

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
