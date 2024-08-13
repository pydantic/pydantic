import dataclasses
import json
import re
import uuid
from decimal import Decimal
from typing import Any, ClassVar, Union

import pytest
from typing_extensions import Literal

from pydantic_core import PydanticSerializationUnexpectedValue, SchemaSerializer, core_schema


class BaseModel:
    def __init__(self, **kwargs) -> None:
        for name, value in kwargs.items():
            setattr(self, name, value)


@pytest.mark.parametrize('bool_case_label', [False, True])
@pytest.mark.parametrize('int_case_label', [False, True])
@pytest.mark.parametrize('input_value,expected_value', [(True, True), (False, False), (1, 1), (123, 123), (-42, -42)])
def test_union_bool_int(input_value, expected_value, bool_case_label, int_case_label):
    bool_case = core_schema.bool_schema() if not bool_case_label else (core_schema.bool_schema(), 'my_bool_label')
    int_case = core_schema.int_schema() if not int_case_label else (core_schema.int_schema(), 'my_int_label')
    s = SchemaSerializer(core_schema.union_schema([bool_case, int_case]))

    assert s.to_python(input_value) == expected_value
    assert s.to_python(input_value, mode='json') == expected_value
    assert s.to_json(input_value) == json.dumps(expected_value).encode()


def test_union_error():
    s = SchemaSerializer(core_schema.union_schema([core_schema.bool_schema(), core_schema.int_schema()]))
    msg = "Expected `Union[bool, int]` but got `str` with value `'a string'` - serialized value may not be as expected"
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert s.to_python('a string') == 'a string'


class ModelA:
    def __init__(self, a, b):
        self.a = a
        self.b = b


class ModelB:
    def __init__(self, c, d):
        self.c = c
        self.d = d


@pytest.fixture(scope='module')
def model_serializer() -> SchemaSerializer:
    return SchemaSerializer(
        {
            'type': 'union',
            'choices': [
                {
                    'type': 'model',
                    'cls': ModelA,
                    'schema': {
                        'type': 'model-fields',
                        'fields': {
                            'a': {'type': 'model-field', 'schema': {'type': 'bytes'}},
                            'b': {
                                'type': 'model-field',
                                'schema': {
                                    'type': 'float',
                                    'serialization': {
                                        'type': 'format',
                                        'formatting_string': '0.1f',
                                        'when_used': 'unless-none',
                                    },
                                },
                            },
                        },
                    },
                },
                {
                    'type': 'model',
                    'cls': ModelB,
                    'schema': {
                        'type': 'model-fields',
                        'fields': {
                            'c': {'type': 'model-field', 'schema': {'type': 'bytes'}},
                            'd': {
                                'type': 'model-field',
                                'schema': {
                                    'type': 'float',
                                    'serialization': {
                                        'type': 'format',
                                        'formatting_string': '0.2f',
                                        'when_used': 'unless-none',
                                    },
                                },
                            },
                        },
                    },
                },
            ],
        }
    )


class SubclassA(ModelA):
    pass


@pytest.mark.parametrize('input_value', [ModelA(b'bite', 2.3456), SubclassA(b'bite', 2.3456)])
def test_model_a(model_serializer: SchemaSerializer, input_value):
    assert model_serializer.to_python(input_value) == {'a': b'bite', 'b': '2.3'}
    assert model_serializer.to_python(input_value, mode='json') == {'a': 'bite', 'b': '2.3'}
    assert model_serializer.to_json(input_value) == b'{"a":"bite","b":"2.3"}'


class SubclassB(ModelB):
    pass


@pytest.mark.parametrize('input_value', [ModelB(b'bite', 2.3456), SubclassB(b'bite', 2.3456)])
def test_model_b(model_serializer: SchemaSerializer, input_value):
    assert model_serializer.to_python(input_value) == {'c': b'bite', 'd': '2.35'}
    assert model_serializer.to_python(input_value, mode='json') == {'c': 'bite', 'd': '2.35'}
    assert model_serializer.to_json(input_value) == b'{"c":"bite","d":"2.35"}'


