import json
import sys
from collections import namedtuple
from operator import itemgetter, methodcaller

import pytest

from pydantic_core import SchemaValidator, ValidationError, core_schema


@pytest.fixture(params=['arguments', 'arguments-v3', 'dataclass-args', 'typed-dict', 'named-tuple'])
def make_validator(request):
    def build(fields):
        if request.param in ('arguments', 'arguments-v3'):
            schema = {
                'type': request.param,
                'arguments_schema': [
                    core_schema.arguments_parameter(
                        name, field['schema'], alias=field.get('validation_alias'), mode='keyword_only'
                    )
                    for name, field in fields.items()
                ],
            }
            normalize = itemgetter(1)
        elif request.param == 'dataclass-args':
            schema = core_schema.dataclass_args_schema(
                'Result',
                [core_schema.dataclass_field(name, **field) for name, field in fields.items()],
                extra_behavior='forbid',
            )
            normalize = itemgetter(0)
        elif request.param == 'typed-dict':
            schema = core_schema.typed_dict_schema(
                {name: core_schema.typed_dict_field(**field) for name, field in fields.items()},
                total=False,
                extra_behavior='forbid',
            )
            normalize = dict
        else:
            schema = core_schema.named_tuple_schema(
                namedtuple('Result', fields),
                [core_schema.named_tuple_field(name, **field) for name, field in fields.items()],
            )
            normalize = methodcaller('_asdict')
        return SchemaValidator(core_schema.no_info_after_validator_function(normalize, schema))

    return build


@pytest.mark.parametrize('nested', [False, True])
def test_many_fields(make_validator, nested):
    fields = {
        f'k{i}': {
            'schema': core_schema.int_schema(),
            'validation_alias': ['payload', f'k{i}'] if nested else f'k{i}',
        }
        for i in range(100)
    }
    validator = make_validator(fields)
    expected = {f'k{i}': i for i in range(100)}
    data = dict(reversed(expected.items()))
    assert validator.validate_json(json.dumps({'payload': data} if nested else data)) == expected


@pytest.mark.parametrize(
    'alias,data',
    [
        ('x', '{"x": "invalid", "x": 2}'),
        ('x', '{"x": 1, "x": "invalid"}'),
        (['payload', 'x'], '{"payload": {"x": 1}, "payload": {"x": 2}}'),
        (['payload', 'x'], '{"payload": {"x": 1}, "payload": {}}'),
        (['payload', 'x'], '{"payload": {"x": 1}, "payload": null}'),
        (['payload', 'x'], '{"payload": {"x": 1, "x": 2}}'),
        (['payload', 'inner', 'x'], '{"payload": {"inner": {"x": 1}, "inner": {}}}'),
        ([['payload', 'x'], ['payload', 'y']], '{"payload": {"x": 1}, "payload": {"y": 2}}'),
        ([['payload', 'x'], ['payload', 'y']], '{"payload": {"y": 2, "x": 1}}'),
        ([['payload', 'x'], ['payload', 'y']], '{"payload": {"x": 1, "y": 2}}'),
        ([['payload', 'x'], ['payload', 'y']], '{"payload": {"x": "invalid", "y": 2}}'),
        ([['payload', -1], ['payload', 0]], '{"payload": [1, 2, 3]}'),
        (['payload', -4], '{"payload": [1, 2, 3]}'),
        (['payload', 4], '{"payload": [1, 2, 3]}'),
        (['payload', 0], '{"payload": "abc"}'),
        ('alias', '{"x": 1, "alias": 2}'),
        ('alias', '{"alias": 2, "x": 1}'),
    ],
)
@pytest.mark.parametrize('by_alias,by_name', [(True, False), (True, True), (False, True)])
def test_lookup_matches_python(make_validator, alias, data, by_alias, by_name):
    validator = make_validator(
        {
            'x': {'schema': core_schema.int_schema(), 'validation_alias': alias},
            'payload': {'schema': core_schema.with_default_schema(core_schema.any_schema(), default=None)},
        }
    )
    kwargs = {'by_alias': by_alias, 'by_name': by_name}
    try:
        expected = validator.validate_python(json.loads(data), **kwargs)
    except ValidationError as expected_error:
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_json(data, **kwargs)
        assert exc_info.value.errors(include_url=False) == expected_error.errors(include_url=False)
    else:
        assert validator.validate_json(data, **kwargs) == expected


