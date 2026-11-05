from datetime import timezone
from zoneinfo import ZoneInfo

import pytest

from pydantic import ConfigDict, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'tz',
    [
        pytest.param(ZoneInfo('America/Los_Angeles'), id='ZoneInfoObject'),
        pytest.param('America/Los_Angeles', id='IanaTimezoneStr'),
    ],
)
def test_zoneinfo_valid_inputs(tz: ZoneInfo | str) -> None:
    ta = TypeAdapter(ZoneInfo)

    assert ta.validate_python(tz) == ZoneInfo('America/Los_Angeles')


def test_zoneinfo_serialization() -> None:
    ta = TypeAdapter(ZoneInfo)

    assert ta.dump_json(ZoneInfo('America/Los_Angeles')) == b'"America/Los_Angeles"'


def test_zoneinfo_parsing_fails_for_invalid_iana_tz_strs() -> None:
    ta = TypeAdapter(ZoneInfo)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('Zone/That_Does_Not_Exist')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'zoneinfo_str',
            'loc': (),
            'msg': 'invalid timezone: Zone/That_Does_Not_Exist',
            'input': 'Zone/That_Does_Not_Exist',
            'ctx': {'value': 'Zone/That_Does_Not_Exist'},
        }
    ]


@pytest.mark.parametrize('value', ['America', 'a' * 300])
def test_zoneinfo_os_error_is_validation_error(value: str) -> None:
    """https://github.com/pydantic/pydantic/issues/13908"""
    ta = TypeAdapter(ZoneInfo)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'zoneinfo_str',
            'loc': (),
            'msg': f'invalid timezone: {value}',
            'input': value,
            'ctx': {'value': value},
        }
    ]


def test_zoneinfo_json_schema() -> None:
    ta = TypeAdapter(ZoneInfo)

    assert ta.json_schema() == {'type': 'string', 'format': 'zoneinfo'}


def test_zoneinfo_union() -> None:
    ta = TypeAdapter(ZoneInfo | timezone, config=ConfigDict(arbitrary_types_allowed=True))

    assert ta.validate_python(timezone.utc) is timezone.utc
