import pytest

from pydantic_core import SchemaSerializer, core_schema

from ..conftest import plain_repr


def test_chain():
    s = SchemaSerializer(core_schema.chain_schema(core_schema.str_schema(), core_schema.int_schema()))

    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Int(IntSerializer),slots=[])'

    assert s.to_python(1) == 1
    assert s.to_json(1) == b'1'


def test_function_plain():
    s = SchemaSerializer(core_schema.function_plain_schema(lambda v, **kwargs: v + 1))
    # can't infer the type from plain function validators
    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Any(AnySerializer),slots=[])'


def test_function_before():
    s = SchemaSerializer(core_schema.function_before_schema(lambda v, **kwargs: v + 1, core_schema.int_schema()))
    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Int(IntSerializer),slots=[])'


def test_function_after():
    s = SchemaSerializer(core_schema.function_after_schema(core_schema.int_schema(), lambda v, **kwargs: v + 1))
    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Int(IntSerializer),slots=[])'


def test_lax_or_strict():
    s = SchemaSerializer(core_schema.lax_or_strict_schema(core_schema.int_schema(), core_schema.str_schema()))
    # insert_assert(plain_repr(s))
    assert plain_repr(s) == 'SchemaSerializer(serializer=Str(StrSerializer),slots=[])'

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
