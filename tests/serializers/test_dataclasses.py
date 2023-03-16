import dataclasses
import json
import platform

from pydantic_core import SchemaSerializer, core_schema

on_pypy = platform.python_implementation() == 'PyPy'
# pypy doesn't seem to maintain order of `__dict__`
if on_pypy:
    IsStrictDict = dict
else:
    from dirty_equals import IsStrictDict


@dataclasses.dataclass
class Foo:
    a: str
    b: bytes


def test_dataclass():
    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bytes_schema()),
            ],
        ),
    )
    s = SchemaSerializer(schema)
    assert s.to_python(Foo(a='hello', b=b'more')) == IsStrictDict(a='hello', b=b'more')
    assert s.to_python(Foo(a='hello', b=b'more'), mode='json') == IsStrictDict(a='hello', b='more')
    j = s.to_json(Foo(a='hello', b=b'more'))

    if on_pypy:
        assert json.loads(j) == {'a': 'hello', 'b': 'more'}
    else:
        assert j == b'{"a":"hello","b":"more"}'

    assert s.to_python(Foo(a='hello', b=b'more'), exclude={'b'}) == IsStrictDict(a='hello')
    assert s.to_json(Foo(a='hello', b=b'more'), include={'a'}) == b'{"a":"hello"}'


def test_serialization_exclude():
    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bytes_schema(), serialization_exclude=True),
            ],
        ),
    )
    s = SchemaSerializer(schema)
    assert s.to_python(Foo(a='hello', b=b'more')) == {'a': 'hello'}
    assert s.to_python(Foo(a='hello', b=b'more'), mode='json') == {'a': 'hello'}
    j = s.to_json(Foo(a='hello', b=b'more'))

    if on_pypy:
        assert json.loads(j) == {'a': 'hello'}
    else:
        assert j == b'{"a":"hello"}'


def test_serialization_alias():
    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bytes_schema(), serialization_alias='BAR'),
            ],
        ),
    )
    s = SchemaSerializer(schema)
    assert s.to_python(Foo(a='hello', b=b'more')) == IsStrictDict(a='hello', BAR=b'more')
    assert s.to_python(Foo(a='hello', b=b'more'), mode='json') == IsStrictDict(a='hello', BAR='more')
    j = s.to_json(Foo(a='hello', b=b'more'))

    if on_pypy:
        assert json.loads(j) == {'a': 'hello', 'BAR': 'more'}
    else:
        assert j == b'{"a":"hello","BAR":"more"}'
