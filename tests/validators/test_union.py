from dataclasses import dataclass
from datetime import date, time
from enum import Enum, IntEnum
from typing import Any
from uuid import UUID

import pytest
from dirty_equals import IsFloat, IsInt

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema, validate_core_schema

from ..conftest import plain_repr


@pytest.mark.parametrize(
    'input_value,expected_value',
    [
        (True, True),
        (False, False),
        ('true', True),
        ('false', False),
        (1, 1),
        (0, 0),
        (123, 123),
        ('123', 123),
        ('0', False),  # this case is different depending on the order of the choices
        ('1', True),  # this case is different depending on the order of the choices
    ],
)
def test_union_bool_int(input_value, expected_value):
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'bool'}, {'type': 'int'}]})
    assert v.validate_python(input_value) == expected_value


@pytest.mark.parametrize(
    'input_value,expected_value',
    [
        (True, True),
        (False, False),
        ('true', True),
        ('false', False),
        (1, 1),
        (0, 0),
        (123, 123),
        ('123', 123),
        ('0', 0),  # this case is different depending on the order of the choices
        ('1', 1),  # this case is different depending on the order of the choices
    ],
)
def test_union_int_bool(input_value, expected_value):
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'int'}, {'type': 'bool'}]})
    assert v.validate_python(input_value) == expected_value


class TestModelClass:
    class ModelA:
        pass

    class ModelB:
        pass

    @pytest.fixture(scope='class')
    def schema_validator(self) -> SchemaValidator:
        return SchemaValidator(
            {
                'type': 'union',
                'choices': [
                    {
                        'type': 'model',
                        'cls': self.ModelA,
                        'schema': {
                            'type': 'model-fields',
                            'fields': {
                                'a': {'type': 'model-field', 'schema': {'type': 'int'}},
                                'b': {'type': 'model-field', 'schema': {'type': 'str'}},
                            },
                        },
                    },
                    {
                        'type': 'model',
                        'cls': self.ModelB,
                        'schema': {
                            'type': 'model-fields',
                            'fields': {
                                'c': {'type': 'model-field', 'schema': {'type': 'int'}},
                                'd': {'type': 'model-field', 'schema': {'type': 'str'}},
                            },
                        },
                    },
                ],
            }
        )

    def test_model_a(self, schema_validator: SchemaValidator):
        m_a = schema_validator.validate_python({'a': 1, 'b': 'hello'})
        assert isinstance(m_a, self.ModelA)
        assert m_a.a == 1
        assert m_a.b == 'hello'

    def test_model_b(self, schema_validator: SchemaValidator):
        m_b = schema_validator.validate_python({'c': 2, 'd': 'again'})
        assert isinstance(m_b, self.ModelB)
        assert m_b.c == 2
        assert m_b.d == 'again'

    def test_exact_check(self, schema_validator: SchemaValidator):
        m_b = schema_validator.validate_python({'c': 2, 'd': 'again'})
        assert isinstance(m_b, self.ModelB)

        m_b2 = schema_validator.validate_python(m_b)
        assert m_b2 is m_b

    def test_error(self, schema_validator: SchemaValidator):
        with pytest.raises(ValidationError) as exc_info:
            schema_validator.validate_python({'a': 2})
        assert exc_info.value.errors(include_url=False) == [
            {'type': 'missing', 'loc': ('ModelA', 'b'), 'msg': 'Field required', 'input': {'a': 2}},
            {'type': 'missing', 'loc': ('ModelB', 'c'), 'msg': 'Field required', 'input': {'a': 2}},
            {'type': 'missing', 'loc': ('ModelB', 'd'), 'msg': 'Field required', 'input': {'a': 2}},
        ]