@pytest.mark.parametrize('index', [sys.maxsize * 2 + 1, -sys.maxsize - 1])
def test_large_array_indices(make_validator, index):
    validator = make_validator(
        {'x': {'schema': core_schema.int_schema(), 'validation_alias': [['payload', index], ['payload', 0]]}}
    )
    assert validator.validate_json('{"payload": [1, 2, 3]}') == {'x': 1}


def test_shared_alias_and_field_order(make_validator):
    calls = []

    def schema(name):
        def record(value):
            calls.append((name, value))
            return value

        return core_schema.no_info_before_validator_function(record, core_schema.int_schema())

    validator = make_validator(
        {
            'a': {'schema': schema('a'), 'validation_alias': [['payload', 'x'], ['payload', 'y']]},
            'b': {'schema': schema('b'), 'validation_alias': ['payload', 'x']},
            'c': {'schema': schema('c')},
        }
    )
    assert validator.validate_json('{"c": 3, "payload": {"y": 2, "x": 0, "x": 1}}') == {'a': 1, 'b': 1, 'c': 3}
    assert calls == [('a', 1), ('b', 1), ('c', 3)]


def test_missing_alias_uses_default(make_validator):
    validator = make_validator(
        {
            'x': {
                'schema': core_schema.with_default_schema(core_schema.int_schema(), default=42),
                'validation_alias': ['payload', 'x'],
            },
            'payload': {'schema': core_schema.any_schema()},
        }
    )
    assert validator.validate_json('{"payload": {"x": 1}, "payload": {}}') == {'x': 42, 'payload': {}}


def test_python_lookup_stays_lazy(make_validator):
    data = {'a': 1, 'b': 2}
    calls = []

    def mutate(value):
        data['b'] = 20
        data['extra'] = 3
        return value

    def record(value):
        calls.append(value)
        return value

    validator = make_validator(
        {
            'a': {'schema': core_schema.no_info_before_validator_function(mutate, core_schema.int_schema())},
            'b': {'schema': core_schema.no_info_before_validator_function(record, core_schema.int_schema())},
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python(data)
    assert calls == [20]
    assert [(error['loc'], error['input']) for error in exc_info.value.errors()] == [(('extra',), 3)]


def test_unused_alias_duplicates_are_extras(make_validator):
    calls = []

    def record(value):
        calls.append(value)
        return value

    validator = make_validator(
        {
            'x': {
                'schema': core_schema.no_info_before_validator_function(record, core_schema.int_schema()),
                'validation_alias': [['first'], ['second']],
            }
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_json('{"second": 0, "first": 1, "second": 2}')
    assert calls == [1]
    assert [(error['loc'], error['input']) for error in exc_info.value.errors()] == [
        (('second',), 0),
        (('second',), 2),
    ]


def test_failed_field_is_not_extra(make_validator):
    validator = make_validator({'x': {'schema': core_schema.int_schema(), 'validation_alias': 'alias'}})
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_json('{"alias": "invalid", "extra": 2}')
    errors = exc_info.value.errors()
    assert [(error['loc'], error['input']) for error in errors] == [(('alias',), 'invalid'), (('extra',), 2)]
    assert errors[0]['type'] == 'int_parsing'


def test_typed_dict_partial_alias():
    validator = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'a': core_schema.typed_dict_field(core_schema.int_schema(), validation_alias=['payload', 'a']),
                'b': core_schema.typed_dict_field(core_schema.int_schema(), validation_alias=['payload', 'b']),
            },
            total=False,
        )
    )
    assert validator.validate_json('{"payload": {"a": 1, "b": "invalid"}}', allow_partial=True) == {'a': 1}
    assert validator.validate_json('{"payload": {"a": 1, "b":', allow_partial=True) == {'a': 1}
