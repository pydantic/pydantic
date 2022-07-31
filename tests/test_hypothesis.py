import re
from datetime import datetime, timezone
from typing import Optional

import pytest
from dirty_equals import AnyThing, IsBytes, IsList, IsStr
from hypothesis import given, strategies
from typing_extensions import TypedDict

from pydantic_core import SchemaValidator, ValidationError


@pytest.fixture(scope='module')
def datetime_schema():
    return SchemaValidator({'type': 'datetime'})


@given(strategies.datetimes())
def test_datetime_datetime(datetime_schema, data):
    assert datetime_schema.validate_python(data) == data


@given(strategies.integers(min_value=-11_676_096_000, max_value=253_402_300_799_000))
def test_datetime_int(datetime_schema, data):
    try:
        if abs(data) > 20_000_000_000:
            microsecond = (data % 1000) * 1000
            expected = datetime.fromtimestamp(data // 1000, tz=timezone.utc).replace(
                tzinfo=None, microsecond=microsecond
            )
        else:
            expected = datetime.fromtimestamp(data, tz=timezone.utc).replace(tzinfo=None)
    except OverflowError:
        pytest.skip('OverflowError, see pyodide/pyodide#2841, this can happen on 32-bit systems')
    else:
        assert datetime_schema.validate_python(data) == expected, data


@given(strategies.binary())
def test_datetime_binary(datetime_schema, data):
    try:
        datetime_schema.validate_python(data)
    except ValidationError as exc:
        assert exc.errors() == [
            {
                'kind': 'datetime_parsing',
                'loc': [],
                'message': IsStr(regex='Input should be a valid datetime, .+'),
                'input_value': IsBytes(),
                'context': {'error': IsStr()},
            }
        ]


@pytest.fixture(scope='module')
def recursive_schema():
    return SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'schema': {'type': 'str'}},
                'sub_branch': {
                    'schema': {'type': 'nullable', 'schema': {'type': 'recursive-ref', 'schema_ref': 'Branch'}},
                    'default': None,
                },
            },
        }
    )


def test_recursive_simple(recursive_schema):
    assert recursive_schema.validate_python({'name': 'root'}) == {'name': 'root', 'sub_branch': None}


class BranchModel(TypedDict):
    name: str
    sub_branch: Optional['BranchModel']


@given(strategies.from_type(BranchModel))
def test_recursive(recursive_schema, data):
    assert recursive_schema.validate_python(data) == data


@strategies.composite
def branch_models_with_cycles(draw, existing=None):
    if existing is None:
        existing = []
    model = BranchModel(name=draw(strategies.text()), sub_branch=None)
    existing.append(model)
    model['sub_branch'] = draw(
        strategies.none()
        | strategies.builds(BranchModel, name=strategies.text(), sub_branch=branch_models_with_cycles(existing))
        | strategies.sampled_from(existing)
    )
    return model


@given(branch_models_with_cycles())
def test_recursive_cycles(recursive_schema, data):
    try:
        assert recursive_schema.validate_python(data) == data
    except ValidationError as exc:
        assert exc.errors() == [
            {
                'kind': 'recursion_loop',
                'loc': IsList(length=(1, None)),
                'message': 'Recursion error - cyclic reference detected',
                'input_value': AnyThing(),
            }
        ]


def test_recursive_broken(recursive_schema):
    data = {'name': 'x'}
    data['sub_branch'] = data
    with pytest.raises(ValidationError, match='Recursion error - cyclic reference detected'):
        recursive_schema.validate_python(data)


@given(strategies.timedeltas())
def test_pytimedelta_as_timedelta(dt):
    v = SchemaValidator({'type': 'timedelta', 'gt': dt})
    # simplest way to check `pytimedelta_as_timedelta` is correct is to extract duration from repr of the validator
    m = re.search(r'Duration ?\{\s+positive: ?(\w+),\s+day: ?(\d+),\s+second: ?(\d+),\s+microsecond: ?(\d+)', repr(v))
    pos, day, sec, micro = m.groups()
    total_seconds = (1 if pos == 'true' else -1) * (int(day) * 86_400 + int(sec) + int(micro) / 1_000_000)

    assert total_seconds == pytest.approx(dt.total_seconds())
