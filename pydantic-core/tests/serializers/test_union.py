from __future__ import annotations

import dataclasses
import json
import uuid
import warnings
from decimal import Decimal
from typing import Any, ClassVar, Literal, Union

import pytest

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

    messages = [
        "Expected `bool` - serialized value may not be as expected [input_value='a string', input_type=str]",
        "Expected `int` - serialized value may not be as expected [input_value='a string', input_type=str]",
    ]

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        s.to_python('a string')
        for m in messages:
            assert m in str(w[0].message)


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
        core_schema.union_schema(
            [
                core_schema.model_schema(
                    ModelA,
                    core_schema.model_fields_schema(
                        {
                            'a': core_schema.model_field(core_schema.bytes_schema()),
                            'b': core_schema.model_field(
                                core_schema.float_schema(
                                    serialization=core_schema.format_ser_schema('0.1f', when_used='unless-none')
                                )
                            ),
                        }
                    ),
                ),
                core_schema.model_schema(
                    ModelB,
                    core_schema.model_fields_schema(
                        {
                            'c': core_schema.model_field(core_schema.bytes_schema()),
                            'd': core_schema.model_field(
                                core_schema.float_schema(
                                    serialization=core_schema.format_ser_schema('0.2f', when_used='unless-none')
                                )
                            ),
                        }
                    ),
                ),
            ],
        )
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


def test_tagged_union() -> None:
    @dataclasses.dataclass
    class ModelA:
        field: int
        tag: Literal['a'] = 'a'

    @dataclasses.dataclass
    class ModelB:
        field: int
        tag: Literal['b'] = 'b'

    s = SchemaSerializer(
        core_schema.tagged_union_schema(
            choices={
                'a': core_schema.dataclass_schema(
                    ModelA,
                    core_schema.dataclass_args_schema(
                        'ModelA',
                        [
                            core_schema.dataclass_field(name='field', schema=core_schema.int_schema()),
                            core_schema.dataclass_field(name='tag', schema=core_schema.literal_schema(['a'])),
                        ],
                    ),
                    ['field', 'tag'],
                ),
                'b': core_schema.dataclass_schema(
                    ModelB,
                    core_schema.dataclass_args_schema(
                        'ModelB',
                        [
                            core_schema.dataclass_field(name='field', schema=core_schema.int_schema()),
                            core_schema.dataclass_field(name='tag', schema=core_schema.literal_schema(['b'])),
                        ],
                    ),
                    ['field', 'tag'],
                ),
            },
            discriminator='tag',
        )
    )

    assert 'TaggedUnionSerializer' in repr(s)

    model_a = ModelA(field=1)
    model_b = ModelB(field=1)
    assert s.to_python(model_a) == {'field': 1, 'tag': 'a'}
    assert s.to_python(model_b) == {'field': 1, 'tag': 'b'}


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


def test_tagged_union_with_aliases() -> None:
    @dataclasses.dataclass
    class ModelA:
        field: int
        tag: Literal['a'] = 'a'

    @dataclasses.dataclass
    class ModelB:
        field: int
        tag: Literal['b'] = 'b'

    s = SchemaSerializer(
        core_schema.tagged_union_schema(
            choices={
                'a': core_schema.dataclass_schema(
                    ModelA,
                    core_schema.dataclass_args_schema(
                        'ModelA',
                        [
                            core_schema.dataclass_field(name='field', schema=core_schema.int_schema()),
                            core_schema.dataclass_field(
                                name='tag',
                                schema=core_schema.literal_schema(['a']),
                                validation_alias='TAG',
                                serialization_alias='TAG',
                            ),
                        ],
                    ),
                    ['field', 'tag'],
                ),
                'b': core_schema.dataclass_schema(
                    ModelB,
                    core_schema.dataclass_args_schema(
                        'ModelB',
                        [
                            core_schema.dataclass_field(name='field', schema=core_schema.int_schema()),
                            core_schema.dataclass_field(
                                name='tag',
                                schema=core_schema.literal_schema(['b']),
                                validation_alias='TAG',
                                serialization_alias='TAG',
                            ),
                        ],
                    ),
                    ['field', 'tag'],
                ),
            },
            discriminator=[['tag'], ['TAG']],
        )
    )

    assert 'TaggedUnionSerializer' in repr(s)

    model_a = ModelA(field=1)
    model_b = ModelB(field=1)
    assert s.to_python(model_a, by_alias=True) == {'field': 1, 'TAG': 'a'}
    assert s.to_python(model_b, by_alias=True) == {'field': 1, 'TAG': 'b'}


