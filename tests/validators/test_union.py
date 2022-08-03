import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError


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
                        'type': 'new-class',
                        'class_type': self.ModelA,
                        'schema': {
                            'type': 'typed-dict',
                            'return_fields_set': True,
                            'fields': {'a': {'schema': {'type': 'int'}}, 'b': {'schema': {'type': 'str'}}},
                        },
                    },
                    {
                        'type': 'new-class',
                        'class_type': self.ModelB,
                        'schema': {
                            'type': 'typed-dict',
                            'return_fields_set': True,
                            'fields': {'c': {'schema': {'type': 'int'}}, 'd': {'schema': {'type': 'str'}}},
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
        assert exc_info.value.errors() == [
            {'kind': 'missing', 'loc': ['ModelA', 'b'], 'message': 'Field required', 'input_value': {'a': 2}},
            {'kind': 'missing', 'loc': ['ModelB', 'c'], 'message': 'Field required', 'input_value': {'a': 2}},
            {'kind': 'missing', 'loc': ['ModelB', 'd'], 'message': 'Field required', 'input_value': {'a': 2}},
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
                        'type': 'new-class',
                        'class_type': self.ModelA,
                        'schema': {
                            'type': 'typed-dict',
                            'return_fields_set': True,
                            'fields': {'a': {'schema': {'type': 'int'}}, 'b': {'schema': {'type': 'str'}}},
                        },
                    },
                    {
                        'type': 'new-class',
                        'class_type': self.ModelB,
                        'schema': {
                            'type': 'typed-dict',
                            'return_fields_set': True,
                            'fields': {
                                'a': {'schema': {'type': 'int'}},
                                'b': {'schema': {'type': 'str'}},
                                'c': {'schema': {'type': 'float'}, 'default': 1.0},
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
    assert exc_info.value.errors() == [
        {'kind': 'none_required', 'loc': ['none'], 'message': 'Input should be None/null', 'input_value': 'hello'},
        {
            'kind': 'int_parsing',
            'loc': ['int'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'hello',
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
    assert exc_info.value.errors() == [
        {
            'kind': 'bool_parsing',
            'loc': ['list[bool]', 0],
            'message': 'Input should be a valid boolean, unable to interpret input',
            'input_value': 3,
        },
        {
            'kind': 'int_parsing',
            'loc': ['list[int]', 1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'true',
        },
    ]


def test_no_choices():
    with pytest.raises(SchemaError) as exc_info:
        SchemaValidator({'type': 'union'})

    assert exc_info.value.args[0] == (
        'Invalid Schema:\n'
        'union -> choices\n'
        "  Field required [kind=missing, input_value={'type': 'union'}, input_type=dict]"
    )


def test_strict_union():
    v = SchemaValidator({'type': 'union', 'strict': True, 'choices': [{'type': 'bool'}, {'type': 'int'}]})
    assert v.validate_python(1) == 1
    assert v.validate_python(123) == 123

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('123')

    assert exc_info.value.errors() == [
        {'kind': 'bool_type', 'loc': ['bool'], 'message': 'Input should be a valid boolean', 'input_value': '123'},
        {'kind': 'int_type', 'loc': ['int'], 'message': 'Input should be a valid integer', 'input_value': '123'},
    ]
