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
                core_schema.dataclass_field(
                    name='a', schema=core_schema.str_schema(), serialization_exclude_if=lambda x: x == 'bye'
                ),
                core_schema.dataclass_field(name='b', schema=core_schema.bytes_schema(), serialization_exclude=True),
            ],
        ),
        ['a', 'b'],
    )
    s = SchemaSerializer(schema)
    assert s.to_python(Foo(a='hello', b=b'more')) == {'a': 'hello'}
    assert s.to_python(Foo(a='hello', b=b'more'), mode='json') == {'a': 'hello'}
    # a = 'bye' excludes it
    assert s.to_python(Foo(a='bye', b=b'more'), mode='json') == {}
    j = s.to_json(Foo(a='hello', b=b'more'))
    if on_pypy:
        assert json.loads(j) == {'a': 'hello'}
    else:
        assert j == b'{"a":"hello"}'
    j = s.to_json(Foo(a='bye', b=b'more'))
    if on_pypy:
        assert json.loads(j) == {}
    else:
        assert j == b'{}'


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
    assert s.to_python(Foo(a='hello', b=b'more'), by_alias=True) == IsStrictDict(a='hello', BAR=b'more')
    assert s.to_python(Foo(a='hello', b=b'more'), mode='json', by_alias=True) == IsStrictDict(a='hello', BAR='more')
    j = s.to_json(Foo(a='hello', b=b'more'), by_alias=True)

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


def test_dataclass_initvar_not_required_on_union_ser() -> None:
    @dataclasses.dataclass
    class Foo:
        x: int
        init_var: dataclasses.InitVar[int] = 1

    @dataclasses.dataclass
    class Bar:
        x: int

    schema = core_schema.union_schema(
        [
            core_schema.dataclass_schema(
                Foo,
                core_schema.dataclass_args_schema(
                    'Foo',
                    [
                        core_schema.dataclass_field(name='x', schema=core_schema.int_schema()),
                        core_schema.dataclass_field(
                            name='init_var',
                            init_only=True,
                            schema=core_schema.with_default_schema(core_schema.int_schema(), default=1),
                        ),
                    ],
                ),
                ['x'],
                post_init=True,
            ),
            core_schema.dataclass_schema(
                Bar,
                core_schema.dataclass_args_schema(
                    'Bar', [core_schema.dataclass_field(name='x', schema=core_schema.int_schema())]
                ),
                ['x'],
            ),
        ]
    )

    s = SchemaSerializer(schema)
    assert s.to_python(Foo(x=1), warnings='error') == {'x': 1}
    assert s.to_python(Foo(x=1, init_var=2), warnings='error') == {'x': 1}


@pytest.mark.parametrize(
    'config,runtime,expected',
    [
        (True, True, {'my_alias': 'hello'}),
        (True, False, {'my_field': 'hello'}),
        (True, None, {'my_alias': 'hello'}),
        (False, True, {'my_alias': 'hello'}),
        (False, False, {'my_field': 'hello'}),
        (False, None, {'my_field': 'hello'}),
        (None, True, {'my_alias': 'hello'}),
        (None, False, {'my_field': 'hello'}),
        (None, None, {'my_field': 'hello'}),
    ],
)
def test_by_alias_and_name_config_interaction(config, runtime, expected) -> None:
    """This test reflects the priority that applies for config vs runtime serialization alias configuration.

    If the runtime value (by_alias) is set, that value is used.
    If the runtime value is unset, the config value (serialize_by_alias) is used.
    If neither are set, the default, False, is used.
    """

    @dataclasses.dataclass
    class Foo:
        my_field: str

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(
                    name='my_field', schema=core_schema.str_schema(), serialization_alias='my_alias'
                ),
            ],
        ),
        ['my_field'],
        config=core_schema.CoreConfig(serialize_by_alias=config or False),
    )
    s = SchemaSerializer(schema)
    assert s.to_python(Foo(my_field='hello'), by_alias=runtime) == expected