def test_union_model_wrap_serializer():
    def wrap_serializer(value, handler):
        return handler(value)

    class Data:
        pass

    class ModelA:
        a: Data

    class ModelB:
        a: Data

    model_serializer = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.model_schema(
                    ModelA,
                    core_schema.model_fields_schema(
                        {
                            'a': core_schema.model_field(
                                core_schema.model_schema(
                                    Data,
                                    core_schema.model_fields_schema({}),
                                )
                            ),
                        },
                    ),
                    serialization=core_schema.wrap_serializer_function_ser_schema(wrap_serializer),
                ),
                core_schema.model_schema(
                    ModelB,
                    core_schema.model_fields_schema(
                        {
                            'a': core_schema.model_field(
                                core_schema.model_schema(
                                    Data,
                                    core_schema.model_fields_schema({}),
                                )
                            ),
                        },
                    ),
                    serialization=core_schema.wrap_serializer_function_ser_schema(wrap_serializer),
                ),
            ],
        )
    )

    input_value = ModelA()
    input_value.a = Data()

    assert model_serializer.to_python(input_value) == {'a': {}}
    assert model_serializer.to_python(input_value, mode='json') == {'a': {}}
    assert model_serializer.to_json(input_value) == b'{"a":{}}'

    # add some additional attribute, should be ignored & not break serialization

    input_value.a._a = 'foo'

    assert model_serializer.to_python(input_value) == {'a': {}}
    assert model_serializer.to_python(input_value, mode='json') == {'a': {}}
    assert model_serializer.to_json(input_value) == b'{"a":{}}'


class ModelDog:
    def __init__(self, type_: Literal['dog']) -> None:
        self.type_ = 'dog'


class ModelCat:
    def __init__(self, type_: Literal['cat']) -> None:
        self.type_ = 'cat'


class ModelAlien:
    def __init__(self, type_: Literal['alien']) -> None:
        self.type_ = 'alien'


@pytest.fixture
def model_a_b_union_schema() -> core_schema.UnionSchema:
    return core_schema.union_schema(
        [
            core_schema.model_schema(
                cls=ModelA,
                schema=core_schema.model_fields_schema(
                    fields={
                        'a': core_schema.model_field(core_schema.str_schema()),
                        'b': core_schema.model_field(core_schema.str_schema()),
                    },
                ),
            ),
            core_schema.model_schema(
                cls=ModelB,
                schema=core_schema.model_fields_schema(
                    fields={
                        'c': core_schema.model_field(core_schema.str_schema()),
                        'd': core_schema.model_field(core_schema.str_schema()),
                    },
                ),
            ),
        ]
    )


@pytest.fixture
def union_of_unions_schema(model_a_b_union_schema: core_schema.UnionSchema) -> core_schema.UnionSchema:
    return core_schema.union_schema(
        [
            model_a_b_union_schema,
            core_schema.union_schema(
                [
                    core_schema.model_schema(
                        cls=ModelCat,
                        schema=core_schema.model_fields_schema(
                            fields={
                                'type_': core_schema.model_field(core_schema.literal_schema(['cat'])),
                            },
                        ),
                    ),
                    core_schema.model_schema(
                        cls=ModelDog,
                        schema=core_schema.model_fields_schema(
                            fields={
                                'type_': core_schema.model_field(core_schema.literal_schema(['dog'])),
                            },
                        ),
                    ),
                ]
            ),
        ]
    )


@pytest.mark.parametrize(
    'input,expected',
    [
        (ModelA(a='a', b='b'), {'a': 'a', 'b': 'b'}),
        (ModelB(c='c', d='d'), {'c': 'c', 'd': 'd'}),
        (ModelCat(type_='cat'), {'type_': 'cat'}),
        (ModelDog(type_='dog'), {'type_': 'dog'}),
    ],
)
def test_union_of_unions_of_models(union_of_unions_schema: core_schema.UnionSchema, input: Any, expected: Any) -> None:
    s = SchemaSerializer(union_of_unions_schema)
    assert s.to_python(input, warnings='error') == expected


def test_union_of_unions_of_models_invalid_variant(union_of_unions_schema: core_schema.UnionSchema) -> None:
    s = SchemaSerializer(union_of_unions_schema)
    # All warnings should be available
    messages = [
        'Expected `ModelA`',
        'Expected `ModelB`',
        'Expected `ModelCat`',
        'Expected `ModelDog`',
    ]

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        s.to_python(ModelAlien(type_='alien'))
        for m in messages:
            assert m in str(w[0].message)
            assert 'input_type=ModelAlien' in str(w[0].message)


@pytest.fixture
def tagged_union_of_unions_schema(model_a_b_union_schema: core_schema.UnionSchema) -> core_schema.UnionSchema:
    return core_schema.union_schema(
        [
            model_a_b_union_schema,
            core_schema.tagged_union_schema(
                discriminator='type_',
                choices={
                    'cat': core_schema.model_schema(
                        cls=ModelCat,
                        schema=core_schema.model_fields_schema(
                            fields={
                                'type_': core_schema.model_field(core_schema.literal_schema(['cat'])),
                            },
                        ),
                    ),
                    'dog': core_schema.model_schema(
                        cls=ModelDog,
                        schema=core_schema.model_fields_schema(
                            fields={
                                'type_': core_schema.model_field(core_schema.literal_schema(['dog'])),
                            },
                        ),
                    ),
                },
            ),
        ]
    )