def test_keys():
    s = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.union_schema(
                [
                    core_schema.int_schema(),
                    core_schema.float_schema(serialization=core_schema.format_ser_schema('0.0f')),
                ]
            ),
            core_schema.int_schema(),
        )
    )
    assert s.to_python({1: 2, 2.111: 3}) == {1: 2, 2.111: 3}
    assert s.to_python({1: 2, 2.111: 3}, mode='json') == {'1': 2, '2': 3}
    assert s.to_json({1: 2, 2.111: 3}) == b'{"1":2,"2":3}'


def test_union_of_functions():
    def repr_function(value, _info):
        if value == 'unexpected':
            raise PydanticSerializationUnexpectedValue()
        return f'func: {value!r}'

    s = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.any_schema(
                    serialization=core_schema.plain_serializer_function_ser_schema(repr_function, info_arg=True)
                ),
                core_schema.float_schema(serialization=core_schema.format_ser_schema('_^14')),
            ]
        )
    )
    assert s.to_python('foobar') == "func: 'foobar'"
    assert s.to_python('foobar', mode='json') == "func: 'foobar'"
    assert s.to_json('foobar') == b'"func: \'foobar\'"'

    assert s.to_python('unexpected') == 'unexpected'
    assert s.to_python('unexpected', mode='json') == '__unexpected__'
    assert s.to_json('unexpected') == b'"__unexpected__"'


def test_typed_dict_literal():
    s = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.typed_dict_schema(
                    dict(
                        pet_type=core_schema.typed_dict_field(core_schema.literal_schema(['cat'])),
                        sound=core_schema.typed_dict_field(
                            core_schema.int_schema(serialization=core_schema.format_ser_schema('04d'))
                        ),
                    )
                ),
                core_schema.typed_dict_schema(
                    dict(
                        pet_type=core_schema.typed_dict_field(core_schema.literal_schema(['dog'])),
                        sound=core_schema.typed_dict_field(
                            core_schema.float_schema(serialization=core_schema.format_ser_schema('0.3f'))
                        ),
                    )
                ),
            ]
        )
    )

    assert s.to_python(dict(pet_type='cat', sound=3), mode='json') == {'pet_type': 'cat', 'sound': '0003'}
    assert s.to_python(dict(pet_type='dog', sound=3), mode='json') == {'pet_type': 'dog', 'sound': '3.000'}


def test_typed_dict_missing():
    s = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.typed_dict_schema(dict(foo=core_schema.typed_dict_field(core_schema.int_schema()))),
                core_schema.typed_dict_schema(
                    dict(
                        foo=core_schema.typed_dict_field(
                            core_schema.int_schema(
                                serialization=core_schema.format_ser_schema('04d', when_used='always')
                            )
                        ),
                        bar=core_schema.typed_dict_field(core_schema.int_schema()),
                    )
                ),
            ]
        )
    )

    assert s.to_python(dict(foo=1)) == {'foo': 1}
    assert s.to_python(dict(foo=1), mode='json') == {'foo': 1}
    assert s.to_json(dict(foo=1)) == b'{"foo":1}'

    assert s.to_python(dict(foo=1, bar=2)) == {'foo': '0001', 'bar': 2}
    assert s.to_python(dict(foo=1, bar=2), mode='json') == {'foo': '0001', 'bar': 2}
    assert s.to_json(dict(foo=1, bar=2)) == b'{"foo":"0001","bar":2}'


def test_typed_dict_extra():
    """
    TODO, needs tests for each case
    """
    s = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.typed_dict_schema(
                    dict(
                        foo=core_schema.typed_dict_field(core_schema.int_schema()),
                        bar=core_schema.typed_dict_field(core_schema.int_schema()),
                    )
                ),
                core_schema.typed_dict_schema(
                    dict(
                        foo=core_schema.typed_dict_field(
                            core_schema.int_schema(serialization=core_schema.format_ser_schema('04d'))
                        )
                    )
                ),
            ]
        )
    )

    assert s.to_python(dict(foo=1, bar=2)) == {'foo': 1, 'bar': 2}
    assert s.to_python(dict(foo=1, bar=2), mode='json') == {'foo': 1, 'bar': 2}
    assert s.to_json(dict(foo=1, bar=2)) == b'{"foo":1,"bar":2}'
    assert s.to_python(dict(foo=1)) == {'foo': 1}
    assert s.to_python(dict(foo=1), mode='json') == {'foo': '0001'}
    assert s.to_json(dict(foo=1)) == b'{"foo":"0001"}'


