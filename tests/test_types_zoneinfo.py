from datetime import timezone
from zoneinfo import ZoneInfo

import pytest

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError


class ZoneInfoModel(BaseModel):
    tz: ZoneInfo


@pytest.mark.parametrize(
    'tz',
    [
        pytest.param(ZoneInfo('America/Los_Angeles'), id='ZoneInfoObject'),
        pytest.param('America/Los_Angeles', id='IanaTimezoneStr'),
    ],
)
def test_zoneinfo_valid_inputs(tz):
    model = ZoneInfoModel(tz=tz)
    assert model.tz == ZoneInfo('America/Los_Angeles')


def test_zoneinfo_serialization():
    model = ZoneInfoModel(tz=ZoneInfo('America/Los_Angeles'))
    assert model.model_dump_json() == '{"tz":"America/Los_Angeles"}'


def test_zoneinfo_parsing_fails_for_invalid_iana_tz_strs():
    with pytest.raises(ValidationError) as ex_info:
        ZoneInfoModel(tz='Zone/That_Does_Not_Exist')

    assert ex_info.value.errors() == [
        {
            'type': 'zoneinfo_str',
            'loc': ('tz',),
            'msg': 'invalid timezone: Zone/That_Does_Not_Exist',
            'input': 'Zone/That_Does_Not_Exist',
            'ctx': {'value': 'Zone/That_Does_Not_Exist'},
        }
    ]


@pytest.mark.parametrize(
    'tz',
    [
        pytest.param('America', id='tzdata-directory'),
        pytest.param('Etc', id='tzdata-directory-Etc'),
        pytest.param('a' * 300, id='over-long-key'),
    ],
)
def test_zoneinfo_parsing_fails_for_os_errors(tz):
    """https://github.com/pydantic/pydantic/issues/13908.

    These inputs fail inside `ZoneInfo(...)` with an `OSError` subclass rather
    than `ZoneInfoNotFoundError`: tzdata *directory* names raise
    `IsADirectoryError` on POSIX / `PermissionError` on Windows for Python < 3.13
    (CPython gh-85702 fixed this only in 3.13), and over-long keys raise
    `ENAMETOOLONG` / `EINVAL`. They must surface as `ValidationError`, just
    like unknown zones, so user-supplied timezones can't crash e.g. a web API
    with an unhandled exception.
    """
    with pytest.raises(ValidationError) as ex_info:
        ZoneInfoModel(tz=tz)

    assert ex_info.value.errors() == [
        {
            'type': 'zoneinfo_str',
            'loc': ('tz',),
            'msg': f'invalid timezone: {tz}',
            'input': tz,
            'ctx': {'value': tz},
        }
    ]


def test_zoneinfo_json_schema():
    assert ZoneInfoModel.model_json_schema() == {
        'type': 'object',
        'title': 'ZoneInfoModel',
        'properties': {'tz': {'type': 'string', 'format': 'zoneinfo', 'title': 'Tz'}},
        'required': ['tz'],
    }


def test_zoneinfo_union() -> None:
    ta = TypeAdapter(ZoneInfo | timezone, config=ConfigDict(arbitrary_types_allowed=True))
    assert ta.validate_python(timezone.utc) is timezone.utc
