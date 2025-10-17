import json
from typing import Any

import pytest
from dirty_equals import IsStrictDict
from typing_extensions import TypedDict

from pydantic_core import SchemaSerializer, core_schema


@pytest.mark.parametrize('extra_behavior_kw', [{}, {'extra_behavior': 'ignore'}, {'extra_behavior': None}])
def test_typed_dict(extra_behavior_kw: dict[str, Any]):
    v = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
            },
            **extra_behavior_kw,
        )
    )
    assert v.to_python({'foo': 1, 'bar': b'more'}) == IsStrictDict(foo=1, bar=b'more')
    assert v.to_python({'bar': b'more', 'foo': 1}) == IsStrictDict(bar=b'more', foo=1)
    assert v.to_python({'foo': 1, 'bar': b'more', 'c': 3}) == IsStrictDict(foo=1, bar=b'more')
    assert v.to_python({'bar': b'more', 'foo': 1, 'c': 3}, mode='json') == IsStrictDict(bar='more', foo=1)

    assert v.to_json({'bar': b'more', 'foo': 1, 'c': 3}) == b'{"bar":"more","foo":1}'


def test_typed_dict_fields_has_type():
    typed_dict_field = core_schema.typed_dict_field(core_schema.bytes_schema())

    assert typed_dict_field['type'] == 'typed-dict-field'


def test_typed_dict_allow_extra():
    v = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
            },
            extra_behavior='allow',
        )
    )
    # extra fields go last but retain their order
    assert v.to_python({'bar': b'more', 'b': 3, 'foo': 1, 'a': 4}) == IsStrictDict(bar=b'more', b=3, foo=1, a=4)
    assert v.to_python({'bar': b'more', 'c': 3, 'foo': 1}, mode='json') == IsStrictDict(bar='more', c=3, foo=1)

    assert v.to_json({'bar': b'more', 'c': 3, 'foo': 1, 'cc': 4}) == b'{"bar":"more","c":3,"foo":1,"cc":4}'


@pytest.mark.parametrize(
    'params',
    [
        dict(include=None, exclude=None, expected={'0': 0, '1': 1, '2': 2, '3': 3}),
        dict(include={'0', '1'}, exclude=None, expected={'0': 0, '1': 1}),
        dict(include={'0': ..., '1': ...}, exclude=None, expected={'0': 0, '1': 1}),
        dict(include={'0': {1}, '1': {1}}, exclude=None, expected={'0': 0, '1': 1}),
        dict(include=None, exclude={'0', '1'}, expected={'2': 2, '3': 3}),
        dict(include=None, exclude={'0': ..., '1': ...}, expected={'2': 2, '3': 3}),
        dict(include={'0', '1'}, exclude={'1', '2'}, expected={'0': 0}),
        dict(include=None, exclude={'3': {1}}, expected={'0': 0, '1': 1, '2': 2, '3': 3}),
        dict(include={'0', '1'}, exclude={'3': {1}}, expected={'0': 0, '1': 1}),
        dict(include={'0', '1'}, exclude={'1': {1}}, expected={'0': 0, '1': 1}),
        dict(include={'0', '1'}, exclude={'1': ...}, expected={'0': 0}),
    ],
)
def test_include_exclude_args(params):
    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                '0': core_schema.typed_dict_field(core_schema.int_schema()),
                '1': core_schema.typed_dict_field(core_schema.int_schema()),
                '2': core_schema.typed_dict_field(core_schema.int_schema()),
                '3': core_schema.typed_dict_field(core_schema.int_schema()),
            }
        )
    )

    # user IsStrictDict to check dict order
    include, exclude, expected = params['include'], params['exclude'], IsStrictDict(params['expected'])
    value = {'0': 0, '1': 1, '2': 2, '3': 3}
    assert s.to_python(value, include=include, exclude=exclude) == expected
    assert s.to_python(value, mode='json', include=include, exclude=exclude) == expected
    assert json.loads(s.to_json(value, include=include, exclude=exclude)) == expected


def test_include_exclude_schema():
    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                '0': core_schema.typed_dict_field(core_schema.int_schema(), serialization_exclude=True),
                '1': core_schema.typed_dict_field(core_schema.int_schema()),
                '2': core_schema.typed_dict_field(
                    core_schema.int_schema(), serialization_exclude=True, serialization_exclude_if=lambda x: x < 0
                ),
                '3': core_schema.typed_dict_field(
                    core_schema.int_schema(), serialization_exclude=False, serialization_exclude_if=lambda x: x < 0
                ),
            }
        )
    )
    value = {'0': 0, '1': 1, '2': 2, '3': 3}
    assert s.to_python(value) == {'1': 1, '3': 3}
    assert s.to_python(value, mode='json') == {'1': 1, '3': 3}
    assert json.loads(s.to_json(value)) == {'1': 1, '3': 3}

    value = {'0': 0, '1': 1, '2': 2, '3': -3}
    assert s.to_python(value) == {'1': 1}
    assert s.to_python(value, mode='json') == {'1': 1}
    assert json.loads(s.to_json(value)) == {'1': 1}