class TestModelClassSimilar:
    class ModelA:
        pass

    class ModelB:
        pass

    @pytest.fixture(scope='class')
    def schema_validator(self) -> SchemaValidator:
        return SchemaValidator(
            {
                'type': 'union',
                'choices': [
                    {
                        'type': 'model',
                        'cls': self.ModelA,
                        'schema': {
                            'type': 'model-fields',
                            'fields': {
                                'a': {'type': 'model-field', 'schema': {'type': 'int'}},
                                'b': {'type': 'model-field', 'schema': {'type': 'str'}},
                            },
                        },
                    },
                    {
                        'type': 'model',
                        'cls': self.ModelB,
                        'schema': {
                            'type': 'model-fields',
                            'fields': {
                                'a': {'type': 'model-field', 'schema': {'type': 'int'}},
                                'b': {'type': 'model-field', 'schema': {'type': 'str'}},
                                'c': {
                                    'type': 'model-field',
                                    'schema': {'type': 'default', 'schema': {'type': 'float'}, 'default': 1.0},
                                },
                            },
                        },
                    },
                ],
            }
        )

    def test_model_a(self, schema_validator: SchemaValidator):
        m = schema_validator.validate_python({'a': 1, 'b': 'hello'})
        assert isinstance(m, self.ModelA)
        assert m.a == 1
        assert m.b == 'hello'
        assert not hasattr(m, 'c')

    def test_model_b_ignored(self, schema_validator: SchemaValidator):
        # first choice works, so second choice is not used
        m = schema_validator.validate_python({'a': 1, 'b': 'hello', 'c': 2.0})
        assert isinstance(m, self.ModelA)
        assert m.a == 1
        assert m.b == 'hello'
        assert not hasattr(m, 'c')

    def test_model_b_not_ignored(self, schema_validator: SchemaValidator):
        m1 = self.ModelB()
        m1.a = 1
        m1.b = 'hello'
        m1.c = 2.0
        m2 = schema_validator.validate_python(m1)
        assert isinstance(m2, self.ModelB)
        assert m2.a == 1
        assert m2.b == 'hello'
        assert m2.c == 2.0


def test_nullable_via_union():
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'none'}, {'type': 'int'}]})
    assert v.validate_python(None) is None
    assert v.validate_python(1) == 1
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('hello')
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'none_required', 'loc': ('none',), 'msg': 'Input should be None', 'input': 'hello'},
        {
            'type': 'int_parsing',
            'loc': ('int',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'hello',
        },
    ]


def test_union_list_bool_int():
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'list', 'items_schema': {'type': 'bool'}},
                {'type': 'list', 'items_schema': {'type': 'int'}},
            ],
        }
    )
    assert v.validate_python(['true', True, 'no']) == [True, True, False]
    assert v.validate_python([5, 6, '789']) == [5, 6, 789]
    assert v.validate_python(['1', '0']) == [1, 0]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([3, 'true'])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'bool_parsing',
            'loc': ('list[bool]', 0),
            'msg': 'Input should be a valid boolean, unable to interpret input',
            'input': 3,
        },
        {
            'type': 'int_parsing',
            'loc': ('list[int]', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'true',
        },
    ]


def test_no_choices(pydantic_version):
    with pytest.raises(SchemaError) as exc_info:
        validate_core_schema({'type': 'union'})

    assert str(exc_info.value) == (
        'Invalid Schema:\n'
        'union.choices\n'
        "  Field required [type=missing, input_value={'type': 'union'}, input_type=dict]\n"
        f'    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/missing'
    )
    assert exc_info.value.error_count() == 1
    assert exc_info.value.errors() == [
        {'input': {'type': 'union'}, 'loc': ('union', 'choices'), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_empty_choices():
    msg = r'Error building "union" validator:\s+SchemaError: One or more union choices required'
    with pytest.raises(SchemaError, match=msg):
        SchemaValidator({'type': 'union', 'choices': []})


def test_one_choice():
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'str'}]})
    assert (
        plain_repr(v)
        == 'SchemaValidator(title="str",validator=Str(StrValidator{strict:false,coerce_numbers_to_str:false}),definitions=[],cache_strings=True)'
    )
    assert v.validate_python('hello') == 'hello'


def test_strict_union():
    v = SchemaValidator({'type': 'union', 'strict': True, 'choices': [{'type': 'bool'}, {'type': 'int'}]})
    assert v.validate_python(1) == 1
    assert v.validate_python(123) == 123

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('123')

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'bool_type', 'loc': ('bool',), 'msg': 'Input should be a valid boolean', 'input': '123'},
        {'type': 'int_type', 'loc': ('int',), 'msg': 'Input should be a valid integer', 'input': '123'},
    ]


def test_custom_error():
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [{'type': 'str'}, {'type': 'bytes'}],
            'custom_error_type': 'my_error',
            'custom_error_message': 'Input should be a string or bytes',
        }
    )
    assert v.validate_python('hello') == 'hello'
    assert v.validate_python(b'hello') == b'hello'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(123)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'my_error', 'loc': (), 'msg': 'Input should be a string or bytes', 'input': 123}
    ]