def test_typed_dict_different_fields():
    """
    TODO, needs tests for each case
    """
    s = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.typed_dict_schema(
                    dict(
                        foo=core_schema.typed_dict_field(core_schema.int_schema()),
                        bar=core_schema.typed_dict_field(core_schema.int_schema()),
                    )
                ),
                core_schema.typed_dict_schema(
                    dict(
                        spam=core_schema.typed_dict_field(core_schema.int_schema()),
                        ham=core_schema.typed_dict_field(
                            core_schema.int_schema(serialization=core_schema.format_ser_schema('04d'))
                        ),
                    )
                ),
            ]
        )
    )

    assert s.to_python(dict(foo=1, bar=2)) == {'foo': 1, 'bar': 2}
    assert s.to_python(dict(foo=1, bar=2), mode='json') == {'foo': 1, 'bar': 2}
    assert s.to_json(dict(foo=1, bar=2)) == b'{"foo":1,"bar":2}'
    assert s.to_python(dict(spam=1, ham=2)) == {'spam': 1, 'ham': 2}
    assert s.to_python(dict(spam=1, ham=2), mode='json') == {'spam': 1, 'ham': '0002'}
    assert s.to_json(dict(spam=1, ham=2)) == b'{"spam":1,"ham":"0002"}'


def test_dataclass_union():
    @dataclasses.dataclass
    class BaseUser:
        name: str

    @dataclasses.dataclass
    class User(BaseUser):
        surname: str

    @dataclasses.dataclass
    class DBUser(User):
        password_hash: str

    @dataclasses.dataclass
    class Item:
        name: str
        price: float

    user_schema = core_schema.dataclass_schema(
        User,
        core_schema.dataclass_args_schema(
            'User',
            [
                core_schema.dataclass_field(name='name', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='surname', schema=core_schema.str_schema()),
            ],
        ),
        ['name', 'surname'],
    )
    item_schema = core_schema.dataclass_schema(
        Item,
        core_schema.dataclass_args_schema(
            'Item',
            [
                core_schema.dataclass_field(name='name', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='price', schema=core_schema.float_schema()),
            ],
        ),
        ['name', 'price'],
    )
    s = SchemaSerializer(core_schema.union_schema([user_schema, item_schema]))
    assert s.to_python(User(name='foo', surname='bar')) == {'name': 'foo', 'surname': 'bar'}
    assert s.to_python(DBUser(name='foo', surname='bar', password_hash='x')) == {'name': 'foo', 'surname': 'bar'}
    assert s.to_json(DBUser(name='foo', surname='bar', password_hash='x')) == b'{"name":"foo","surname":"bar"}'


def test_model_union():
    class BaseUser:
        def __init__(self, name: str):
            self.name = name

    class User(BaseUser):
        def __init__(self, name: str, surname: str):
            super().__init__(name)
            self.surname = surname

    class DBUser(User):
        def __init__(self, name: str, surname: str, password_hash: str):
            super().__init__(name, surname)
            self.password_hash = password_hash

    class Item:
        def __init__(self, name: str, price: float):
            self.name = name
            self.price = price

    user_schema = core_schema.model_schema(
        User,
        core_schema.model_fields_schema(
            {
                'name': core_schema.model_field(schema=core_schema.str_schema()),
                'surname': core_schema.model_field(schema=core_schema.str_schema()),
            }
        ),
    )
    item_schema = core_schema.model_schema(
        Item,
        core_schema.model_fields_schema(
            {
                'name': core_schema.model_field(schema=core_schema.str_schema()),
                'price': core_schema.model_field(schema=core_schema.float_schema()),
            }
        ),
    )
    s = SchemaSerializer(core_schema.union_schema([user_schema, item_schema]))
    assert s.to_python(User(name='foo', surname='bar')) == {'name': 'foo', 'surname': 'bar'}
    assert s.to_python(DBUser(name='foo', surname='bar', password_hash='x')) == {'name': 'foo', 'surname': 'bar'}
    assert s.to_json(DBUser(name='foo', surname='bar', password_hash='x')) == b'{"name":"foo","surname":"bar"}'


