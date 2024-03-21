import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

from ..conftest import plain_repr


def test_chain():
    s = SchemaSerializer(core_schema.chain_schema([core_schema.str_schema(), core_schema.int_schema()]))

    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Int(IntSerializer),definitions=[])'

    assert s.to_python(1) == 1
    assert s.to_json(1) == b'1'


def test_function_plain():
    s = SchemaSerializer(core_schema.with_info_plain_validator_function(lambda v, info: v + 1))
    # can't infer the type from plain function validators
    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Any(AnySerializer),definitions=[])'


def test_function_before():
    s = SchemaSerializer(
        core_schema.with_info_before_validator_function(lambda v, info: v + 1, core_schema.int_schema())
    )
    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Int(IntSerializer),definitions=[])'


def test_function_after():
    s = SchemaSerializer(
        core_schema.with_info_after_validator_function(lambda v, info: v + 1, core_schema.int_schema())
    )
    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Int(IntSerializer),definitions=[])'


def test_lax_or_strict():
    s = SchemaSerializer(core_schema.lax_or_strict_schema(core_schema.int_schema(), core_schema.str_schema()))
    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Str(StrSerializer),definitions=[])'

    assert s.to_json('abc') == b'"abc"'
    with pytest.warns(UserWarning, match='Expected `str` but got `int` - serialized value may not be as expected'):
        assert s.to_json(123) == b'123'


def test_lax_or_strict_custom_ser():
    s = SchemaSerializer(
        core_schema.lax_or_strict_schema(
            core_schema.int_schema(),
            core_schema.str_schema(),
            serialization=core_schema.format_ser_schema('^5s', when_used='always'),
        )
    )

    assert s.to_python('abc') == ' abc '
    assert s.to_python('abc', mode='json') == ' abc '
    assert s.to_json('abc') == b'" abc "'


def test_serialize_with_extra_on_superclass() -> None:
    class Parent:
        x: int

    class Other(Parent):
        y: str

    Parent.__pydantic_core_schema__ = core_schema.model_schema(
        Parent,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
            }
        ),
        config=core_schema.CoreConfig(extra_fields_behavior='allow'),
    )
    Parent.__pydantic_validator__ = SchemaValidator(Parent.__pydantic_core_schema__)
    Parent.__pydantic_serializer__ = SchemaSerializer(Parent.__pydantic_core_schema__)

    Other.__pydantic_core_schema__ = core_schema.model_schema(
        Other,
        core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
                'y': core_schema.model_field(core_schema.str_schema()),
            }
        ),
        config=core_schema.CoreConfig(extra_fields_behavior='forbid'),
    )
    Other.__pydantic_validator__ = SchemaValidator(Other.__pydantic_core_schema__)
    Other.__pydantic_serializer__ = SchemaSerializer(Other.__pydantic_core_schema__)

    other = Other.__pydantic_validator__.validate_python({'x': 1, 'y': 'some string'})
    assert Parent.__pydantic_serializer__.to_python(other) == {'x': 1}
