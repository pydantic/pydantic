import json
import re
import sys
from datetime import datetime, timezone
from typing import Optional

import pytest
from dirty_equals import AnyThing, IsBytes, IsStr, IsTuple
from hypothesis import given, strategies
from typing_extensions import TypedDict

from pydantic_core import SchemaSerializer, SchemaValidator, ValidationError
from pydantic_core import core_schema as cs


@pytest.fixture(scope='module')
def datetime_schema():
    return SchemaValidator({'type': 'datetime'})


@given(strategies.datetimes())
def test_datetime_datetime(datetime_schema, data):
    assert datetime_schema.validate_python(data) == data


@pytest.mark.skipif(sys.platform == 'win32', reason='Can fail on windows, I guess due to 64-bit issue')
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
        assert datetime_schema.validate_python(data).replace(tzinfo=None) == expected, data


@given(strategies.binary())
def test_datetime_binary(datetime_schema, data):
    try:
        datetime_schema.validate_python(data)
    except ValidationError as exc:
        assert exc.errors(include_url=False) == [
            {
                'type': 'datetime_parsing',
                'loc': (),
                'msg': IsStr(regex='Input should be a valid datetime, .+'),
                'input': IsBytes(),
                'ctx': {'error': IsStr()},
            }
        ]


@pytest.fixture(scope='module')
def definition_schema():
    return SchemaValidator(
        cs.definitions_schema(
            cs.definition_reference_schema('Branch'),
            [
                cs.typed_dict_schema(
                    {
                        'name': cs.typed_dict_field(cs.str_schema()),
                        'sub_branch': cs.typed_dict_field(
                            cs.with_default_schema(
                                cs.nullable_schema(cs.definition_reference_schema('Branch')), default=None
                            )
                        ),
                    },
                    ref='Branch',
                )
            ],
        )
    )


def test_definition_simple(definition_schema):
    assert definition_schema.validate_python({'name': 'root'}) == {'name': 'root', 'sub_branch': None}


class BranchModel(TypedDict):
    name: str
    sub_branch: Optional['BranchModel']


@pytest.mark.skipif(sys.platform == 'emscripten', reason='Seems to fail sometimes on pyodide no idea why')
@given(strategies.from_type(BranchModel))
def test_recursive(definition_schema, data):
    assert definition_schema.validate_python(data) == data


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
def test_definition_cycles(definition_schema, data):
    try:
        assert definition_schema.validate_python(data) == data
    except ValidationError as exc:
        assert exc.errors(include_url=False) == [
            {
                'type': 'recursion_loop',
                'loc': IsTuple(length=(1, None)),
                'msg': 'Recursion error - cyclic reference detected',
                'input': AnyThing(),
            }
        ]


def test_definition_broken(definition_schema):
    data = {'name': 'x'}
    data['sub_branch'] = data
    with pytest.raises(ValidationError, match='Recursion error - cyclic reference detected'):
        definition_schema.validate_python(data)


@given(strategies.timedeltas())
def test_pytimedelta_as_timedelta(dt):
    v = SchemaValidator({'type': 'timedelta', 'gt': dt})
    # simplest way to check `pytimedelta_as_timedelta` is correct is to extract duration from repr of the validator
    m = re.search(r'Duration ?\{\s+positive: ?(\w+),\s+day: ?(\d+),\s+second: ?(\d+),\s+microsecond: ?(\d+)', repr(v))
    pos, day, sec, micro = m.groups()
    total_seconds = (1 if pos == 'true' else -1) * (int(day) * 86_400 + int(sec) + int(micro) / 1_000_000)

    assert total_seconds == pytest.approx(dt.total_seconds())


@pytest.fixture(scope='module')
def url_validator():
    return SchemaValidator({'type': 'url'})


# Parsing errors which hypothesis is likely to hit
_URL_PARSE_ERRORS = {'input is empty', 'relative URL without a base', 'empty host'}


@given(strategies.text())
def test_urls_text(url_validator, text):
    try:
        url_validator.validate_python(text)
    except ValidationError as exc:
        assert exc.error_count() == 1
        error = exc.errors(include_url=False)[0]
        assert error['type'] == 'url_parsing'
        assert error['ctx']['error'] in _URL_PARSE_ERRORS


@pytest.fixture(scope='module')
def multi_host_url_validator():
    return SchemaValidator({'type': 'multi-host-url'})


@given(strategies.text())
def test_multi_host_urls_text(multi_host_url_validator, text):
    try:
        multi_host_url_validator.validate_python(text)
    except ValidationError as exc:
        assert exc.error_count() == 1
        error = exc.errors(include_url=False)[0]
        assert error['type'] == 'url_parsing'
        assert error['ctx']['error'] in _URL_PARSE_ERRORS


@pytest.fixture(scope='module')
def str_serializer():
    return SchemaSerializer({'type': 'str'})


@given(strategies.text())
def test_serialize_string(str_serializer: SchemaSerializer, data):
    assert str_serializer.to_python(data) == data
    assert json.loads(str_serializer.to_json(data)) == data