@pytest.mark.parametrize(('data', 'json_value'), [(False, 'false'), ('abc', '"abc"')])
def test_union_literal_with_other_type(data, json_value):
    class Model(BaseModel):
        value: Union[Literal[False], str]
        value_types_reversed: Union[str, Literal[False]]

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'value': core_schema.model_field(
                        core_schema.union_schema([core_schema.literal_schema([False]), core_schema.str_schema()])
                    ),
                    'value_types_reversed': core_schema.model_field(
                        core_schema.union_schema([core_schema.str_schema(), core_schema.literal_schema([False])])
                    ),
                }
            ),
        )
    )

    m = Model(value=data, value_types_reversed=data)

    assert s.to_python(m) == {'value': data, 'value_types_reversed': data}
    assert s.to_json(m) == f'{{"value":{json_value},"value_types_reversed":{json_value}}}'.encode()


def test_union_serializes_model_subclass_from_definition() -> None:
    class BaseModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        def __init__(self, **kwargs: Any):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class User(BaseModel):
        name: str

    class DBUser(User):
        password: str
        __pydantic_serializer__: ClassVar[SchemaSerializer]

    DBUser.__pydantic_serializer__ = SchemaSerializer(
        core_schema.model_schema(
            DBUser,
            core_schema.model_fields_schema(
                {
                    'name': core_schema.model_field(core_schema.str_schema()),
                    'password': core_schema.model_field(core_schema.str_schema()),
                }
            ),
        )
    )

    class Item(BaseModel):
        price: float

    s = SchemaSerializer(
        core_schema.definitions_schema(
            core_schema.union_schema(
                [core_schema.definition_reference_schema('User'), core_schema.definition_reference_schema('Item')]
            ),
            [
                core_schema.model_schema(
                    User,
                    core_schema.model_fields_schema({'name': core_schema.model_field(core_schema.str_schema())}),
                    ref='User',
                ),
                core_schema.model_schema(
                    Item,
                    core_schema.model_fields_schema({'price': core_schema.model_field(core_schema.float_schema())}),
                    ref='Item',
                ),
            ],
        )
    )

    assert s.to_python(DBUser(name='John', password='secret')) == {'name': 'John'}


def test_union_serializes_list_of_model_subclass_from_definition() -> None:
    class BaseModel:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        def __init__(self, **kwargs: Any):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class User(BaseModel):
        name: str

    class DBUser(User):
        password: str
        __pydantic_serializer__: ClassVar[SchemaSerializer]

    DBUser.__pydantic_serializer__ = SchemaSerializer(
        core_schema.model_schema(
            DBUser,
            core_schema.model_fields_schema(
                {
                    'name': core_schema.model_field(core_schema.str_schema()),
                    'password': core_schema.model_field(core_schema.str_schema()),
                }
            ),
        )
    )

    class Item(BaseModel):
        price: float

    s = SchemaSerializer(
        core_schema.definitions_schema(
            core_schema.union_schema(
                [
                    core_schema.list_schema(core_schema.definition_reference_schema('User'), strict=False),
                    core_schema.list_schema(core_schema.definition_reference_schema('Item'), strict=False),
                ]
            ),
            [
                core_schema.model_schema(
                    User,
                    core_schema.model_fields_schema({'name': core_schema.model_field(core_schema.str_schema())}),
                    ref='User',
                ),
                core_schema.model_schema(
                    Item,
                    core_schema.model_fields_schema({'price': core_schema.model_field(core_schema.float_schema())}),
                    ref='Item',
                ),
            ],
        )
    )

    assert s.to_python([DBUser(name='John', password='secret')]) == [{'name': 'John'}]


EXAMPLE_UUID = uuid.uuid4()


