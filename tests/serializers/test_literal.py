import pytest

from pydantic_core import SchemaError, SchemaSerializer, core_schema

from ..conftest import plain_repr


def test_int_literal():
    s = SchemaSerializer(core_schema.literal_schema(1, 2, 3))
    r = plain_repr(s)
    assert 'expected_int:{' in r
    assert 'expected_str:{}' in r
    assert 'expected_py:None' in r

    assert s.to_python(1) == 1
    assert s.to_python(1, mode='json') == 1
    assert s.to_python(44) == 44
    assert s.to_json(1) == b'1'

    # with pytest.warns(UserWarning, match='Expected `int` but got `str` - serialized value may not be as expected'):
    assert s.to_python('a', mode='json') == 'a'

    # with pytest.warns(UserWarning, match='Expected `int` but got `str` - serialized value may not be as expected'):
    assert s.to_json('a') == b'"a"'


def test_str_literal():
    s = SchemaSerializer(core_schema.literal_schema('a', 'b', 'c'))
    r = plain_repr(s)
    assert 'expected_str:{' in r
    assert 'expected_int:{}' in r
    assert 'expected_py:None' in r

    assert s.to_python('a') == 'a'
    assert s.to_python('a', mode='json') == 'a'
    assert s.to_python('not in literal') == 'not in literal'
    assert s.to_json('a') == b'"a"'

    # with pytest.warns(UserWarning, match='Expected `str` but got `int` - serialized value may not be as expected'):
    assert s.to_python(1, mode='json') == 1

    # with pytest.warns(UserWarning, match='Expected `str` but got `int` - serialized value may not be as expected'):
    assert s.to_json(1) == b'1'


def test_other_literal():
    s = SchemaSerializer(core_schema.literal_schema('a', 1))
    assert 'expected_int:{1},expected_str:{"a"},expected_py:None' in plain_repr(s)

    assert s.to_python('a') == 'a'
    assert s.to_python('a', mode='json') == 'a'
    assert s.to_python('not in literal') == 'not in literal'
    assert s.to_json('a') == b'"a"'

    assert s.to_python(1) == 1
    assert s.to_python(1, mode='json') == 1
    assert s.to_python(44) == 44
    assert s.to_json(1) == b'1'


def test_empty_literal():
    with pytest.raises(SchemaError, match='`expected` should have length > 0'):
        SchemaSerializer(core_schema.literal_schema())
