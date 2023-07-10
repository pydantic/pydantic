import pytest
from dirty_equals import IsFloat, IsInt

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

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
        SchemaValidator({'type': 'union'})

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
    assert plain_repr(v) == 'SchemaValidator(title="str",validator=Str(StrValidator{strict:false}),definitions=[])'
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
    assert 'strict_required:true' in plain_repr(v)
    assert 'ultra_strict_required:true' in plain_repr(v)  # since "float" schema has ultra-strict behaviour

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


def test_strict_check():
    v = SchemaValidator(core_schema.union_schema([core_schema.int_schema(), core_schema.json_schema()]))
    assert 'strict_required:true' in plain_repr(v)
    assert 'ultra_strict_required:false' in plain_repr(v)


def test_no_strict_check():
    v = SchemaValidator(core_schema.union_schema([core_schema.is_instance_schema(int), core_schema.json_schema()]))
    assert 'strict_required:false' in plain_repr(v)
    assert 'ultra_strict_required:false' in plain_repr(v)

    assert v.validate_python(123) == 123
    assert v.validate_python('[1, 2, 3]') == [1, 2, 3]


def test_strict_reference():
    v = SchemaValidator(
        core_schema.tuple_positional_schema(
            [
                core_schema.float_schema(),
                core_schema.union_schema(
                    [core_schema.int_schema(), core_schema.definition_reference_schema('tuple-ref')]
                ),
            ],
            ref='tuple-ref',
        )
    )
    assert 'strict_required:true' in plain_repr(v)
    assert 'ultra_strict_required:true' in plain_repr(v)  # since "float" schema has ultra-strict behaviour

    assert repr(v.validate_python((1, 2))) == '(1.0, 2)'
    assert repr(v.validate_python((1.0, (2.0, 3)))) == '(1.0, (2.0, 3))'