def test_alias():
    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'cat': core_schema.typed_dict_field(core_schema.int_schema(), serialization_alias='Meow'),
                'dog': core_schema.typed_dict_field(core_schema.int_schema(), serialization_alias='Woof'),
                'bird': core_schema.typed_dict_field(core_schema.int_schema()),
            }
        )
    )
    value = {'cat': 0, 'dog': 1, 'bird': 2}
    assert s.to_python(value, by_alias=True) == IsStrictDict(Meow=0, Woof=1, bird=2)
    assert s.to_python(value, exclude={'dog'}, by_alias=True) == IsStrictDict(Meow=0, bird=2)
    assert s.to_python(value, by_alias=False) == IsStrictDict(cat=0, dog=1, bird=2)

    assert s.to_python(value, mode='json', by_alias=True) == IsStrictDict(Meow=0, Woof=1, bird=2)
    assert s.to_python(value, mode='json', include={'cat'}, by_alias=True) == IsStrictDict(Meow=0)
    assert s.to_python(value, mode='json', by_alias=False) == IsStrictDict(cat=0, dog=1, bird=2)

    assert json.loads(s.to_json(value, by_alias=True)) == IsStrictDict(Meow=0, Woof=1, bird=2)
    assert json.loads(s.to_json(value, include={'cat', 'bird'}, by_alias=True)) == IsStrictDict(Meow=0, bird=2)
    assert json.loads(s.to_json(value, by_alias=False)) == IsStrictDict(cat=0, dog=1, bird=2)


def test_exclude_none():
    v = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'foo': core_schema.typed_dict_field(core_schema.nullable_schema(core_schema.int_schema())),
                'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
            },
            extra_behavior='allow',
        )
    )
    assert v.to_python({'foo': 1, 'bar': b'more', 'c': 3}) == {'foo': 1, 'bar': b'more', 'c': 3}
    assert v.to_python({'foo': None, 'bar': b'more', 'c': None}) == {'foo': None, 'bar': b'more', 'c': None}
    assert v.to_python({'foo': None, 'bar': b'more', 'c': None}, exclude_none=True) == {'bar': b'more'}

    assert v.to_python({'foo': None, 'bar': b'more', 'c': None}, mode='json') == {'foo': None, 'bar': 'more', 'c': None}
    assert v.to_python({'foo': None, 'bar': b'more', 'c': None}, mode='json', exclude_none=True) == {'bar': 'more'}

    assert v.to_json({'foo': 1, 'bar': b'more', 'c': None}) == b'{"foo":1,"bar":"more","c":null}'
    assert v.to_json({'foo': None, 'bar': b'more'}) == b'{"foo":null,"bar":"more"}'
    assert v.to_json({'foo': None, 'bar': b'more', 'c': None}, exclude_none=True) == b'{"bar":"more"}'


def test_exclude_default():
    v = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'foo': core_schema.typed_dict_field(core_schema.nullable_schema(core_schema.int_schema())),
                'bar': core_schema.typed_dict_field(
                    core_schema.with_default_schema(core_schema.bytes_schema(), default=b'[default]')
                ),
            }
        )
    )
    assert v.to_python({'foo': 1, 'bar': b'x'}) == {'foo': 1, 'bar': b'x'}
    assert v.to_python({'foo': 1, 'bar': b'[default]'}) == {'foo': 1, 'bar': b'[default]'}
    assert v.to_python({'foo': 1, 'bar': b'[default]'}, exclude_defaults=True) == {'foo': 1}
    assert v.to_python({'foo': 1, 'bar': b'[default]'}, mode='json') == {'foo': 1, 'bar': '[default]'}
    assert v.to_python({'foo': 1, 'bar': b'[default]'}, exclude_defaults=True, mode='json') == {'foo': 1}

    assert v.to_json({'foo': 1, 'bar': b'[default]'}) == b'{"foo":1,"bar":"[default]"}'
    assert v.to_json({'foo': 1, 'bar': b'[default]'}, exclude_defaults=True) == b'{"foo":1}'


def test_function_plain_field_serializer_to_python():
    class Model(TypedDict):
        x: int

    def ser_x(data: Model, v: Any, _) -> str:
        assert data['x'] == 1_000
        return f'{v:_}'

    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.int_schema(
                        serialization=core_schema.plain_serializer_function_ser_schema(
                            ser_x, is_field_serializer=True, info_arg=True
                        )
                    )
                )
            }
        )
    )
    assert s.to_python(Model(x=1000)) == {'x': '1_000'}