def test_custom_error_type():
    v = SchemaValidator(
        {'type': 'union', 'choices': [{'type': 'str'}, {'type': 'bytes'}], 'custom_error_type': 'string_type'}
    )
    assert v.validate_python('hello') == 'hello'
    assert v.validate_python(b'hello') == b'hello'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(123)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': (), 'msg': 'Input should be a valid string', 'input': 123}
    ]


def test_custom_error_type_context():
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [{'type': 'str'}, {'type': 'bytes'}],
            'custom_error_type': 'less_than',
            'custom_error_context': {'lt': 42},
        }
    )
    assert v.validate_python('hello') == 'hello'
    assert v.validate_python(b'hello') == b'hello'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(123)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'less_than', 'loc': (), 'msg': 'Input should be less than 42', 'input': 123, 'ctx': {'lt': 42.0}}
    ]


def test_dirty_behaviour():
    """
    Check dirty-equals does what we expect.
    """

    assert 1 == IsInt(approx=1, delta=0)
    assert 1.0 != IsInt(approx=1, delta=0)
    assert 1 != IsFloat(approx=1, delta=0)
    assert 1.0 == IsFloat(approx=1, delta=0)


def test_int_float():
    v = SchemaValidator(core_schema.union_schema([core_schema.int_schema(), core_schema.float_schema()]))
    assert v.validate_python(1) == IsInt(approx=1, delta=0)
    assert v.validate_json('1') == IsInt(approx=1, delta=0)
    assert v.validate_python(1.0) == IsFloat(approx=1, delta=0)
    assert v.validate_json('1.0') == IsFloat(approx=1, delta=0)

    v = SchemaValidator(core_schema.union_schema([core_schema.float_schema(), core_schema.int_schema()]))
    assert v.validate_python(1) == IsInt(approx=1, delta=0)
    assert v.validate_json('1') == IsInt(approx=1, delta=0)
    assert v.validate_python(1.0) == IsFloat(approx=1, delta=0)
    assert v.validate_json('1.0') == IsFloat(approx=1, delta=0)


def test_str_float():
    v = SchemaValidator(core_schema.union_schema([core_schema.str_schema(), core_schema.float_schema()]))

    assert v.validate_python(1) == IsFloat(approx=1, delta=0)
    assert v.validate_json('1') == IsFloat(approx=1, delta=0)
    assert v.validate_python(1.0) == IsFloat(approx=1, delta=0)
    assert v.validate_json('1.0') == IsFloat(approx=1, delta=0)

    assert v.validate_python('1.0') == '1.0'
    assert v.validate_python('1') == '1'
    assert v.validate_json('"1.0"') == '1.0'
    assert v.validate_json('"1"') == '1'

    v = SchemaValidator(core_schema.union_schema([core_schema.float_schema(), core_schema.str_schema()]))
    assert v.validate_python(1) == IsFloat(approx=1, delta=0)
    assert v.validate_json('1') == IsFloat(approx=1, delta=0)
    assert v.validate_python(1.0) == IsFloat(approx=1, delta=0)
    assert v.validate_json('1.0') == IsFloat(approx=1, delta=0)

    assert v.validate_python('1.0') == '1.0'
    assert v.validate_python('1') == '1'
    assert v.validate_json('"1.0"') == '1.0'
    assert v.validate_json('"1"') == '1'


def test_no_strict_check():
    v = SchemaValidator(core_schema.union_schema([core_schema.is_instance_schema(int), core_schema.json_schema()]))
    assert v.validate_python(123) == 123
    assert v.validate_python('[1, 2, 3]') == [1, 2, 3]


def test_strict_reference():
    v = SchemaValidator(
        core_schema.definitions_schema(
            core_schema.definition_reference_schema(schema_ref='tuple-ref'),
            [
                core_schema.tuple_positional_schema(
                    [
                        core_schema.float_schema(),
                        core_schema.union_schema(
                            [core_schema.int_schema(), core_schema.definition_reference_schema('tuple-ref')]
                        ),
                    ],
                    ref='tuple-ref',
                )
            ],
        )
    )

    assert repr(v.validate_python((1, 2))) == '(1.0, 2)'
    assert repr(v.validate_python((1.0, (2.0, 3)))) == '(1.0, (2.0, 3))'


