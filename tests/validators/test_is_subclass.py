import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema


class Foo:
    pass


class Foobar(Foo):
    pass


class Bar:
    pass


def test_is_subclass_basic():
    v = SchemaValidator(core_schema.is_subclass_schema(Foo))
    assert v.validate_python(Foo) == Foo
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(Bar)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'is_subclass_of',
            'loc': (),
            'msg': 'Input should be a subclass of Foo',
            'input': Bar,
            'ctx': {'class': 'Foo'},
        }
    ]


@pytest.mark.parametrize(
    'input_value,valid',
    [
        (Foo, True),
        (Foobar, True),
        (Bar, False),
        (type, False),
        (1, False),
        ('foo', False),
        (Foo(), False),
        (Foobar(), False),
        (Bar(), False),
    ],
)
def test_is_subclass(input_value, valid):
    v = SchemaValidator(core_schema.is_subclass_schema(Foo))
    assert v.isinstance_python(input_value) == valid


def test_not_parent():
    v = SchemaValidator(core_schema.is_subclass_schema(Foobar))
    assert v.isinstance_python(Foobar)
    assert not v.isinstance_python(Foo)


def test_invalid_type():
    with pytest.raises(SchemaError, match="TypeError: 'Foo' object cannot be converted to 'PyType"):
        SchemaValidator(core_schema.is_subclass_schema(Foo()))


def test_custom_repr():
    v = SchemaValidator(core_schema.is_subclass_schema(Foo, cls_repr='Spam'))
    assert v.validate_python(Foo) == Foo
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(Bar)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'is_subclass_of',
            'loc': (),
            'msg': 'Input should be a subclass of Spam',
            'input': Bar,
            'ctx': {'class': 'Spam'},
        }
    ]
