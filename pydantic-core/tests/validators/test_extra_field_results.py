from collections.abc import Mapping
from operator import itemgetter

import pytest

from pydantic_core import (
    ArgsKwargs,
    PydanticOmit,
    PydanticUseDefault,
    SchemaError,
    SchemaValidator,
    ValidationError,
    core_schema,
)


@pytest.fixture(params=['typed-dict', 'model-fields', 'dataclass-args', 'arguments'])
def extra_schema(request):
    def build(extras):
        if request.param == 'typed-dict':
            return core_schema.typed_dict_schema({}, extra_behavior='allow', extras_schema=extras)
        if request.param == 'model-fields':
            schema = core_schema.model_fields_schema({}, extra_behavior='allow', extras_schema=extras)
            normalize = itemgetter(1)
        elif request.param == 'dataclass-args':
            schema = core_schema.dataclass_args_schema('Result', [], extra_behavior='allow')
            schema['extras_schema'] = extras
            normalize = itemgetter(0)
        else:
            schema = core_schema.arguments_schema([], var_kwargs_schema=extras)
            normalize = itemgetter(1)
        return core_schema.no_info_after_validator_function(normalize, schema)

    return build


@pytest.fixture(params=['python', 'json'])
def validate_extras(request):
    def validate(validator):
        if request.param == 'json':
            return validator.validate_json('{"first": 1, "second": 2}')
        return validator.validate_python({'first': 1, 'second': 2})

    return validate


@pytest.mark.parametrize('control', [PydanticOmit, PydanticUseDefault])
def test_extra_control_does_not_escape_to_parent(extra_schema, validate_extras, control):
    def check(value):
        if value == 1:
            raise control()
        return value

    schema = extra_schema(core_schema.no_info_after_validator_function(check, core_schema.int_schema()))
    validator = SchemaValidator(core_schema.with_default_schema(schema, default='outer default'))
    if control is PydanticOmit:
        assert validate_extras(validator) == {'second': 2}
    else:
        with pytest.raises(SchemaError, match='Uncaught.*UseDefault'):
            validate_extras(validator)


@pytest.mark.parametrize('control', [PydanticOmit, PydanticUseDefault])
def test_extra_key_control_does_not_escape_to_parent(validate_extras, control):
    def check(value):
        if value == 'first':
            raise control()
        return value

    schema = core_schema.model_fields_schema(
        {},
        extra_behavior='allow',
        extras_keys_schema=core_schema.no_info_after_validator_function(check, core_schema.str_schema()),
    )
    validator = SchemaValidator(core_schema.with_default_schema(schema, default='outer default'))
    if control is PydanticOmit:
        assert validate_extras(validator) == ({}, {'second': 2}, {'second'})
    else:
        with pytest.raises(SchemaError, match='Uncaught.*UseDefault'):
            validate_extras(validator)


def test_extra_default_is_handled_by_extra_validator(extra_schema, validate_extras):
    def check(value):
        if value == 1:
            raise PydanticUseDefault()
        return value

    extras = core_schema.with_default_schema(
        core_schema.no_info_after_validator_function(check, core_schema.int_schema()), default=42
    )
    assert validate_extras(SchemaValidator(extra_schema(extras))) == {'first': 42, 'second': 2}


def test_extra_internal_error_stops_validation(extra_schema, validate_extras):
    calls = []
    error = RuntimeError('broken validator')

    def check(value):
        calls.append(value)
        raise error

    validator = SchemaValidator(extra_schema(core_schema.no_info_plain_validator_function(check)))
    with pytest.raises(RuntimeError) as exc_info:
        validate_extras(validator)
    assert exc_info.value is error
    assert calls == [1]


def test_extra_key_and_value_errors_are_collected(extra_schema):
    validator = SchemaValidator(extra_schema(core_schema.int_schema()))
    data = {1: 'bad', 'second': 'bad', 3: 'bad'}
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python(data)
    assert [(e['type'], e['loc']) for e in exc_info.value.errors()] == [
        ('invalid_key', (1,)),
        ('int_parsing', ('second',)),
        ('invalid_key', (3,)),
    ]


@pytest.mark.parametrize('control', [PydanticOmit, PydanticUseDefault])
def test_argskwargs_extra_control(control):
    def check(value):
        if value == 1:
            raise control()
        return value

    schema = core_schema.arguments_v3_schema(
        [
            core_schema.arguments_v3_parameter(
                'kwargs', core_schema.no_info_plain_validator_function(check), mode='var_kwargs_uniform'
            )
        ]
    )
    validator = SchemaValidator(core_schema.with_default_schema(schema, default='outer default'))
    data = ArgsKwargs((), {'first': 1, 'second': 2})
    if control is PydanticOmit:
        assert validator.validate_python(data) == ((), {'second': 2})
    else:
        with pytest.raises(SchemaError, match='Uncaught.*UseDefault'):
            validator.validate_python(data)


def test_argskwargs_extra_errors_are_collected():
    validator = SchemaValidator(
        core_schema.arguments_v3_schema(
            [core_schema.arguments_v3_parameter('kwargs', core_schema.int_schema(), mode='var_kwargs_uniform')]
        )
    )
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python(ArgsKwargs((), {1: 'bad', 'second': 'bad'}))
    assert [(e['type'], e['loc']) for e in exc_info.value.errors()] == [
        ('invalid_key', (1,)),
        ('int_parsing', ('second',)),
    ]


@pytest.mark.parametrize('model', [False, True])
def test_mapping_entry_errors_are_collected(model):
    class Input(Mapping):
        def __getitem__(self, key):
            return 'bad'

        def __iter__(self):
            raise AssertionError('use items')

        def __len__(self):
            return 3

        def items(self):
            return [('a', 'bad'), ('malformed',), ('extra', 'bad')]

    if model:
        schema = core_schema.model_fields_schema(
            {'a': core_schema.model_field(core_schema.int_schema())},
            extra_behavior='allow',
            extras_schema=core_schema.int_schema(),
        )
    else:
        schema = core_schema.typed_dict_schema(
            {'a': core_schema.typed_dict_field(core_schema.int_schema())},
            extra_behavior='allow',
            extras_schema=core_schema.int_schema(),
        )
    with pytest.raises(ValidationError) as exc_info:
        SchemaValidator(schema).validate_python(Input())
    assert [(e['type'], e['loc']) for e in exc_info.value.errors()] == [
        ('int_parsing', ('a',)),
        ('mapping_type', ()),
        ('int_parsing', ('extra',)),
    ]


def test_mapping_items_exception_propagates_after_field_validation():
    calls = []
    error = RuntimeError('broken items')

    class Input(Mapping):
        def __getitem__(self, key):
            calls.append(key)
            return 1

        def __iter__(self):
            raise AssertionError('use items')

        def __len__(self):
            return 1

        def items(self):
            calls.append('items')
            raise error

    def check(value):
        calls.append('validate')
        return value

    validator = SchemaValidator(
        core_schema.typed_dict_schema(
            {'a': core_schema.typed_dict_field(core_schema.no_info_plain_validator_function(check))},
            extra_behavior='allow',
        )
    )
    with pytest.raises(RuntimeError) as exc_info:
        validator.validate_python(Input())
    assert exc_info.value is error
    assert calls == ['a', 'validate', 'items']
