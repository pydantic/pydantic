from pydantic import TypeAdapter, GetCoreSchemaHandler
from typing_extensions import Annotated
from datetime import datetime
from dataclasses import dataclass
from typing import Any
from pydantic_core import CoreSchema, core_schema
from functools import partial


def test_tzinfo_validator_example_pattern() -> None:
    """test that tzinfo custom validator pattern works as explained"""

    def my_validator_function(tz_constraint: str, value: datetime, handler):
        """strip and validate tzinfo"""

        # pre logic

        validated_dt = handler(value)

        # post logic

        return validated_dt

    @dataclass(frozen=True)
    class MyDatetimeValidator:
        tz_constraint: str

        def __get_pydantic_core_schema__(
            self, source_type: Any, handler: GetCoreSchemaHandler,
        ) -> CoreSchema:
            return core_schema.no_info_wrap_validator_function(
                partial(my_validator_function, self.tz_constraint), handler(source_type)
            )

    ta = TypeAdapter(Annotated[datetime, MyDatetimeValidator('UTC')])

    # print(pretty_print_core_schema(ta.core_schema))
    # """
    # {
    #     'type': 'function-wrap',
    #     'function': {
    #         'type': 'no-info',
    #         'function': functools.partial(<function my_validator_function at 0x104a73d90>, 'UTC')
    #     },
    #     'schema': {'type': 'datetime', 'microseconds_precision': 'truncate'}
    # }
    # """

    assert "'schema': {'type': 'datetime', 'microseconds_precision': 'truncate'}" in str(ta.core_schema)
    assert "tzinfo" not in str(ta.core_schema)

    my_dt = ta.validate_python(datetime.now())

    # print(my_dt)
    # > 2024-05-20 14:42:15.066963

    assert isinstance(my_dt, datetime)
    assert my_dt.tzinfo == datetime.timezone.utc