def test_case_labels():
    v = SchemaValidator(
        {'type': 'union', 'choices': [{'type': 'none'}, ({'type': 'int'}, 'my_label'), {'type': 'str'}]}
    )
    assert v.validate_python(None) is None
    assert v.validate_python(1) == 1
    with pytest.raises(ValidationError, match=r'3 validation errors for union\[none,my_label,str]') as exc_info:
        v.validate_python(1.5)
    assert exc_info.value.errors(include_url=False) == [
        {'input': 1.5, 'loc': ('none',), 'msg': 'Input should be None', 'type': 'none_required'},
        {
            'input': 1.5,
            'loc': ('my_label',),
            'msg': 'Input should be a valid integer, got a number with a fractional part',
            'type': 'int_from_float',
        },
        {'input': 1.5, 'loc': ('str',), 'msg': 'Input should be a valid string', 'type': 'string_type'},
    ]


def test_left_to_right_doesnt_care_about_strict_check():
    v = SchemaValidator(
        core_schema.union_schema([core_schema.int_schema(), core_schema.json_schema()], mode='left_to_right')
    )
    assert 'strict_required' not in plain_repr(v)
    assert 'ultra_strict_required' not in plain_repr(v)


def test_left_to_right_union():
    choices = [core_schema.int_schema(), core_schema.float_schema()]

    # smart union prefers float
    v = SchemaValidator(core_schema.union_schema(choices, mode='smart'))
    out = v.validate_python(1.0)
    assert out == 1.0
    assert isinstance(out, float)

    # left_to_right union will select int
    v = SchemaValidator(core_schema.union_schema(choices, mode='left_to_right'))
    out = v.validate_python(1)
    assert out == 1
    assert isinstance(out, int)

    out = v.validate_python(1.0)
    assert out == 1
    assert isinstance(out, int)

    # reversing them will select float
    v = SchemaValidator(core_schema.union_schema(list(reversed(choices)), mode='left_to_right'))
    out = v.validate_python(1.0)
    assert out == 1.0
    assert isinstance(out, float)

    out = v.validate_python(1)
    assert out == 1.0
    assert isinstance(out, float)


def test_left_to_right_union_strict():
    choices = [core_schema.int_schema(), core_schema.float_schema()]

    # left_to_right union will select not cast if int first (strict int will not accept float)
    v = SchemaValidator(core_schema.union_schema(choices, mode='left_to_right', strict=True))
    out = v.validate_python(1)
    assert out == 1
    assert isinstance(out, int)

    out = v.validate_python(1.0)
    assert out == 1.0
    assert isinstance(out, float)

    # reversing union will select float always (as strict float will accept int)
    v = SchemaValidator(core_schema.union_schema(list(reversed(choices)), mode='left_to_right', strict=True))
    out = v.validate_python(1.0)
    assert out == 1.0
    assert isinstance(out, float)

    out = v.validate_python(1)
    assert out == 1.0
    assert isinstance(out, float)


def test_union_function_before_called_once():
    # See https://github.com/pydantic/pydantic/issues/6830 - in particular the
    # smart union validator used to call `remove_prefix` twice, which is not
    # ideal from a user perspective.
    class SpecialValues(str, Enum):
        DEFAULT = 'default'
        OTHER = 'other'

    special_values_schema = core_schema.no_info_after_validator_function(SpecialValues, core_schema.str_schema())

    validator_called_count = 0

    def remove_prefix(v: str):
        nonlocal validator_called_count
        validator_called_count += 1
        if v.startswith('uuid::'):
            return v[6:]
        return v

    prefixed_uuid_schema = core_schema.no_info_before_validator_function(remove_prefix, core_schema.uuid_schema())

    v = SchemaValidator(core_schema.union_schema([special_values_schema, prefixed_uuid_schema]))

    assert v.validate_python('uuid::12345678-1234-5678-1234-567812345678') == UUID(
        '12345678-1234-5678-1234-567812345678'
    )
    assert validator_called_count == 1