def test_function_wrap_field_serializer_to_python():
    class Model(TypedDict):
        x: int

    def ser_x(data: Model, v: Any, serializer: core_schema.SerializerFunctionWrapHandler, _) -> str:
        x = serializer(v)
        assert data['x'] == 1_000
        return f'{x:_}'

    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.int_schema(
                        serialization=core_schema.wrap_serializer_function_ser_schema(
                            ser_x, is_field_serializer=True, info_arg=True, schema=core_schema.any_schema()
                        )
                    )
                )
            }
        )
    )
    assert s.to_python(Model(x=1000)) == {'x': '1_000'}


def test_function_plain_field_serializer_to_json():
    class Model(TypedDict):
        x: int

    def ser_x(data: Model, v: Any, info: core_schema.FieldSerializationInfo) -> str:
        assert data['x'] == 1_000
        return f'{v:_}-{info.field_name}'

    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.int_schema(
                        serialization=core_schema.plain_serializer_function_ser_schema(
                            ser_x, is_field_serializer=True, info_arg=True
                        )
                    )
                )
            }
        )
    )
    assert json.loads(s.to_json(Model(x=1000))) == {'x': '1_000-x'}


def test_function_plain_field_serializer_to_json_no_info():
    class Model(TypedDict):
        x: int

    def ser_x(data: Model, v: Any) -> str:
        assert data['x'] == 1_000
        return f'{v:_}'

    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.int_schema(
                        serialization=core_schema.plain_serializer_function_ser_schema(ser_x, is_field_serializer=True)
                    )
                )
            }
        )
    )
    assert json.loads(s.to_json(Model(x=1000))) == {'x': '1_000'}


def test_function_wrap_field_serializer_to_json():
    class Model(TypedDict):
        x: int

    def ser_x(
        data: Model,
        v: Any,
        serializer: core_schema.SerializerFunctionWrapHandler,
        info: core_schema.FieldSerializationInfo,
    ) -> str:
        assert data['x'] == 1_000
        x = serializer(v)
        return f'{x:_}-{info.field_name}'

    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.int_schema(
                        serialization=core_schema.wrap_serializer_function_ser_schema(
                            ser_x, is_field_serializer=True, info_arg=True, schema=core_schema.any_schema()
                        )
                    )
                )
            }
        )
    )
    assert json.loads(s.to_json(Model(x=1000))) == {'x': '1_000-x'}


def test_function_wrap_field_serializer_to_json_no_info():
    class Model(TypedDict):
        x: int

    def ser_x(data: Model, v: Any, serializer: core_schema.SerializerFunctionWrapHandler) -> str:
        assert data['x'] == 1_000
        x = serializer(v)
        return f'{x:_}'

    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.int_schema(
                        serialization=core_schema.wrap_serializer_function_ser_schema(
                            ser_x, is_field_serializer=True, schema=core_schema.any_schema()
                        )
                    )
                )
            }
        )
    )
    assert json.loads(s.to_json(Model(x=1000))) == {'x': '1_000'}


def test_extra_custom_serializer():
    schema = core_schema.typed_dict_schema(
        {},
        extra_behavior='allow',
        extras_schema=core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(lambda v: v + ' bam!')
        ),
    )
    s = SchemaSerializer(schema)

    m = {'extra': 'extra'}

    assert s.to_python(m) == {'extra': 'extra bam!'}


@pytest.mark.parametrize(
    'config,runtime,expected',
    [
        (True, True, {'my_alias': 1}),
        (True, False, {'my_field': 1}),
        (True, None, {'my_alias': 1}),
        (False, True, {'my_alias': 1}),
        (False, False, {'my_field': 1}),
        (False, None, {'my_field': 1}),
        (None, True, {'my_alias': 1}),
        (None, False, {'my_field': 1}),
        (None, None, {'my_field': 1}),
    ],
)
def test_by_alias_and_name_config_interaction(config, runtime, expected) -> None:
    """This test reflects the priority that applies for config vs runtime serialization alias configuration.

    If the runtime value (by_alias) is set, that value is used.
    If the runtime value is unset, the config value (serialize_by_alias) is used.
    If neither are set, the default, False, is used.
    """

    class Model(TypedDict):
        my_field: int

    schema = core_schema.typed_dict_schema(
        {
            'my_field': core_schema.typed_dict_field(core_schema.int_schema(), serialization_alias='my_alias'),
        },
    )
    s = SchemaSerializer(schema, config=core_schema.CoreConfig(serialize_by_alias=config or False))
    assert s.to_python(Model(my_field=1), by_alias=runtime) == expected