@pytest.mark.parametrize(
    'input,expected',
    [
        (ModelA(a='a', b='b'), {'a': 'a', 'b': 'b'}),
        (ModelB(c='c', d='d'), {'c': 'c', 'd': 'd'}),
        (ModelCat(type_='cat'), {'type_': 'cat'}),
        (ModelDog(type_='dog'), {'type_': 'dog'}),
    ],
)
def test_union_of_unions_of_models_with_tagged_union(
    tagged_union_of_unions_schema: core_schema.UnionSchema, input: Any, expected: Any
) -> None:
    s = SchemaSerializer(tagged_union_of_unions_schema)
    assert s.to_python(input, warnings='error') == expected


def test_union_of_unions_of_models_with_tagged_union_invalid_variant(
    tagged_union_of_unions_schema: core_schema.UnionSchema,
) -> None:
    s = SchemaSerializer(tagged_union_of_unions_schema)
    # All warnings should be available
    messages = [
        'Expected `ModelA`',
        'Expected `ModelB`',
        'Expected `ModelCat`',
        'Expected `ModelDog`',
    ]

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        s.to_python(ModelAlien(type_='alien'))
        for m in messages:
            assert m in str(w[0].message)
            assert 'input_type=ModelAlien' in str(w[0].message)


def test_mixed_union_models_and_other_types() -> None:
    s = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.tagged_union_schema(
                    discriminator='type_',
                    choices={
                        'cat': core_schema.model_schema(
                            cls=ModelCat,
                            schema=core_schema.model_fields_schema(
                                fields={
                                    'type_': core_schema.model_field(core_schema.literal_schema(['cat'])),
                                },
                            ),
                        ),
                        'dog': core_schema.model_schema(
                            cls=ModelDog,
                            schema=core_schema.model_fields_schema(
                                fields={
                                    'type_': core_schema.model_field(core_schema.literal_schema(['dog'])),
                                },
                            ),
                        ),
                    },
                ),
                core_schema.str_schema(),
            ]
        )
    )

    assert s.to_python(ModelCat(type_='cat'), warnings='error') == {'type_': 'cat'}
    assert s.to_python(ModelDog(type_='dog'), warnings='error') == {'type_': 'dog'}
    # note, this fails as ModelCat and ModelDog (discriminator warnings, etc), but the warnings
    # don't bubble up to this level :)
    assert s.to_python('a string', warnings='error') == 'a string'


@pytest.mark.parametrize(
    'input,expected',
    [
        ({True: '1'}, b'{"true":"1"}'),
        ({1: '1'}, b'{"1":"1"}'),
        ({2.3: '1'}, b'{"2.3":"1"}'),
        ({'a': 'b'}, b'{"a":"b"}'),
    ],
)
def test_union_of_unions_of_models_with_tagged_union_json_key_serialization(
    input: dict[bool | int | float | str, str], expected: bytes
) -> None:
    s = SchemaSerializer(
        core_schema.dict_schema(
            keys_schema=core_schema.union_schema(
                [
                    core_schema.union_schema([core_schema.bool_schema(), core_schema.int_schema()]),
                    core_schema.union_schema([core_schema.float_schema(), core_schema.str_schema()]),
                ]
            ),
            values_schema=core_schema.str_schema(),
        )
    )

    assert s.to_json(input, warnings='error') == expected


@pytest.mark.parametrize(
    'input,expected',
    [
        ({'key': True}, b'{"key":true}'),
        ({'key': 1}, b'{"key":1}'),
        ({'key': 2.3}, b'{"key":2.3}'),
        ({'key': 'a'}, b'{"key":"a"}'),
    ],
)
def test_union_of_unions_of_models_with_tagged_union_json_serialization(
    input: dict[str, bool | int | float | str], expected: bytes
) -> None:
    s = SchemaSerializer(
        core_schema.dict_schema(
            keys_schema=core_schema.str_schema(),
            values_schema=core_schema.union_schema(
                [
                    core_schema.union_schema([core_schema.bool_schema(), core_schema.int_schema()]),
                    core_schema.union_schema([core_schema.float_schema(), core_schema.str_schema()]),
                ]
            ),
        )
    )

    assert s.to_json(input, warnings='error') == expected


def test_discriminated_union_ser_with_typed_dict() -> None:
    v = SchemaSerializer(
        core_schema.tagged_union_schema(
            {
                'a': core_schema.typed_dict_schema(
                    {
                        'type': core_schema.typed_dict_field(core_schema.literal_schema(['a'])),
                        'a': core_schema.typed_dict_field(core_schema.int_schema()),
                    }
                ),
                'b': core_schema.typed_dict_schema(
                    {
                        'type': core_schema.typed_dict_field(core_schema.literal_schema(['b'])),
                        'b': core_schema.typed_dict_field(core_schema.str_schema()),
                    }
                ),
            },
            discriminator='type',
        )
    )

    assert v.to_python({'type': 'a', 'a': 1}, warnings='error') == {'type': 'a', 'a': 1}
    assert v.to_python({'type': 'b', 'b': 'foo'}, warnings='error') == {'type': 'b', 'b': 'foo'}