@pytest.mark.parametrize(
    ('schema', 'input_value', 'expected_value'),
    (
        (
            core_schema.uuid_schema(),
            '12345678-1234-5678-1234-567812345678',
            UUID('12345678-1234-5678-1234-567812345678'),
        ),
        (core_schema.date_schema(), '2020-01-01', date(2020, 1, 1)),
        (core_schema.time_schema(), '00:00:00', time(0, 0, 0)),
        # In V2.4 these already returned strings, so we keep this behaviour in V2
        (core_schema.datetime_schema(), '2020-01-01:00:00:00', '2020-01-01:00:00:00'),
        (core_schema.url_schema(), 'https://foo.com', 'https://foo.com'),
        (core_schema.multi_host_url_schema(), 'https://bar.com,foo.com', 'https://bar.com,foo.com'),
    ),
)
def test_smart_union_json_string_types(schema: core_schema.CoreSchema, input_value: str, expected_value: Any):
    # Many types have to be represented in strings as JSON, we make sure that
    # when parsing in JSON mode these types are preferred
    # TODO: in V3 we will make str win in all these cases.

    validator = SchemaValidator(core_schema.union_schema([schema, core_schema.str_schema()]))
    assert validator.validate_json(f'"{input_value}"') == expected_value
    # in Python mode the string will be preferred
    assert validator.validate_python(input_value) == input_value


@pytest.mark.parametrize(
    ('schema', 'input_value'),
    (
        pytest.param(
            core_schema.uuid_schema(),
            '12345678-1234-5678-1234-567812345678',
            marks=pytest.mark.xfail(reason='TODO: V3'),
        ),
        (core_schema.date_schema(), '2020-01-01'),
        (core_schema.time_schema(), '00:00:00'),
        (core_schema.datetime_schema(), '2020-01-01:00:00:00'),
        (core_schema.url_schema(), 'https://foo.com'),
        (core_schema.multi_host_url_schema(), 'https://bar.com,foo.com'),
    ),
)
def test_smart_union_json_string_types_str_first(schema: core_schema.CoreSchema, input_value: str):
    # As above, but reversed order; str should always win
    validator = SchemaValidator(core_schema.union_schema([core_schema.str_schema(), schema]))
    assert validator.validate_json(f'"{input_value}"') == input_value
    assert validator.validate_python(input_value) == input_value


def test_smart_union_default_fallback():
    """Using a default value does not affect the exactness of the smart union match."""

    class ModelA:
        x: int
        y: int = 1

    class ModelB:
        x: int

    schema = core_schema.union_schema(
        [
            core_schema.model_schema(
                ModelA,
                core_schema.model_fields_schema(
                    {
                        'x': core_schema.model_field(core_schema.int_schema()),
                        'y': core_schema.model_field(
                            core_schema.with_default_schema(core_schema.int_schema(), default=1)
                        ),
                    }
                ),
            ),
            core_schema.model_schema(
                ModelB, core_schema.model_fields_schema({'x': core_schema.model_field(core_schema.int_schema())})
            ),
        ]
    )

    validator = SchemaValidator(schema)

    result = validator.validate_python({'x': 1})
    assert isinstance(result, ModelA)
    assert result.x == 1
    assert result.y == 1

    # passing a ModelB explicitly will not match the default value
    b = ModelB()
    assert validator.validate_python(b) is b


def test_smart_union_model_field():
    class ModelA:
        x: int

    class ModelB:
        x: str

    schema = core_schema.union_schema(
        [
            core_schema.model_schema(
                ModelA, core_schema.model_fields_schema({'x': core_schema.model_field(core_schema.int_schema())})
            ),
            core_schema.model_schema(
                ModelB, core_schema.model_fields_schema({'x': core_schema.model_field(core_schema.str_schema())})
            ),
        ]
    )

    validator = SchemaValidator(schema)

    result = validator.validate_python({'x': 1})
    assert isinstance(result, ModelA)
    assert result.x == 1

    result = validator.validate_python({'x': '1'})
    assert isinstance(result, ModelB)
    assert result.x == '1'


def test_smart_union_dataclass_field():
    @dataclass
    class ModelA:
        x: int

    @dataclass
    class ModelB:
        x: str

    schema = core_schema.union_schema(
        [
            core_schema.dataclass_schema(
                ModelA,
                core_schema.dataclass_args_schema(
                    'ModelA', [core_schema.dataclass_field('x', core_schema.int_schema())]
                ),
                ['x'],
            ),
            core_schema.dataclass_schema(
                ModelB,
                core_schema.dataclass_args_schema(
                    'ModelB', [core_schema.dataclass_field('x', core_schema.str_schema())]
                ),
                ['x'],
            ),
        ]
    )

    validator = SchemaValidator(schema)

    result = validator.validate_python({'x': 1})
    assert isinstance(result, ModelA)
    assert result.x == 1

    result = validator.validate_python({'x': '1'})
    assert isinstance(result, ModelB)
    assert result.x == '1'


