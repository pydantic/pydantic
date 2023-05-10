import typing

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema


class Foo:
    pass


class Bar(Foo):
    pass


class Spam:
    pass


def test_validate_json() -> None:
    v = SchemaValidator({'type': 'is-instance', 'cls': Foo})
    with pytest.raises(NotImplementedError, match='use a JsonOrPython validator instead'):
        v.validate_json('"foo"')


def test_is_instance():
    v = SchemaValidator({'type': 'is-instance', 'cls': Foo})
    foo = Foo()
    assert v.validate_python(foo) == foo
    assert v.isinstance_python(foo) is True
    bar = Bar()
    assert v.validate_python(bar) == bar
    s = Spam()
    assert v.isinstance_python(s) is False
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(s)

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': (),
            'msg': 'Input should be an instance of Foo',
            'input': s,
            'ctx': {'class': 'Foo'},
        }
    ]
    with pytest.raises(ValidationError, match='type=is_instance_of'):
        v.validate_python(Foo)


@pytest.mark.parametrize(
    'schema_class,input_val,value',
    [
        (Foo, Foo(), True),
        (Foo, Foo, False),
        (Foo, Bar(), True),
        (Foo, Bar, False),
        (Bar, Foo(), False),
        (Bar, Foo, False),
        (dict, {1: 2}, True),
        (dict, {1, 2}, False),
        (type, Foo, True),
        (type, Foo(), False),
    ],
)
def test_is_instance_cases(schema_class, input_val, value):
    v = SchemaValidator({'type': 'is-instance', 'cls': schema_class})
    assert v.isinstance_python(input_val) == value


@pytest.mark.parametrize('input_cls', [123, 'foo', Foo(), [], {1: 2}])
def test_is_instance_invalid(input_cls):
    with pytest.raises(SchemaError, match="SchemaError: 'cls' must be valid as the first argument to 'isinstance'"):
        SchemaValidator({'type': 'is-instance', 'cls': input_cls})


class HasIsInstanceMeta(type):
    def __instancecheck__(self, instance) -> bool:
        if 'error' in repr(instance):
            # an error here comes from a problem in the schema, not in the input value, so raise as internal error
            raise TypeError('intentional error')
        return 'true' in repr(instance)


class HasIsInstance(metaclass=HasIsInstanceMeta):
    pass


def test_instancecheck():
    v = SchemaValidator({'type': 'is-instance', 'cls': HasIsInstance})
    assert v.validate_python('true') == 'true'

    with pytest.raises(ValidationError, match='type=is_instance_of'):
        v.validate_python('other')

    with pytest.raises(TypeError, match='intentional error'):
        v.validate_python('error')


def test_repr():
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'int'}, {'type': 'is-instance', 'cls': Foo}]})
    assert v.isinstance_python(4) is True
    assert v.isinstance_python(Bar()) is True
    assert v.isinstance_python('foo') is False

    with pytest.raises(ValidationError, match=r'is-instance\[Foo\]\s+Input should be an instance of Foo'):
        v.validate_python('foo')


@pytest.mark.parametrize(
    'input_val,value',
    [
        (Foo, True),
        (Foo(), False),
        (str, True),
        ('foo', False),
        (int, True),
        (1, False),
        (type, True),
        (type('Foobar', (), {'x': 1}), True),
    ],
)
def test_is_type(input_val, value):
    v = SchemaValidator({'type': 'is-instance', 'cls': type})
    assert v.isinstance_python(input_val) == value


def test_is_instance_dict():
    v = SchemaValidator(
        core_schema.dict_schema(
            keys_schema=core_schema.is_instance_schema(str), values_schema=core_schema.is_instance_schema(int)
        )
    )
    assert v.isinstance_python({'foo': 1}) is True
    assert v.isinstance_python({1: 1}) is False


def test_is_instance_dict_not_str():
    v = SchemaValidator(core_schema.dict_schema(keys_schema=core_schema.is_instance_schema(int)))
    assert v.isinstance_python({1: 1}) is True
    assert v.isinstance_python({'foo': 1}) is False


def test_is_instance_sequence():
    v = SchemaValidator(core_schema.is_instance_schema(typing.Sequence))
    assert v.isinstance_python(1) is False
    assert v.isinstance_python([1]) is True

    with pytest.raises(ValidationError, match=r'Input should be an instance of typing.Sequence \[type=is_instance_of,'):
        v.validate_python(1)


def test_is_instance_tuple():
    v = SchemaValidator(core_schema.is_instance_schema((int, str)))
    assert v.isinstance_python(1) is True
    assert v.isinstance_python('foobar') is True
    assert v.isinstance_python([1]) is False
    with pytest.raises(ValidationError, match=r"Input should be an instance of \(<class 'int'>, <class 'str'>\)"):
        v.validate_python([1])


def test_class_repr():
    v = SchemaValidator(core_schema.is_instance_schema(int, cls_repr='Foobar'))
    assert v.validate_python(1) == 1
    with pytest.raises(ValidationError, match=r'Input should be an instance of Foobar \[type=is_instance_of,'):
        v.validate_python('1')