class IntSubclass(int):
    pass


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize(
    'core_schema_left,core_schema_right,input_value,expected_value',
    [
        (core_schema.int_schema(), core_schema.bool_schema(), True, True),
        (core_schema.int_schema(), core_schema.bool_schema(), 1, 1),
        (core_schema.str_schema(), core_schema.int_schema(), 1, 1),
        (core_schema.str_schema(), core_schema.int_schema(), '1', '1'),
        (core_schema.int_schema(), core_schema.bool_schema(), IntSubclass(1), 1),
        (
            core_schema.decimal_schema(),
            core_schema.int_schema(),
            Decimal('1'),
            Decimal('1'),
        ),
        (core_schema.decimal_schema(), core_schema.int_schema(), 1, 1),
        (
            core_schema.decimal_schema(),
            core_schema.float_schema(),
            Decimal('1.'),
            Decimal('1.'),
        ),
        (
            core_schema.decimal_schema(),
            core_schema.str_schema(),
            Decimal('_1'),
            Decimal('_1'),
        ),
        (
            core_schema.decimal_schema(),
            core_schema.str_schema(),
            '_1',
            '_1',
        ),
        (
            core_schema.uuid_schema(),
            core_schema.str_schema(),
            EXAMPLE_UUID,
            EXAMPLE_UUID,
        ),
        (
            core_schema.uuid_schema(),
            core_schema.str_schema(),
            str(EXAMPLE_UUID),
            str(EXAMPLE_UUID),
        ),
    ],
)
def test_union_serializer_picks_exact_type_over_subclass(
    core_schema_left, core_schema_right, input_value, expected_value, reverse
):
    s = SchemaSerializer(
        core_schema.union_schema(
            [core_schema_right, core_schema_left] if reverse else [core_schema_left, core_schema_right]
        )
    )
    assert s.to_python(input_value) == expected_value


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize(
    'core_schema_left,core_schema_right,input_value,expected_value',
    [
        (core_schema.int_schema(), core_schema.bool_schema(), True, True),
        (core_schema.int_schema(), core_schema.bool_schema(), 1, 1),
        (core_schema.str_schema(), core_schema.int_schema(), 1, 1),
        (core_schema.str_schema(), core_schema.int_schema(), '1', '1'),
        (core_schema.int_schema(), core_schema.bool_schema(), IntSubclass(1), 1),
        (
            core_schema.decimal_schema(),
            core_schema.int_schema(),
            Decimal('1'),
            '1',
        ),
        (core_schema.decimal_schema(), core_schema.int_schema(), 1, 1),
        (
            core_schema.decimal_schema(),
            core_schema.float_schema(),
            Decimal('1.'),
            '1',
        ),
        (
            core_schema.decimal_schema(),
            core_schema.str_schema(),
            Decimal('_1'),
            '1',
        ),
        (
            core_schema.decimal_schema(),
            core_schema.str_schema(),
            '_1',
            '_1',
        ),
    ],
)
def test_union_serializer_picks_exact_type_over_subclass_json(
    core_schema_left, core_schema_right, input_value, expected_value, reverse
):
    s = SchemaSerializer(
        core_schema.union_schema(
            [core_schema_right, core_schema_left] if reverse else [core_schema_left, core_schema_right]
        )
    )
    assert s.to_python(input_value, mode='json') == expected_value
    assert s.to_json(input_value) == json.dumps(expected_value).encode()


def test_union_float_int() -> None:
    s = SchemaSerializer(core_schema.union_schema([core_schema.float_schema(), core_schema.int_schema()]))

    assert s.to_python(1) == 1
    assert json.loads(s.to_json(1)) == 1

    s = SchemaSerializer(core_schema.union_schema([core_schema.int_schema(), core_schema.float_schema()]))

    assert s.to_python(1) == 1
    assert json.loads(s.to_json(1)) == 1


def test_custom_serializer() -> None:
    s = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.dict_schema(
                    keys_schema=core_schema.any_schema(),
                    values_schema=core_schema.any_schema(),
                    serialization=core_schema.plain_serializer_function_ser_schema(lambda x: x['id']),
                ),
                core_schema.list_schema(
                    items_schema=core_schema.dict_schema(
                        keys_schema=core_schema.any_schema(),
                        values_schema=core_schema.any_schema(),
                        serialization=core_schema.plain_serializer_function_ser_schema(lambda x: x['id']),
                    )
                ),
            ]
        )
    )
    print(s)
    assert s.to_python([{'id': 1}, {'id': 2}]) == [1, 2]
    assert s.to_python({'id': 1}) == 1