def test_smart_union_with_any():
    """any is preferred over lax validations"""

    # str not coerced to int
    schema = core_schema.union_schema([core_schema.int_schema(), core_schema.any_schema()])
    validator = SchemaValidator(schema)
    assert validator.validate_python('1') == '1'

    # int *is* coerced to float, this is a strict validation
    schema = core_schema.union_schema([core_schema.float_schema(), core_schema.any_schema()])
    validator = SchemaValidator(schema)
    assert repr(validator.validate_python(1)) == '1.0'


def test_smart_union_validator_function():
    """adding a validator function should not change smart union behaviour"""

    inner_schema = core_schema.union_schema([core_schema.int_schema(), core_schema.float_schema()])

    validator = SchemaValidator(inner_schema)
    assert repr(validator.validate_python(1)) == '1'
    assert repr(validator.validate_python(1.0)) == '1.0'

    schema = core_schema.union_schema(
        [core_schema.no_info_after_validator_function(lambda v: v * 2, inner_schema), core_schema.str_schema()]
    )

    validator = SchemaValidator(schema)
    assert repr(validator.validate_python(1)) == '2'
    assert repr(validator.validate_python(1.0)) == '2.0'
    assert validator.validate_python('1') == '1'

    schema = core_schema.union_schema(
        [
            core_schema.no_info_wrap_validator_function(lambda v, handler: handler(v) * 2, inner_schema),
            core_schema.str_schema(),
        ]
    )

    validator = SchemaValidator(schema)
    assert repr(validator.validate_python(1)) == '2'
    assert repr(validator.validate_python(1.0)) == '2.0'
    assert validator.validate_python('1') == '1'


def test_smart_union_validator_function_one_arm():
    """adding a validator function should not change smart union behaviour"""

    schema = core_schema.union_schema(
        [
            core_schema.float_schema(),
            core_schema.no_info_after_validator_function(lambda v: v * 2, core_schema.int_schema()),
        ]
    )

    validator = SchemaValidator(schema)
    assert repr(validator.validate_python(1)) == '2'
    assert repr(validator.validate_python(1.0)) == '1.0'

    schema = core_schema.union_schema(
        [
            core_schema.float_schema(),
            core_schema.no_info_wrap_validator_function(lambda v, handler: handler(v) * 2, core_schema.int_schema()),
        ]
    )

    validator = SchemaValidator(schema)
    assert repr(validator.validate_python(1)) == '2'
    assert repr(validator.validate_python(1.0)) == '1.0'


def test_int_not_coerced_to_enum():
    class BinaryEnum(IntEnum):
        ZERO = 0
        ONE = 1

    enum_schema = core_schema.lax_or_strict_schema(
        core_schema.no_info_after_validator_function(BinaryEnum, core_schema.int_schema()),
        core_schema.is_instance_schema(BinaryEnum),
    )

    schema = core_schema.union_schema([enum_schema, core_schema.int_schema()])

    validator = SchemaValidator(schema)

    assert validator.validate_python(0) is not BinaryEnum.ZERO
    assert validator.validate_python(1) is not BinaryEnum.ONE
    assert validator.validate_python(BinaryEnum.ZERO) is BinaryEnum.ZERO
    assert validator.validate_python(BinaryEnum.ONE) is BinaryEnum.ONE


def test_model_and_literal_union() -> None:
    # see https://github.com/pydantic/pydantic/issues/8183
    class ModelA:
        pass

    validator = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {
                    'type': 'model',
                    'cls': ModelA,
                    'schema': {
                        'type': 'model-fields',
                        'fields': {
                            'a': {'type': 'model-field', 'schema': {'type': 'int'}},
                        },
                    },
                },
                {'type': 'literal', 'expected': [True]},
            ],
        }
    )

    # validation against Literal[True] fails bc of the unhashable dict
    # A ValidationError is raised, not a ValueError, which allows the validation against the union to continue
    m = validator.validate_python({'a': 42})
    assert isinstance(m, ModelA)
    assert m.a == 42
    assert validator.validate_python(True) is True
