import dataclasses
import json
import platform
import sys
from typing import ClassVar

import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

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
        ['a', 'b'],
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
        ['a', 'b'],
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
        ['a', 'b'],
    )
    s = SchemaSerializer(schema)
    assert s.to_python(Foo(a='hello', b=b'more')) == IsStrictDict(a='hello', BAR=b'more')
    assert s.to_python(Foo(a='hello', b=b'more'), mode='json') == IsStrictDict(a='hello', BAR='more')
    j = s.to_json(Foo(a='hello', b=b'more'))

    if on_pypy:
        assert json.loads(j) == {'a': 'hello', 'BAR': 'more'}
    else:
        assert j == b'{"a":"hello","BAR":"more"}'


def test_properties():
    @dataclasses.dataclass
    class FooProp:
        a: str
        b: bytes

        @property
        def c(self) -> str:
            return f'{self.a} {self.b.decode()}'

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'FooProp',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bytes_schema()),
            ],
            computed_fields=[core_schema.computed_field('c', core_schema.str_schema())],
        ),
        ['a', 'b'],
    )
    s = SchemaSerializer(schema)
    assert s.to_python(FooProp(a='hello', b=b'more')) == IsStrictDict(a='hello', b=b'more', c='hello more')
    assert s.to_python(FooProp(a='hello', b=b'more'), mode='json') == IsStrictDict(a='hello', b='more', c='hello more')
    j = s.to_json(FooProp(a='hello', b=b'more'))

    if on_pypy:
        assert json.loads(j) == {'a': 'hello', 'b': 'more', 'c': 'hello more'}
    else:
        assert j == b'{"a":"hello","b":"more","c":"hello more"}'

    assert s.to_python(FooProp(a='hello', b=b'more'), exclude={'b'}) == IsStrictDict(a='hello', c='hello more')
    assert s.to_json(FooProp(a='hello', b=b'more'), include={'a'}) == b'{"a":"hello"}'


@pytest.mark.skipif(sys.version_info < (3, 10), reason='slots are only supported for dataclasses in Python > 3.10')
def test_slots_mixed():
    @dataclasses.dataclass(slots=True)
    class Model:
        x: int
        y: dataclasses.InitVar[str]
        z: ClassVar[str] = 'z-classvar'

    @dataclasses.dataclass
    class SubModel(Model):
        x2: int
        y2: dataclasses.InitVar[str]
        z2: ClassVar[str] = 'z2-classvar'

    schema = core_schema.dataclass_schema(
        SubModel,
        core_schema.dataclass_args_schema(
            'SubModel',
            [
                core_schema.dataclass_field(name='x', schema=core_schema.int_schema()),
                core_schema.dataclass_field(name='y', init_only=True, schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='x2', schema=core_schema.int_schema()),
                core_schema.dataclass_field(name='y2', init_only=True, schema=core_schema.str_schema()),
            ],
        ),
        ['x', 'x2'],
        slots=True,
    )
    dc = SubModel(x=1, y='a', x2=2, y2='b')
    assert dataclasses.asdict(dc) == {'x': 1, 'x2': 2}

    s = SchemaSerializer(schema)
    assert s.to_python(dc) == {'x': 1, 'x2': 2}
    assert s.to_json(dc) == b'{"x":1,"x2":2}'


@pytest.mark.xfail(reason='dataclasses do not serialize extras')
def test_extra_custom_serializer():
    @dataclasses.dataclass
    class Model:
        pass

    schema = core_schema.dataclass_schema(
        Model,
        core_schema.dataclass_args_schema(
            'Model',
            [],
            extra_behavior='allow',
            # extras_schema=core_schema.any_schema(
            #     serialization=core_schema.plain_serializer_function_ser_schema(
            #         lambda v: v + ' bam!',
            #     )
            # )
        ),
        [],
    )
    s = SchemaSerializer(schema)
    v = SchemaValidator(schema)

    m = v.validate_python({'extra': 'extra'})

    assert s.to_python(m) == {'extra': 'extra bam!'}
