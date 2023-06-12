import json
import math
import re
import typing
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    FrozenSet,
    Generic,
    Iterable,
    List,
    NamedTuple,
    NewType,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

import pytest
from pydantic_core import CoreSchema, core_schema, to_json
from typing_extensions import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ImportString,
    PydanticUserError,
    RootModel,
    ValidationError,
    computed_field,
    field_validator,
)
from pydantic._internal._core_metadata import CoreMetadataHandler, build_metadata_dict
from pydantic.color import Color
from pydantic.config import ConfigDict
from pydantic.dataclasses import dataclass
from pydantic.errors import PydanticInvalidForJsonSchema
from pydantic.json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaValue,
    PydanticJsonSchemaWarning,
    model_json_schema,
    models_json_schema,
)
from pydantic.networks import AnyUrl, EmailStr, IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork, MultiHostUrl, NameEmail
from pydantic.type_adapter import TypeAdapter
from pydantic.types import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    DirectoryPath,
    FilePath,
    InstanceOf,
    Json,
    NegativeFloat,
    NegativeInt,
    NewPath,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PositiveFloat,
    PositiveInt,
    SecretBytes,
    SecretStr,
    StrictBool,
    StrictStr,
    WithJsonSchema,
    conbytes,
    condate,
    condecimal,
    confloat,
    conint,
    constr,
)

try:
    import email_validator
except ImportError:
    email_validator = None

T = TypeVar('T')


def test_by_alias():
    class ApplePie(BaseModel):
        model_config = ConfigDict(title='Apple Pie')
        a: float = Field(alias='Snap')
        b: int = Field(10, alias='Crackle')

    assert ApplePie.model_json_schema() == {
        'type': 'object',
        'title': 'Apple Pie',
        'properties': {
            'Snap': {'type': 'number', 'title': 'Snap'},
            'Crackle': {'type': 'integer', 'title': 'Crackle', 'default': 10},
        },
        'required': ['Snap'],
    }
    assert list(ApplePie.model_json_schema(by_alias=True)['properties'].keys()) == ['Crackle', 'Snap']
    assert list(ApplePie.model_json_schema(by_alias=False)['properties'].keys()) == ['a', 'b']


def test_ref_template():
    class KeyLimePie(BaseModel):
        x: str = None

    class ApplePie(BaseModel):
        model_config = ConfigDict(title='Apple Pie')
        a: float = None
        key_lime: Optional[KeyLimePie] = None

    assert ApplePie.model_json_schema(ref_template='foobar/{model}.json') == {
        'title': 'Apple Pie',
        'type': 'object',
        'properties': {
            'a': {'default': None, 'title': 'A', 'type': 'number'},
            'key_lime': {
                'anyOf': [{'$ref': 'foobar/KeyLimePie.json'}, {'type': 'null'}],
                'default': None,
            },
        },
        '$defs': {
            'KeyLimePie': {
                'title': 'KeyLimePie',
                'type': 'object',
                'properties': {'x': {'default': None, 'title': 'X', 'type': 'string'}},
            }
        },
    }
    assert ApplePie.model_json_schema()['properties']['key_lime'] == {
        'anyOf': [{'$ref': '#/$defs/KeyLimePie'}, {'type': 'null'}],
        'default': None,
    }
    json_schema = json.dumps(ApplePie.model_json_schema(ref_template='foobar/{model}.json'))
    assert 'foobar/KeyLimePie.json' in json_schema
    assert '#/$defs/KeyLimePie' not in json_schema


def test_by_alias_generator():
    class ApplePie(BaseModel):
        model_config = ConfigDict(alias_generator=lambda x: x.upper())
        a: float
        b: int = 10

    assert ApplePie.model_json_schema() == {
        'title': 'ApplePie',
        'type': 'object',
        'properties': {'A': {'title': 'A', 'type': 'number'}, 'B': {'title': 'B', 'default': 10, 'type': 'integer'}},
        'required': ['A'],
    }
    assert ApplePie.model_json_schema(by_alias=False)['properties'].keys() == {'a', 'b'}


def test_sub_model():
    class Foo(BaseModel):
        """hello"""

        b: float

    class Bar(BaseModel):
        a: int
        b: Optional[Foo] = None

    assert Bar.model_json_schema() == {
        'type': 'object',
        'title': 'Bar',
        '$defs': {
            'Foo': {
                'type': 'object',
                'title': 'Foo',
                'description': 'hello',
                'properties': {'b': {'type': 'number', 'title': 'B'}},
                'required': ['b'],
            }
        },
        'properties': {
            'a': {'type': 'integer', 'title': 'A'},
            'b': {'anyOf': [{'$ref': '#/$defs/Foo'}, {'type': 'null'}], 'default': None},
        },
        'required': ['a'],
    }


def test_schema_class():
    class Model(BaseModel):
        foo: int = Field(4, title='Foo is Great')
        bar: str = Field(..., description='this description of bar')

    with pytest.raises(ValidationError):
        Model()

    m = Model(bar='123')
    assert m.model_dump() == {'foo': 4, 'bar': '123'}

    assert Model.model_json_schema() == {
        'type': 'object',
        'title': 'Model',
        'properties': {
            'foo': {'type': 'integer', 'title': 'Foo is Great', 'default': 4},
            'bar': {'type': 'string', 'title': 'Bar', 'description': 'this description of bar'},
        },
        'required': ['bar'],
    }


def test_schema_repr():
    s = Field(4, title='Foo is Great')
    assert str(s) == "annotation=NoneType required=False default=4 title='Foo is Great'"
    assert repr(s) == "FieldInfo(annotation=NoneType, required=False, default=4, title='Foo is Great')"


def test_schema_class_by_alias():
    class Model(BaseModel):
        foo: int = Field(4, alias='foofoo')

    assert list(Model.model_json_schema()['properties'].keys()) == ['foofoo']
    assert list(Model.model_json_schema(by_alias=False)['properties'].keys()) == ['foo']


def test_choices():
    FooEnum = Enum('FooEnum', {'foo': 'f', 'bar': 'b'})
    BarEnum = IntEnum('BarEnum', {'foo': 1, 'bar': 2})

    class SpamEnum(str, Enum):
        foo = 'f'
        bar = 'b'

    class Model(BaseModel):
        foo: FooEnum
        bar: BarEnum
        spam: SpamEnum = Field(None)

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'type': 'object',
        'properties': {
            'foo': {'$ref': '#/$defs/FooEnum'},
            'bar': {'$ref': '#/$defs/BarEnum'},
            'spam': {'allOf': [{'$ref': '#/$defs/SpamEnum'}], 'default': None},
        },
        'required': ['foo', 'bar'],
        'title': 'Model',
        '$defs': {
            'BarEnum': {'enum': [1, 2], 'title': 'BarEnum', 'type': 'integer'},
            'SpamEnum': {'enum': ['f', 'b'], 'title': 'SpamEnum', 'type': 'string'},
            'FooEnum': {'enum': ['f', 'b'], 'title': 'FooEnum'},
        },
    }


def test_enum_modify_schema():
    class SpamEnum(str, Enum):
        """
        Spam enum.
        """

        foo = 'f'
        bar = 'b'

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            field_schema = handler(core_schema)
            field_schema = handler.resolve_ref_schema(field_schema)
            existing_comment = field_schema.get('$comment', '')
            field_schema['$comment'] = existing_comment + 'comment'  # make sure this function is only called once
            field_schema['tsEnumNames'] = [e.name for e in cls]
            return field_schema

    class Model(BaseModel):
        spam: Optional[SpamEnum] = Field(None)

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        '$defs': {
            'SpamEnum': {
                '$comment': 'comment',
                'description': 'Spam enum.',
                'enum': ['f', 'b'],
                'title': 'SpamEnum',
                'tsEnumNames': ['foo', 'bar'],
                'type': 'string',
            }
        },
        'properties': {'spam': {'anyOf': [{'$ref': '#/$defs/SpamEnum'}, {'type': 'null'}], 'default': None}},
        'title': 'Model',
        'type': 'object',
    }


def test_enum_schema_custom_field():
    class FooBarEnum(str, Enum):
        foo = 'foo'
        bar = 'bar'

    class Model(BaseModel):
        pika: FooBarEnum = Field(alias='pikalias', title='Pikapika!', description='Pika is definitely the best!')
        bulbi: FooBarEnum = Field('foo', alias='bulbialias', title='Bulbibulbi!', description='Bulbi is not...')
        cara: FooBarEnum

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'type': 'object',
        'properties': {
            'pikalias': {
                'title': 'Pikapika!',
                'description': 'Pika is definitely the best!',
                'allOf': [{'$ref': '#/$defs/FooBarEnum'}],
            },
            'bulbialias': {
                'allOf': [{'$ref': '#/$defs/FooBarEnum'}],
                'default': 'foo',
                'title': 'Bulbibulbi!',
                'description': 'Bulbi is not...',
            },
            'cara': {'$ref': '#/$defs/FooBarEnum'},
        },
        'required': ['pikalias', 'cara'],
        'title': 'Model',
        '$defs': {'FooBarEnum': {'enum': ['foo', 'bar'], 'title': 'FooBarEnum', 'type': 'string'}},
    }


def test_enum_and_model_have_same_behaviour():
    class Names(str, Enum):
        rick = 'Rick'
        morty = 'Morty'
        summer = 'Summer'

    class Pika(BaseModel):
        a: str

    class Foo(BaseModel):
        enum: Names
        titled_enum: Names = Field(
            ...,
            title='Title of enum',
            description='Description of enum',
        )
        model: Pika
        titled_model: Pika = Field(
            ...,
            title='Title of model',
            description='Description of model',
        )

    # insert_assert(Foo.model_json_schema())
    assert Foo.model_json_schema() == {
        'type': 'object',
        'properties': {
            'enum': {'$ref': '#/$defs/Names'},
            'titled_enum': {
                'title': 'Title of enum',
                'description': 'Description of enum',
                'allOf': [{'$ref': '#/$defs/Names'}],
            },
            'model': {'$ref': '#/$defs/Pika'},
            'titled_model': {
                'title': 'Title of model',
                'description': 'Description of model',
                'allOf': [{'$ref': '#/$defs/Pika'}],
            },
        },
        'required': ['enum', 'titled_enum', 'model', 'titled_model'],
        'title': 'Foo',
        '$defs': {
            'Names': {'enum': ['Rick', 'Morty', 'Summer'], 'title': 'Names', 'type': 'string'},
            'Pika': {
                'type': 'object',
                'properties': {'a': {'type': 'string', 'title': 'A'}},
                'required': ['a'],
                'title': 'Pika',
            },
        },
    }


def test_enum_includes_extra_without_other_params():
    class Names(str, Enum):
        rick = 'Rick'
        morty = 'Morty'
        summer = 'Summer'

    class Foo(BaseModel):
        enum: Names
        extra_enum: Names = Field(..., json_schema_extra={'extra': 'Extra field'})

    assert Foo.model_json_schema() == {
        '$defs': {
            'Names': {
                'enum': ['Rick', 'Morty', 'Summer'],
                'title': 'Names',
                'type': 'string',
            },
        },
        'properties': {
            'enum': {'$ref': '#/$defs/Names'},
            'extra_enum': {'allOf': [{'$ref': '#/$defs/Names'}], 'extra': 'Extra field'},
        },
        'required': ['enum', 'extra_enum'],
        'title': 'Foo',
        'type': 'object',
    }


def test_invalid_json_schema_extra():
    class MyModel(BaseModel):
        model_config = ConfigDict(json_schema_extra=1)

        name: str

    with pytest.raises(
        ValueError, match=re.escape("model_config['json_schema_extra']=1 should be a dict, callable, or None")
    ):
        MyModel.model_json_schema()


def test_list_enum_schema_extras():
    class FoodChoice(str, Enum):
        spam = 'spam'
        egg = 'egg'
        chips = 'chips'

    class Model(BaseModel):
        foods: List[FoodChoice] = Field(examples=[['spam', 'egg']])

    assert Model.model_json_schema() == {
        '$defs': {
            'FoodChoice': {
                'enum': ['spam', 'egg', 'chips'],
                'title': 'FoodChoice',
                'type': 'string',
            }
        },
        'properties': {
            'foods': {
                'title': 'Foods',
                'type': 'array',
                'items': {'$ref': '#/$defs/FoodChoice'},
                'examples': [['spam', 'egg']],
            },
        },
        'required': ['foods'],
        'title': 'Model',
        'type': 'object',
    }


def test_enum_schema_cleandoc():
    class FooBar(str, Enum):
        """
        This is docstring which needs to be cleaned up
        """

        foo = 'foo'
        bar = 'bar'

    class Model(BaseModel):
        enum: FooBar

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'enum': {'$ref': '#/$defs/FooBar'}},
        'required': ['enum'],
        '$defs': {
            'FooBar': {
                'title': 'FooBar',
                'description': 'This is docstring which needs to be cleaned up',
                'enum': ['foo', 'bar'],
                'type': 'string',
            }
        },
    }


def test_decimal_json_schema():
    class Model(BaseModel):
        a: bytes = b'foobar'
        b: Decimal = Decimal('12.34')

    model_json_schema_validation = Model.model_json_schema(mode='validation')
    model_json_schema_serialization = Model.model_json_schema(mode='serialization')

    assert model_json_schema_validation == {
        'properties': {
            'a': {'default': 'foobar', 'format': 'binary', 'title': 'A', 'type': 'string'},
            'b': {'anyOf': [{'type': 'number'}, {'type': 'string'}], 'default': '12.34', 'title': 'B'},
        },
        'title': 'Model',
        'type': 'object',
    }
    assert model_json_schema_serialization == {
        'properties': {
            'a': {'default': 'foobar', 'format': 'binary', 'title': 'A', 'type': 'string'},
            'b': {'default': '12.34', 'title': 'B', 'type': 'string'},
        },
        'required': ['a', 'b'],
        'title': 'Model',
        'type': 'object',
    }


def test_list_sub_model():
    class Foo(BaseModel):
        a: float

    class Bar(BaseModel):
        b: List[Foo]

    assert Bar.model_json_schema() == {
        'title': 'Bar',
        'type': 'object',
        '$defs': {
            'Foo': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'type': 'number', 'title': 'A'}},
                'required': ['a'],
            }
        },
        'properties': {'b': {'type': 'array', 'items': {'$ref': '#/$defs/Foo'}, 'title': 'B'}},
        'required': ['b'],
    }


def test_optional():
    class Model(BaseModel):
        a: Optional[str]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'title': 'A'}},
        'required': ['a'],
    }


def test_optional_modify_schema():
    class MyNone(Type[None]):
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            return core_schema.nullable_schema(core_schema.none_schema())

    class Model(BaseModel):
        x: MyNone

    assert Model.model_json_schema() == {
        'properties': {'x': {'title': 'X', 'type': 'null'}},
        'required': ['x'],
        'title': 'Model',
        'type': 'object',
    }


def test_any():
    class Model(BaseModel):
        a: Any
        b: object

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A'},
            'b': {'title': 'B'},
        },
        'required': ['a', 'b'],
    }


def test_set():
    class Model(BaseModel):
        a: Set[int]
        b: set
        c: set = {1}

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'array', 'uniqueItems': True, 'items': {'type': 'integer'}},
            'b': {'title': 'B', 'type': 'array', 'items': {}, 'uniqueItems': True},
            'c': {'title': 'C', 'type': 'array', 'items': {}, 'default': [1], 'uniqueItems': True},
        },
        'required': ['a', 'b'],
    }


@pytest.mark.parametrize(
    'field_type,extra_props',
    [
        (tuple, {'items': {}}),
        (Tuple, {'items': {}}),
        (
            Tuple[str, int, Union[str, int, float], float],
            {
                'prefixItems': [
                    {'type': 'string'},
                    {'type': 'integer'},
                    {'anyOf': [{'type': 'string'}, {'type': 'integer'}, {'type': 'number'}]},
                    {'type': 'number'},
                ],
                'minItems': 4,
                'maxItems': 4,
            },
        ),
        (Tuple[str], {'prefixItems': [{'type': 'string'}], 'minItems': 1, 'maxItems': 1}),
        (Tuple[()], {'maxItems': 0, 'minItems': 0}),
        (
            Tuple[str, ...],
            {'items': {'type': 'string'}, 'type': 'array'},
        ),
    ],
)
def test_tuple(field_type, extra_props):
    class Model(BaseModel):
        a: field_type

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'array', **extra_props}},
        'required': ['a'],
    }

    ta = TypeAdapter(field_type)

    assert ta.json_schema() == {'type': 'array', **extra_props}


def test_deque():
    class Model(BaseModel):
        a: Deque[str]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'array', 'items': {'type': 'string'}}},
        'required': ['a'],
    }


def test_bool():
    class Model(BaseModel):
        a: bool

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'boolean'}},
        'required': ['a'],
    }


def test_strict_bool():
    class Model(BaseModel):
        a: StrictBool

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'boolean'}},
        'required': ['a'],
    }


def test_dict():
    class Model(BaseModel):
        a: dict

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'object'}},
        'required': ['a'],
    }


def test_list():
    class Model(BaseModel):
        a: list

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'array', 'items': {}}},
        'required': ['a'],
    }


class Foo(BaseModel):
    a: float


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (
            Union[int, str],
            {
                'properties': {'a': {'title': 'A', 'anyOf': [{'type': 'integer'}, {'type': 'string'}]}},
                'required': ['a'],
            },
        ),
        (
            List[int],
            {'properties': {'a': {'title': 'A', 'type': 'array', 'items': {'type': 'integer'}}}, 'required': ['a']},
        ),
        (
            Dict[str, Foo],
            {
                '$defs': {
                    'Foo': {
                        'title': 'Foo',
                        'type': 'object',
                        'properties': {'a': {'title': 'A', 'type': 'number'}},
                        'required': ['a'],
                    }
                },
                'properties': {'a': {'title': 'A', 'type': 'object', 'additionalProperties': {'$ref': '#/$defs/Foo'}}},
                'required': ['a'],
            },
        ),
        (
            Union[None, Foo],
            {
                '$defs': {
                    'Foo': {
                        'title': 'Foo',
                        'type': 'object',
                        'properties': {'a': {'title': 'A', 'type': 'number'}},
                        'required': ['a'],
                    }
                },
                'properties': {'a': {'anyOf': [{'$ref': '#/$defs/Foo'}, {'type': 'null'}]}},
                'required': ['a'],
                'title': 'Model',
                'type': 'object',
            },
        ),
        (
            Union[int, int],
            {'properties': {'a': {'title': 'A', 'type': 'integer'}}, 'required': ['a']},
        ),
        (Dict[str, Any], {'properties': {'a': {'title': 'A', 'type': 'object'}}, 'required': ['a']}),
    ],
)
def test_list_union_dict(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {'title': 'Model', 'type': 'object'}
    base_schema.update(expected_schema)

    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (datetime, {'type': 'string', 'format': 'date-time'}),
        (date, {'type': 'string', 'format': 'date'}),
        (time, {'type': 'string', 'format': 'time'}),
        (timedelta, {'type': 'string', 'format': 'duration'}),
    ],
)
def test_date_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    attribute_schema = {'title': 'A'}
    attribute_schema.update(expected_schema)

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': attribute_schema}, 'required': ['a']}

    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (condate(), {}),
        (
            condate(gt=date(2010, 1, 1), lt=date(2021, 2, 2)),
            {'exclusiveMinimum': date(2010, 1, 1), 'exclusiveMaximum': date(2021, 2, 2)},
        ),
        (condate(ge=date(2010, 1, 1), le=date(2021, 2, 2)), {'minimum': date(2010, 1, 1), 'maximum': date(2021, 2, 2)}),
    ],
)
def test_date_constrained_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'format': 'date', **expected_schema}},
        'required': ['a'],
    }


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (Optional[str], {'properties': {'a': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'title': 'A'}}}),
        (
            Optional[bytes],
            {'properties': {'a': {'title': 'A', 'anyOf': [{'type': 'string', 'format': 'binary'}, {'type': 'null'}]}}},
        ),
        (
            Union[str, bytes],
            {
                'properties': {
                    'a': {'title': 'A', 'anyOf': [{'type': 'string'}, {'type': 'string', 'format': 'binary'}]}
                },
            },
        ),
        (
            Union[None, str, bytes],
            {
                'properties': {
                    'a': {
                        'title': 'A',
                        'anyOf': [{'type': 'string'}, {'type': 'string', 'format': 'binary'}, {'type': 'null'}],
                    }
                }
            },
        ),
    ],
)
def test_str_basic_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {'title': 'Model', 'type': 'object', 'required': ['a']}
    base_schema.update(expected_schema)
    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (Pattern, {'type': 'string', 'format': 'regex'}),
        (Pattern[str], {'type': 'string', 'format': 'regex'}),
        (Pattern[bytes], {'type': 'string', 'format': 'regex'}),
    ],
)
def test_pattern(field_type, expected_schema) -> None:
    class Model(BaseModel):
        a: field_type

    expected_schema.update({'title': 'A'})
    full_schema = {'title': 'Model', 'type': 'object', 'required': ['a'], 'properties': {'a': expected_schema}}
    assert Model.model_json_schema() == full_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (StrictStr, {'title': 'A', 'type': 'string'}),
        # (ConstrainedStr, {'title': 'A', 'type': 'string'}),
        (
            constr(min_length=3, max_length=5, pattern='^text$'),
            {'title': 'A', 'type': 'string', 'minLength': 3, 'maxLength': 5, 'pattern': '^text$'},
        ),
    ],
)
def test_str_constrained_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    model_schema = Model.model_json_schema()
    assert model_schema['properties']['a'] == expected_schema

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': expected_schema}, 'required': ['a']}

    assert model_schema == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (AnyUrl, {'title': 'A', 'type': 'string', 'format': 'uri', 'minLength': 1}),
        (
            Annotated[AnyUrl, Field(max_length=2**16)],
            {'title': 'A', 'type': 'string', 'format': 'uri', 'minLength': 1, 'maxLength': 2**16},
        ),
        (MultiHostUrl, {'title': 'A', 'type': 'string', 'format': 'multi-host-uri', 'minLength': 1}),
    ],
)
def test_special_str_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': {}}, 'required': ['a']}
    base_schema['properties']['a'] = expected_schema

    assert Model.model_json_schema() == base_schema


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
@pytest.mark.parametrize('field_type,expected_schema', [(EmailStr, 'email'), (NameEmail, 'name-email')])
def test_email_str_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string'}},
        'required': ['a'],
    }
    base_schema['properties']['a']['format'] = expected_schema

    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize('field_type,inner_type', [(SecretBytes, 'string'), (SecretStr, 'string')])
def test_secret_types(field_type, inner_type):
    class Model(BaseModel):
        a: field_type

    base_schema = {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': inner_type, 'writeOnly': True, 'format': 'password'}},
        'required': ['a'],
    }

    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        # (ConstrainedInt, {}),
        (conint(gt=5, lt=10), {'exclusiveMinimum': 5, 'exclusiveMaximum': 10}),
        (conint(ge=5, le=10), {'minimum': 5, 'maximum': 10}),
        (conint(multiple_of=5), {'multipleOf': 5}),
        (PositiveInt, {'exclusiveMinimum': 0}),
        (NegativeInt, {'exclusiveMaximum': 0}),
        (NonNegativeInt, {'minimum': 0}),
        (NonPositiveInt, {'maximum': 0}),
    ],
)
def test_special_int_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
    }
    base_schema['properties']['a'].update(expected_schema)

    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (confloat(gt=5, lt=10), {'exclusiveMinimum': 5, 'exclusiveMaximum': 10}),
        (confloat(ge=5, le=10), {'minimum': 5, 'maximum': 10}),
        (confloat(multiple_of=5), {'multipleOf': 5}),
        (PositiveFloat, {'exclusiveMinimum': 0}),
        (NegativeFloat, {'exclusiveMaximum': 0}),
        (NonNegativeFloat, {'minimum': 0}),
        (NonPositiveFloat, {'maximum': 0}),
    ],
)
def test_special_float_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'number'}},
        'required': ['a'],
    }
    base_schema['properties']['a'].update(expected_schema)

    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (condecimal(gt=5, lt=10), {'exclusiveMinimum': 5, 'exclusiveMaximum': 10}),
        (condecimal(ge=5, le=10), {'minimum': 5, 'maximum': 10}),
        (condecimal(multiple_of=5), {'multipleOf': 5}),
    ],
)
def test_special_decimal_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'anyOf': [{'type': 'number'}, {'type': 'string'}], 'title': 'A'}},
        'required': ['a'],
    }
    base_schema['properties']['a']['anyOf'][0].update(expected_schema)

    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [(UUID, 'uuid'), (UUID1, 'uuid1'), (UUID3, 'uuid3'), (UUID4, 'uuid4'), (UUID5, 'uuid5')],
)
def test_uuid_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'format': 'uuid'}},
        'required': ['a'],
    }
    base_schema['properties']['a']['format'] = expected_schema

    assert Model.model_json_schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [(FilePath, 'file-path'), (DirectoryPath, 'directory-path'), (NewPath, 'path'), (Path, 'path')],
)
def test_path_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'format': ''}},
        'required': ['a'],
    }
    base_schema['properties']['a']['format'] = expected_schema

    assert Model.model_json_schema() == base_schema


def test_json_type():
    class Model(BaseModel):
        a: Json
        b: Json[int]
        c: Json[Any]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'string', 'format': 'json-string'},
            'b': {'title': 'B', 'type': 'string', 'format': 'json-string'},
            'c': {'title': 'C', 'type': 'string', 'format': 'json-string'},
        },
        'required': ['a', 'b', 'c'],
    }
    assert Model.model_json_schema(mode='serialization') == {
        'properties': {'a': {'title': 'A'}, 'b': {'title': 'B', 'type': 'integer'}, 'c': {'title': 'C'}},
        'required': ['a', 'b', 'c'],
        'title': 'Model',
        'type': 'object',
    }


def test_ipv4address_type():
    class Model(BaseModel):
        ip_address: IPv4Address

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip Address', 'type': 'string', 'format': 'ipv4'}},
        'required': ['ip_address'],
    }


def test_ipv6address_type():
    class Model(BaseModel):
        ip_address: IPv6Address

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip Address', 'type': 'string', 'format': 'ipv6'}},
        'required': ['ip_address'],
    }


def test_ipvanyaddress_type():
    class Model(BaseModel):
        ip_address: IPvAnyAddress

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip Address', 'type': 'string', 'format': 'ipvanyaddress'}},
        'required': ['ip_address'],
    }


def test_ipv4interface_type():
    class Model(BaseModel):
        ip_interface: IPv4Interface

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip Interface', 'type': 'string', 'format': 'ipv4interface'}},
        'required': ['ip_interface'],
    }


def test_ipv6interface_type():
    class Model(BaseModel):
        ip_interface: IPv6Interface

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip Interface', 'type': 'string', 'format': 'ipv6interface'}},
        'required': ['ip_interface'],
    }


def test_ipvanyinterface_type():
    class Model(BaseModel):
        ip_interface: IPvAnyInterface

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip Interface', 'type': 'string', 'format': 'ipvanyinterface'}},
        'required': ['ip_interface'],
    }


def test_ipv4network_type():
    class Model(BaseModel):
        ip_network: IPv4Network

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_network': {'title': 'Ip Network', 'type': 'string', 'format': 'ipv4network'}},
        'required': ['ip_network'],
    }


def test_ipv6network_type():
    class Model(BaseModel):
        ip_network: IPv6Network

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_network': {'title': 'Ip Network', 'type': 'string', 'format': 'ipv6network'}},
        'required': ['ip_network'],
    }


def test_ipvanynetwork_type():
    class Model(BaseModel):
        ip_network: IPvAnyNetwork

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_network': {'title': 'Ip Network', 'type': 'string', 'format': 'ipvanynetwork'}},
        'required': ['ip_network'],
    }


@pytest.mark.parametrize(
    'type_,default_value',
    (
        (Callable, ...),
        (Callable, lambda x: x),
        (Callable[[int], int], ...),
        (Callable[[int], int], lambda x: x),
    ),
)
@pytest.mark.parametrize(
    'base_json_schema,properties',
    [
        (
            {'a': 'b'},
            {
                'callback': {'title': 'Callback', 'a': 'b'},
                'foo': {'title': 'Foo', 'type': 'integer'},
            },
        ),
        (
            None,
            {
                'foo': {'title': 'Foo', 'type': 'integer'},
            },
        ),
    ],
)
def test_callable_type(type_, default_value, base_json_schema, properties):
    class Model(BaseModel):
        callback: type_ = default_value
        foo: int

    with pytest.raises(PydanticInvalidForJsonSchema):
        Model.model_json_schema()

    class ModelWithOverride(BaseModel):
        callback: Annotated[type_, WithJsonSchema(base_json_schema)] = default_value
        foo: int

    if default_value is Ellipsis or base_json_schema is None:
        model_schema = ModelWithOverride.model_json_schema()
    else:
        with pytest.warns(
            PydanticJsonSchemaWarning,
            match='Default value .* is not JSON serializable; excluding'
            r' default from JSON schema \[non-serializable-default]',
        ):
            model_schema = ModelWithOverride.model_json_schema()
    assert model_schema['properties'] == properties


@pytest.mark.parametrize(
    'default_value,properties',
    (
        (Field(...), {'callback': {'title': 'Callback', 'type': 'integer'}}),
        (1, {'callback': {'default': 1, 'title': 'Callback', 'type': 'integer'}}),
    ),
)
def test_callable_type_with_fallback(default_value, properties):
    class Model(BaseModel):
        callback: Union[int, Callable[[int], int]] = default_value

    class MyGenerator(GenerateJsonSchema):
        ignored_warning_kinds = ()

    with pytest.warns(
        PydanticJsonSchemaWarning,
        match=re.escape('Cannot generate a JsonSchema for core_schema.CallableSchema [skipped-choice]'),
    ):
        model_schema = Model.model_json_schema(schema_generator=MyGenerator)
    assert model_schema['properties'] == properties


@pytest.mark.parametrize(
    'type_,default_value,properties',
    (
        (
            Dict[Any, Any],
            {(lambda x: x): 1},
            {'callback': {'title': 'Callback', 'type': 'object'}},
        ),
        (
            Union[int, Callable[[int], int]],
            lambda x: x,
            {'callback': {'title': 'Callback', 'type': 'integer'}},
        ),
    ),
)
def test_non_serializable_default(type_, default_value, properties):
    class Model(BaseModel):
        callback: type_ = default_value

    with pytest.warns(
        PydanticJsonSchemaWarning,
        match=(
            'Default value .* is not JSON serializable; excluding default from JSON schema '
            r'\[non-serializable-default\]'
        ),
    ):
        model_schema = Model.model_json_schema()
    assert model_schema['properties'] == properties
    assert model_schema.get('required') is None


@pytest.mark.parametrize(
    'warning_match',
    (
        r'Cannot generate a JsonSchema for core_schema.CallableSchema \[skipped-choice\]',
        r'Default value .* is not JSON serializable; excluding default from JSON schema \[non-serializable-default\]',
    ),
)
def test_callable_fallback_with_non_serializable_default(warning_match):
    class Model(BaseModel):
        callback: Union[int, Callable[[int], int]] = lambda x: x  # noqa E731

    class MyGenerator(GenerateJsonSchema):
        ignored_warning_kinds = ()

    with pytest.warns(PydanticJsonSchemaWarning, match=warning_match):
        model_schema = Model.model_json_schema(schema_generator=MyGenerator)
    assert model_schema == {
        'properties': {'callback': {'title': 'Callback', 'type': 'integer'}},
        'title': 'Model',
        'type': 'object',
    }


def test_error_non_supported_types():
    class Model(BaseModel):
        a: ImportString

    with pytest.raises(PydanticInvalidForJsonSchema):
        Model.model_json_schema()


def test_schema_overrides():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo = Foo(a='foo')

    class Baz(BaseModel):
        c: Optional[Bar]

    class Model(BaseModel):
        d: Baz

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        '$defs': {
            'Foo': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'string'}},
                'required': ['a'],
            },
            'Bar': {
                'title': 'Bar',
                'type': 'object',
                'properties': {'b': {'allOf': [{'$ref': '#/$defs/Foo'}], 'default': {'a': 'foo'}}},
            },
            'Baz': {
                'title': 'Baz',
                'type': 'object',
                'properties': {'c': {'anyOf': [{'$ref': '#/$defs/Bar'}, {'type': 'null'}]}},
                'required': ['c'],
            },
        },
        'properties': {'d': {'$ref': '#/$defs/Baz'}},
        'required': ['d'],
    }


def test_schema_overrides_w_union():
    class Foo(BaseModel):
        pass

    class Bar(BaseModel):
        pass

    class Spam(BaseModel):
        a: Union[Foo, Bar] = Field(..., description='xxx')

    assert Spam.model_json_schema()['properties'] == {
        'a': {
            'title': 'A',
            'description': 'xxx',
            'anyOf': [{'$ref': '#/$defs/Foo'}, {'$ref': '#/$defs/Bar'}],
        },
    }


def test_schema_from_models():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    class Model(BaseModel):
        d: Baz

    class Ingredient(BaseModel):
        name: str

    class Pizza(BaseModel):
        name: str
        ingredients: List[Ingredient]

    keys_map, model_schema = models_json_schema(
        [(Model, 'validation'), (Pizza, 'validation')],
        title='Multi-model schema',
        description='Single JSON Schema with multiple definitions',
    )
    assert keys_map == {(Pizza, 'validation'): 'Pizza', (Model, 'validation'): 'Model'}
    assert model_schema == {
        'title': 'Multi-model schema',
        'description': 'Single JSON Schema with multiple definitions',
        '$defs': {
            'Pizza': {
                'title': 'Pizza',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'ingredients': {
                        'title': 'Ingredients',
                        'type': 'array',
                        'items': {'$ref': '#/$defs/Ingredient'},
                    },
                },
                'required': ['name', 'ingredients'],
            },
            'Ingredient': {
                'title': 'Ingredient',
                'type': 'object',
                'properties': {'name': {'title': 'Name', 'type': 'string'}},
                'required': ['name'],
            },
            'Model': {
                'title': 'Model',
                'type': 'object',
                'properties': {'d': {'$ref': '#/$defs/Baz'}},
                'required': ['d'],
            },
            'Baz': {
                'title': 'Baz',
                'type': 'object',
                'properties': {'c': {'$ref': '#/$defs/Bar'}},
                'required': ['c'],
            },
            'Bar': {
                'title': 'Bar',
                'type': 'object',
                'properties': {'b': {'$ref': '#/$defs/Foo'}},
                'required': ['b'],
            },
            'Foo': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'string'}},
                'required': ['a'],
            },
        },
    }


def test_schema_with_refs():
    ref_template = '#/components/schemas/{model}'

    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    keys_map, model_schema = models_json_schema([(Bar, 'validation'), (Baz, 'validation')], ref_template=ref_template)
    assert keys_map == {(Bar, 'validation'): 'Bar', (Baz, 'validation'): 'Baz'}
    assert model_schema == {
        '$defs': {
            'Baz': {
                'title': 'Baz',
                'type': 'object',
                'properties': {'c': {'$ref': '#/components/schemas/Bar'}},
                'required': ['c'],
            },
            'Bar': {
                'title': 'Bar',
                'type': 'object',
                'properties': {'b': {'$ref': '#/components/schemas/Foo'}},
                'required': ['b'],
            },
            'Foo': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'string'}},
                'required': ['a'],
            },
        }
    }


def test_schema_with_custom_ref_template():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    keys_map, model_schema = models_json_schema(
        [(Bar, 'validation'), (Baz, 'validation')], ref_template='/schemas/{model}.json#/'
    )
    assert keys_map == {(Bar, 'validation'): 'Bar', (Baz, 'validation'): 'Baz'}
    assert model_schema == {
        '$defs': {
            'Baz': {
                'title': 'Baz',
                'type': 'object',
                'properties': {'c': {'$ref': '/schemas/Bar.json#/'}},
                'required': ['c'],
            },
            'Bar': {
                'title': 'Bar',
                'type': 'object',
                'properties': {'b': {'$ref': '/schemas/Foo.json#/'}},
                'required': ['b'],
            },
            'Foo': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'string'}},
                'required': ['a'],
            },
        }
    }


def test_schema_ref_template_key_error():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    with pytest.raises(KeyError):
        models_json_schema([(Bar, 'validation'), (Baz, 'validation')], ref_template='/schemas/{bad_name}.json#/')


def test_schema_no_definitions():
    keys_map, model_schema = models_json_schema([], title='Schema without definitions')
    assert keys_map == {}
    assert model_schema == {'title': 'Schema without definitions'}


def test_list_default():
    class UserModel(BaseModel):
        friends: List[int] = [1]

    assert UserModel.model_json_schema() == {
        'title': 'UserModel',
        'type': 'object',
        'properties': {'friends': {'title': 'Friends', 'default': [1], 'type': 'array', 'items': {'type': 'integer'}}},
    }


def test_enum_str_default():
    class MyEnum(str, Enum):
        FOO = 'foo'

    class UserModel(BaseModel):
        friends: MyEnum = MyEnum.FOO

    assert UserModel.model_json_schema()['properties']['friends']['default'] is MyEnum.FOO.value


def test_enum_int_default():
    class MyEnum(IntEnum):
        FOO = 1

    class UserModel(BaseModel):
        friends: MyEnum = MyEnum.FOO

    assert UserModel.model_json_schema()['properties']['friends']['default'] is MyEnum.FOO.value


def test_dict_default():
    class UserModel(BaseModel):
        friends: Dict[str, float] = {'a': 1.1, 'b': 2.2}

    assert UserModel.model_json_schema() == {
        'title': 'UserModel',
        'type': 'object',
        'properties': {
            'friends': {
                'title': 'Friends',
                'default': {'a': 1.1, 'b': 2.2},
                'type': 'object',
                'additionalProperties': {'type': 'number'},
            }
        },
    }


def test_model_default():
    """Make sure inner model types are encoded properly"""

    class Inner(BaseModel):
        a: Dict[Path, str] = {Path(): ''}

    class Outer(BaseModel):
        inner: Inner = Inner()

    assert Outer.model_json_schema() == {
        '$defs': {
            'Inner': {
                'properties': {
                    'a': {
                        'additionalProperties': {'type': 'string'},
                        'default': {'.': ''},
                        'title': 'A',
                        'type': 'object',
                    }
                },
                'title': 'Inner',
                'type': 'object',
            }
        },
        'properties': {'inner': {'allOf': [{'$ref': '#/$defs/Inner'}], 'default': {'a': {'.': ''}}}},
        'title': 'Outer',
        'type': 'object',
    }


@pytest.mark.parametrize(
    'kwargs,type_,expected_extra',
    [
        ({'max_length': 5}, str, {'type': 'string', 'maxLength': 5}),
        ({}, constr(max_length=6), {'type': 'string', 'maxLength': 6}),
        ({'min_length': 2}, str, {'type': 'string', 'minLength': 2}),
        ({'max_length': 5}, bytes, {'type': 'string', 'maxLength': 5, 'format': 'binary'}),
        ({'pattern': '^foo$'}, str, {'type': 'string', 'pattern': '^foo$'}),
        ({'gt': 2}, int, {'type': 'integer', 'exclusiveMinimum': 2}),
        ({'lt': 5}, int, {'type': 'integer', 'exclusiveMaximum': 5}),
        ({'ge': 2}, int, {'type': 'integer', 'minimum': 2}),
        ({'le': 5}, int, {'type': 'integer', 'maximum': 5}),
        ({'multiple_of': 5}, int, {'type': 'integer', 'multipleOf': 5}),
        ({'gt': 2}, float, {'type': 'number', 'exclusiveMinimum': 2}),
        ({'lt': 5}, float, {'type': 'number', 'exclusiveMaximum': 5}),
        ({'ge': 2}, float, {'type': 'number', 'minimum': 2}),
        ({'le': 5}, float, {'type': 'number', 'maximum': 5}),
        ({'gt': -math.inf}, float, {'type': 'number'}),
        ({'lt': math.inf}, float, {'type': 'number'}),
        ({'ge': -math.inf}, float, {'type': 'number'}),
        ({'le': math.inf}, float, {'type': 'number'}),
        ({'multiple_of': 5}, float, {'type': 'number', 'multipleOf': 5}),
        ({'gt': 2}, Decimal, {'anyOf': [{'exclusiveMinimum': 2.0, 'type': 'number'}, {'type': 'string'}]}),
        ({'lt': 5}, Decimal, {'anyOf': [{'type': 'number', 'exclusiveMaximum': 5}, {'type': 'string'}]}),
        ({'ge': 2}, Decimal, {'anyOf': [{'type': 'number', 'minimum': 2}, {'type': 'string'}]}),
        ({'le': 5}, Decimal, {'anyOf': [{'type': 'number', 'maximum': 5}, {'type': 'string'}]}),
        ({'multiple_of': 5}, Decimal, {'anyOf': [{'type': 'number', 'multipleOf': 5}, {'type': 'string'}]}),
    ],
)
def test_constraints_schema_validation(kwargs, type_, expected_extra):
    class Foo(BaseModel):
        a: type_ = Field('foo', title='A title', description='A description', **kwargs)

    expected_schema = {
        'title': 'Foo',
        'type': 'object',
        'properties': {'a': {'title': 'A title', 'description': 'A description', 'default': 'foo'}},
    }

    expected_schema['properties']['a'].update(expected_extra)
    assert Foo.model_json_schema(mode='validation') == expected_schema


@pytest.mark.parametrize(
    'kwargs,type_,expected_extra',
    [
        ({'max_length': 5}, str, {'type': 'string', 'maxLength': 5}),
        ({}, constr(max_length=6), {'type': 'string', 'maxLength': 6}),
        ({'min_length': 2}, str, {'type': 'string', 'minLength': 2}),
        ({'max_length': 5}, bytes, {'type': 'string', 'maxLength': 5, 'format': 'binary'}),
        ({'pattern': '^foo$'}, str, {'type': 'string', 'pattern': '^foo$'}),
        ({'gt': 2}, int, {'type': 'integer', 'exclusiveMinimum': 2}),
        ({'lt': 5}, int, {'type': 'integer', 'exclusiveMaximum': 5}),
        ({'ge': 2}, int, {'type': 'integer', 'minimum': 2}),
        ({'le': 5}, int, {'type': 'integer', 'maximum': 5}),
        ({'multiple_of': 5}, int, {'type': 'integer', 'multipleOf': 5}),
        ({'gt': 2}, float, {'type': 'number', 'exclusiveMinimum': 2}),
        ({'lt': 5}, float, {'type': 'number', 'exclusiveMaximum': 5}),
        ({'ge': 2}, float, {'type': 'number', 'minimum': 2}),
        ({'le': 5}, float, {'type': 'number', 'maximum': 5}),
        ({'gt': -math.inf}, float, {'type': 'number'}),
        ({'lt': math.inf}, float, {'type': 'number'}),
        ({'ge': -math.inf}, float, {'type': 'number'}),
        ({'le': math.inf}, float, {'type': 'number'}),
        ({'multiple_of': 5}, float, {'type': 'number', 'multipleOf': 5}),
        ({'gt': 2}, Decimal, {'type': 'string'}),
        ({'lt': 5}, Decimal, {'type': 'string'}),
        ({'ge': 2}, Decimal, {'type': 'string'}),
        ({'le': 5}, Decimal, {'type': 'string'}),
        ({'multiple_of': 5}, Decimal, {'type': 'string'}),
    ],
)
def test_constraints_schema_serialization(kwargs, type_, expected_extra):
    class Foo(BaseModel):
        a: type_ = Field('foo', title='A title', description='A description', **kwargs)

    expected_schema = {
        'title': 'Foo',
        'type': 'object',
        'properties': {'a': {'title': 'A title', 'description': 'A description', 'default': 'foo'}},
        'required': ['a'],
    }

    expected_schema['properties']['a'].update(expected_extra)
    assert Foo.model_json_schema(mode='serialization') == expected_schema


@pytest.mark.parametrize(
    'kwargs,type_,value',
    [
        ({'max_length': 5}, str, 'foo'),
        ({'min_length': 2}, str, 'foo'),
        ({'max_length': 5}, bytes, b'foo'),
        ({'pattern': '^foo$'}, str, 'foo'),
        ({'gt': 2}, int, 3),
        ({'lt': 5}, int, 3),
        ({'ge': 2}, int, 3),
        ({'ge': 2}, int, 2),
        ({'gt': 2}, int, '3'),
        ({'le': 5}, int, 3),
        ({'le': 5}, int, 5),
        ({'gt': 2}, float, 3.0),
        ({'gt': 2}, float, 2.1),
        ({'lt': 5}, float, 3.0),
        ({'lt': 5}, float, 4.9),
        ({'ge': 2}, float, 3.0),
        ({'ge': 2}, float, 2.0),
        ({'le': 5}, float, 3.0),
        ({'le': 5}, float, 5.0),
        ({'gt': 2}, float, 3),
        ({'gt': 2}, float, '3'),
        ({'gt': 2}, Decimal, Decimal(3)),
        ({'lt': 5}, Decimal, Decimal(3)),
        ({'ge': 2}, Decimal, Decimal(3)),
        ({'ge': 2}, Decimal, Decimal(2)),
        ({'le': 5}, Decimal, Decimal(3)),
        ({'le': 5}, Decimal, Decimal(5)),
    ],
)
def test_constraints_schema_validation_passes(kwargs, type_, value):
    class Foo(BaseModel):
        a: type_ = Field('foo', title='A title', description='A description', **kwargs)

    assert Foo(a=value)


@pytest.mark.parametrize(
    'kwargs,type_,value',
    [
        ({'max_length': 5}, str, 'foobar'),
        ({'min_length': 2}, str, 'f'),
        ({'pattern': '^foo$'}, str, 'bar'),
        ({'gt': 2}, int, 2),
        ({'lt': 5}, int, 5),
        ({'ge': 2}, int, 1),
        ({'le': 5}, int, 6),
        ({'gt': 2}, float, 2.0),
        ({'lt': 5}, float, 5.0),
        ({'ge': 2}, float, 1.9),
        ({'le': 5}, float, 5.1),
        ({'gt': 2}, Decimal, Decimal(2)),
        ({'lt': 5}, Decimal, Decimal(5)),
        ({'ge': 2}, Decimal, Decimal(1)),
        ({'le': 5}, Decimal, Decimal(6)),
    ],
)
def test_constraints_schema_validation_raises(kwargs, type_, value):
    class Foo(BaseModel):
        a: type_ = Field('foo', title='A title', description='A description', **kwargs)

    with pytest.raises(ValidationError):
        Foo(a=value)


def test_schema_kwargs():
    class Foo(BaseModel):
        a: str = Field('foo', examples=['bar'])

    assert Foo.model_json_schema() == {
        'title': 'Foo',
        'type': 'object',
        'properties': {'a': {'type': 'string', 'title': 'A', 'default': 'foo', 'examples': ['bar']}},
    }


def test_schema_dict_constr():
    regex_str = r'^([a-zA-Z_][a-zA-Z0-9_]*)$'
    ConStrType = constr(pattern=regex_str)
    ConStrKeyDict = Dict[ConStrType, str]

    class Foo(BaseModel):
        a: ConStrKeyDict = {}

    assert Foo.model_json_schema() == {
        'title': 'Foo',
        'type': 'object',
        'properties': {
            'a': {'type': 'object', 'title': 'A', 'default': {}, 'patternProperties': {regex_str: {'type': 'string'}}}
        },
    }


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        # (ConstrainedBytes, {'title': 'A', 'type': 'string', 'format': 'binary'}),
        (
            conbytes(min_length=3, max_length=5),
            {'title': 'A', 'type': 'string', 'format': 'binary', 'minLength': 3, 'maxLength': 5},
        ),
    ],
)
def test_bytes_constrained_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': {}}, 'required': ['a']}
    base_schema['properties']['a'] = expected_schema

    assert Model.model_json_schema() == base_schema


def test_optional_dict():
    class Model(BaseModel):
        something: Optional[Dict[str, Any]] = None

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'something': {'anyOf': [{'type': 'object'}, {'type': 'null'}], 'default': None, 'title': 'Something'}
        },
    }

    assert Model().model_dump() == {'something': None}
    assert Model(something={'foo': 'Bar'}).model_dump() == {'something': {'foo': 'Bar'}}


def test_optional_validator():
    class Model(BaseModel):
        something: Optional[str] = None

        @field_validator('something')
        def check_something(cls, v):
            if v is not None and 'x' in v:
                raise ValueError('should not contain x')
            return v

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'something': {
                'title': 'Something',
                'anyOf': [{'type': 'string'}, {'type': 'null'}],
                'default': None,
            }
        },
    }

    assert Model().model_dump() == {'something': None}
    assert Model(something=None).model_dump() == {'something': None}
    assert Model(something='hello').model_dump() == {'something': 'hello'}
    with pytest.raises(ValidationError) as exc_info:
        Model(something='hellox')
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'error': 'should not contain x'},
            'input': 'hellox',
            'loc': ('something',),
            'msg': 'Value error, should not contain x',
            'type': 'value_error',
        }
    ]


def test_field_with_validator():
    class Model(BaseModel):
        something: Optional[int] = None

        @field_validator('something')
        def check_field(cls, v, info):
            return v

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'something': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'default': None, 'title': 'Something'}
        },
    }


def test_unparameterized_schema_generation():
    class FooList(BaseModel):
        d: List

    class BarList(BaseModel):
        d: list

    assert model_json_schema(FooList) == {
        'title': 'FooList',
        'type': 'object',
        'properties': {'d': {'items': {}, 'title': 'D', 'type': 'array'}},
        'required': ['d'],
    }

    foo_list_schema = model_json_schema(FooList)
    bar_list_schema = model_json_schema(BarList)
    bar_list_schema['title'] = 'FooList'  # to check for equality
    assert foo_list_schema == bar_list_schema

    class FooDict(BaseModel):
        d: Dict

    class BarDict(BaseModel):
        d: dict

    model_json_schema(Foo)
    assert model_json_schema(FooDict) == {
        'title': 'FooDict',
        'type': 'object',
        'properties': {'d': {'title': 'D', 'type': 'object'}},
        'required': ['d'],
    }

    foo_dict_schema = model_json_schema(FooDict)
    bar_dict_schema = model_json_schema(BarDict)
    bar_dict_schema['title'] = 'FooDict'  # to check for equality
    assert foo_dict_schema == bar_dict_schema


def test_known_model_optimization():
    class Dep(BaseModel):
        number: int

    class Model(BaseModel):
        dep: Dep
        dep_l: List[Dep]

    expected = {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'dep': {'$ref': '#/$defs/Dep'},
            'dep_l': {'title': 'Dep L', 'type': 'array', 'items': {'$ref': '#/$defs/Dep'}},
        },
        'required': ['dep', 'dep_l'],
        '$defs': {
            'Dep': {
                'title': 'Dep',
                'type': 'object',
                'properties': {'number': {'title': 'Number', 'type': 'integer'}},
                'required': ['number'],
            }
        },
    }

    assert Model.model_json_schema() == expected


def test_new_type_schema():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', str)

    class Model(BaseModel):
        a: a_type
        b: b_type
        c: c_type

    assert Model.model_json_schema() == {
        'properties': {
            'a': {'title': 'A', 'type': 'integer'},
            'b': {'title': 'B', 'type': 'integer'},
            'c': {'title': 'C', 'type': 'string'},
        },
        'required': ['a', 'b', 'c'],
        'title': 'Model',
        'type': 'object',
    }


def test_literal_schema():
    class Model(BaseModel):
        a: Literal[1]
        b: Literal['a']
        c: Literal['a', 1]
        d: Literal['a', Literal['b'], 1, 2]

    assert Model.model_json_schema() == {
        'properties': {
            'a': {'const': 1, 'title': 'A'},
            'b': {'const': 'a', 'title': 'B'},
            'c': {'enum': ['a', 1], 'title': 'C'},
            'd': {'enum': ['a', 'b', 1, 2], 'title': 'D'},
        },
        'required': ['a', 'b', 'c', 'd'],
        'title': 'Model',
        'type': 'object',
    }


def test_literal_enum():
    class MyEnum(str, Enum):
        FOO = 'foo'
        BAR = 'bar'

    class Model(BaseModel):
        kind: Literal[MyEnum.FOO]
        other: Literal[MyEnum.FOO, MyEnum.BAR]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'kind': {'const': 'foo', 'title': 'Kind'}, 'other': {'enum': ['foo', 'bar'], 'title': 'Other'}},
        'required': ['kind', 'other'],
    }


def test_color_type():
    class Model(BaseModel):
        color: Color

    model_schema = Model.model_json_schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'color': {'title': 'Color', 'type': 'string', 'format': 'color'}},
        'required': ['color'],
    }


def test_model_with_extra_forbidden():
    class Model(BaseModel):
        model_config = ConfigDict(extra='forbid')
        a: str

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'additionalProperties': False,
    }


@pytest.mark.parametrize(
    'annotation,kwargs,field_schema',
    [
        (int, dict(gt=0), {'title': 'A', 'exclusiveMinimum': 0, 'type': 'integer'}),
        (
            Optional[int],
            dict(gt=0),
            {'title': 'A', 'anyOf': [{'exclusiveMinimum': 0, 'type': 'integer'}, {'type': 'null'}]},
        ),
        (
            Tuple[Annotated[int, Field(gt=0)], ...],
            {},
            {'items': {'exclusiveMinimum': 0, 'type': 'integer'}, 'title': 'A', 'type': 'array'},
        ),
        (
            Tuple[Annotated[int, Field(gt=0)], Annotated[int, Field(gt=0)], Annotated[int, Field(gt=0)]],
            {},
            {
                'title': 'A',
                'type': 'array',
                'prefixItems': [
                    {'exclusiveMinimum': 0, 'type': 'integer'},
                    {'exclusiveMinimum': 0, 'type': 'integer'},
                    {'exclusiveMinimum': 0, 'type': 'integer'},
                ],
                'minItems': 3,
                'maxItems': 3,
            },
        ),
        (
            Union[Annotated[int, Field(gt=0)], Annotated[float, Field(gt=0)]],
            {},
            {
                'title': 'A',
                'anyOf': [{'exclusiveMinimum': 0, 'type': 'integer'}, {'exclusiveMinimum': 0, 'type': 'number'}],
            },
        ),
        (
            List[Annotated[int, Field(gt=0)]],
            {},
            {'title': 'A', 'type': 'array', 'items': {'exclusiveMinimum': 0, 'type': 'integer'}},
        ),
        (
            Dict[str, Annotated[int, Field(gt=0)]],
            {},
            {
                'title': 'A',
                'type': 'object',
                'additionalProperties': {'exclusiveMinimum': 0, 'type': 'integer'},
            },
        ),
        (
            Union[Annotated[str, Field(max_length=5)], Annotated[int, Field(gt=0)]],
            {},
            {'title': 'A', 'anyOf': [{'maxLength': 5, 'type': 'string'}, {'exclusiveMinimum': 0, 'type': 'integer'}]},
        ),
    ],
)
def test_enforced_constraints(annotation, kwargs, field_schema):
    class Model(BaseModel):
        a: annotation = Field(..., **kwargs)

    schema = Model.model_json_schema()
    # debug(schema['properties']['a'])
    assert schema['properties']['a'] == field_schema


def test_real_constraints():
    class Model1(BaseModel):
        model_config = ConfigDict(title='Test Model')
        foo: int = Field(..., gt=123)

    with pytest.raises(ValidationError, match='should be greater than 123'):
        Model1(foo=123)

    assert Model1(foo=124).model_dump() == {'foo': 124}

    assert Model1.model_json_schema() == {
        'title': 'Test Model',
        'type': 'object',
        'properties': {'foo': {'title': 'Foo', 'exclusiveMinimum': 123, 'type': 'integer'}},
        'required': ['foo'],
    }


def test_subfield_field_info():
    class MyModel(BaseModel):
        entries: Dict[str, List[int]]

    assert MyModel.model_json_schema() == {
        'title': 'MyModel',
        'type': 'object',
        'properties': {
            'entries': {
                'title': 'Entries',
                'type': 'object',
                'additionalProperties': {'type': 'array', 'items': {'type': 'integer'}},
            }
        },
        'required': ['entries'],
    }


def test_dataclass():
    @dataclass
    class Model:
        a: bool

    assert models_json_schema([(Model, 'validation')]) == (
        {(Model, 'validation'): 'Model'},
        {
            '$defs': {
                'Model': {
                    'title': 'Model',
                    'type': 'object',
                    'properties': {'a': {'title': 'A', 'type': 'boolean'}},
                    'required': ['a'],
                }
            }
        },
    )

    assert model_json_schema(Model) == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'boolean'}},
        'required': ['a'],
    }


def test_schema_attributes():
    class ExampleEnum(Enum):
        """This is a test description."""

        gt = 'GT'
        lt = 'LT'
        ge = 'GE'
        le = 'LE'
        max_length = 'ML'
        multiple_of = 'MO'
        regex = 'RE'

    class Example(BaseModel):
        example: ExampleEnum

    assert Example.model_json_schema() == {
        'title': 'Example',
        'type': 'object',
        'properties': {'example': {'$ref': '#/$defs/ExampleEnum'}},
        'required': ['example'],
        '$defs': {
            'ExampleEnum': {
                'title': 'ExampleEnum',
                'description': 'This is a test description.',
                'enum': ['GT', 'LT', 'GE', 'LE', 'ML', 'MO', 'RE'],
            }
        },
    }


def test_tuple_with_extra_schema():
    class MyTuple(Tuple[int, str]):
        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.tuple_positional_schema(
                [core_schema.int_schema(), core_schema.str_schema()], extra_schema=core_schema.int_schema()
            )

    class Model(BaseModel):
        x: MyTuple

    assert Model.model_json_schema() == {
        'properties': {
            'x': {
                'items': {'type': 'integer'},
                'minItems': 2,
                'prefixItems': [{'type': 'integer'}, {'type': 'string'}],
                'title': 'X',
                'type': 'array',
            }
        },
        'required': ['x'],
        'title': 'Model',
        'type': 'object',
    }


def test_path_modify_schema():
    class MyPath(Path):
        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return handler.generate_schema(Path)

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            schema = handler(core_schema)
            schema.update(foobar=123)
            return schema

    class Model(BaseModel):
        path1: Path
        path2: MyPath
        path3: List[MyPath]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'path1': {'title': 'Path1', 'type': 'string', 'format': 'path'},
            'path2': {'title': 'Path2', 'type': 'string', 'format': 'path', 'foobar': 123},
            'path3': {'title': 'Path3', 'type': 'array', 'items': {'type': 'string', 'format': 'path', 'foobar': 123}},
        },
        'required': ['path1', 'path2', 'path3'],
    }


def test_frozen_set():
    class Model(BaseModel):
        a: FrozenSet[int] = frozenset({1, 2, 3})
        b: FrozenSet = frozenset({1, 2, 3})
        c: frozenset = frozenset({1, 2, 3})
        d: frozenset = ...

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {
                'title': 'A',
                'default': [1, 2, 3],
                'type': 'array',
                'items': {'type': 'integer'},
                'uniqueItems': True,
            },
            'b': {'title': 'B', 'default': [1, 2, 3], 'type': 'array', 'items': {}, 'uniqueItems': True},
            'c': {'title': 'C', 'default': [1, 2, 3], 'type': 'array', 'items': {}, 'uniqueItems': True},
            'd': {'title': 'D', 'type': 'array', 'items': {}, 'uniqueItems': True},
        },
        'required': ['d'],
    }


def test_iterable():
    class Model(BaseModel):
        a: Iterable[int]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'array', 'items': {'type': 'integer'}}},
        'required': ['a'],
    }


def test_new_type():
    new_type = NewType('NewStr', str)

    class Model(BaseModel):
        a: new_type

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string'}},
        'required': ['a'],
    }


def test_multiple_models_with_same_name(create_module):
    module = create_module(
        # language=Python
        """
from pydantic import BaseModel


class ModelOne(BaseModel):
    class NestedModel(BaseModel):
        a: float

    nested: NestedModel


class ModelTwo(BaseModel):
    class NestedModel(BaseModel):
        b: float

    nested: NestedModel


class NestedModel(BaseModel):
    c: float
        """
    )

    # All validation
    keys_map, schema = models_json_schema(
        [(module.ModelOne, 'validation'), (module.ModelTwo, 'validation'), (module.NestedModel, 'validation')]
    )
    model_names = set(schema['$defs'].keys())
    expected_model_names = {
        'ModelOne',
        'ModelTwo',
        f'{module.__name__}__ModelOne__NestedModel',
        f'{module.__name__}__ModelTwo__NestedModel',
        f'{module.__name__}__NestedModel',
    }
    assert model_names == expected_model_names

    # Validation + serialization
    keys_map, schema = models_json_schema(
        [
            (module.ModelOne, 'validation'),
            (module.ModelTwo, 'validation'),
            (module.NestedModel, 'validation'),
            (module.ModelOne, 'serialization'),
            (module.ModelTwo, 'serialization'),
            (module.NestedModel, 'serialization'),
        ]
    )
    model_names = set(schema['$defs'].keys())
    expected_model_names = {
        'ModelOneInput',
        'ModelOneOutput',
        'ModelTwoInput',
        'ModelTwoOutput',
        f'{module.__name__}__ModelOne__NestedModelInput',
        f'{module.__name__}__ModelOne__NestedModelOutput',
        f'{module.__name__}__ModelTwo__NestedModelInput',
        f'{module.__name__}__ModelTwo__NestedModelOutput',
        f'{module.__name__}__NestedModelInput',
        f'{module.__name__}__NestedModelOutput',
    }
    assert model_names == expected_model_names


def test_multiple_enums_with_same_name(create_module):
    module_1 = create_module(
        # language=Python
        """
from enum import Enum

from pydantic import BaseModel


class MyEnum(str, Enum):
    a = 'a'
    b = 'b'
    c = 'c'


class MyModel(BaseModel):
    my_enum_1: MyEnum
        """
    )

    module_2 = create_module(
        # language=Python
        """
from enum import Enum

from pydantic import BaseModel


class MyEnum(str, Enum):
    d = 'd'
    e = 'e'
    f = 'f'


class MyModel(BaseModel):
    my_enum_2: MyEnum
        """
    )

    class Model(BaseModel):
        my_model_1: module_1.MyModel
        my_model_2: module_2.MyModel

    assert len(Model.model_json_schema()['$defs']) == 4
    assert set(Model.model_json_schema()['$defs']) == {
        f'{module_1.__name__}__MyEnum',
        f'{module_1.__name__}__MyModel',
        f'{module_2.__name__}__MyEnum',
        f'{module_2.__name__}__MyModel',
    }


def test_schema_for_generic_field():
    T = TypeVar('T')

    class GenModel(Generic[T]):
        def __init__(self, data: Any):
            self.data = data

        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v: Any):
            return v

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source: Any,
            handler: GetCoreSchemaHandler,
        ) -> core_schema.PlainValidatorFunctionSchema:
            source_args = getattr(source, '__args__', [Any])
            param = source_args[0]
            metadata = build_metadata_dict(js_functions=[lambda _c, h: h(handler.generate_schema(param))])
            return core_schema.general_plain_validator_function(
                GenModel,
                metadata=metadata,
            )

    class Model(BaseModel):
        data: GenModel[str]
        data1: GenModel

        model_config = dict(arbitrary_types_allowed=True)

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'data': {'type': 'string', 'title': 'Data'},
            'data1': {
                'title': 'Data1',
            },
        },
        'required': ['data', 'data1'],
    }

    class GenModelModified(GenModel, Generic[T]):
        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            field_schema = handler(core_schema)
            type = field_schema.pop('type', 'other')
            field_schema.update(anyOf=[{'type': type}, {'type': 'array', 'items': {'type': type}}])
            return field_schema

    class ModelModified(BaseModel):
        data: GenModelModified[str]
        data1: GenModelModified

        model_config = dict(arbitrary_types_allowed=True)

    assert ModelModified.model_json_schema() == {
        'title': 'ModelModified',
        'type': 'object',
        'properties': {
            'data': {'title': 'Data', 'anyOf': [{'type': 'string'}, {'type': 'array', 'items': {'type': 'string'}}]},
            'data1': {'title': 'Data1', 'anyOf': [{'type': 'other'}, {'type': 'array', 'items': {'type': 'other'}}]},
        },
        'required': ['data', 'data1'],
    }


def test_namedtuple_default():
    class Coordinates(NamedTuple):
        x: float
        y: float

    class LocationBase(BaseModel):
        coords: Coordinates = Coordinates(34, 42)

    assert LocationBase(coords=Coordinates(1, 2)).coords == Coordinates(1, 2)

    assert LocationBase.model_json_schema() == {
        'title': 'LocationBase',
        'type': 'object',
        'properties': {
            'coords': {
                'title': 'Coords',
                'default': [34, 42],
                'type': 'array',
                'prefixItems': [{'title': 'X', 'type': 'number'}, {'title': 'Y', 'type': 'number'}],
                'minItems': 2,
                'maxItems': 2,
            }
        },
    }


def test_namedtuple_modify_schema():
    class Coordinates(NamedTuple):
        x: float
        y: float

    class CustomCoordinates(Coordinates):
        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            schema = handler(source)
            schema['arguments_schema']['metadata']['pydantic_js_prefer_positional_arguments'] = False
            return schema

    class Location(BaseModel):
        coords: CustomCoordinates = CustomCoordinates(34, 42)

    assert Location.model_json_schema() == {
        'properties': {
            'coords': {
                'additionalProperties': False,
                'properties': {'x': {'title': 'X', 'type': 'number'}, 'y': {'title': 'Y', 'type': 'number'}},
                'required': ['x', 'y'],
                'title': 'Coords',
                'type': 'object',
                'default': [34, 42],
            }
        },
        'title': 'Location',
        'type': 'object',
    }


def test_advanced_generic_schema():  # noqa: C901
    T = TypeVar('T')
    K = TypeVar('K')

    class Gen(Generic[T]):
        def __init__(self, data: Any):
            self.data = data

        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v: Any):
            return v

        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            if hasattr(source, '__args__'):
                arg = source.__args__[0]

                def js_func(s, h):
                    # ignore the schema we were given and get a new CoreSchema
                    s = handler.generate_schema(Optional[arg])
                    return h(s)

                return core_schema.general_plain_validator_function(
                    Gen,
                    metadata={'pydantic_js_functions': [js_func]},
                )
            else:
                return handler(source)

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            try:
                field_schema = handler(core_schema)
            except PydanticInvalidForJsonSchema:
                field_schema = {}
            the_type = field_schema.pop('anyOf', [{'type': 'string'}])[0]
            field_schema.update(title='Gen title', anyOf=[the_type, {'type': 'array', 'items': the_type}])
            return field_schema

    class GenTwoParams(Generic[T, K]):
        def __init__(self, x: str, y: Any):
            self.x = x
            self.y = y

        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v: Any):
            return cls(*v)

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source: Any, handler: GetCoreSchemaHandler, **_kwargs: Any
        ) -> core_schema.CoreSchema:
            if hasattr(source, '__args__'):
                # the js_function ignores the schema we were given and gets a new Tuple CoreSchema
                metadata = build_metadata_dict(js_functions=[lambda _c, h: h(handler(Tuple[source.__args__]))])
                return core_schema.general_plain_validator_function(
                    GenTwoParams,
                    metadata=metadata,
                )
            return handler(source)

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            field_schema = handler(core_schema)
            field_schema.pop('minItems')
            field_schema.pop('maxItems')
            field_schema.update(examples='examples')
            return field_schema

    class CustomType(Enum):
        A = 'a'
        B = 'b'

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> core_schema.CoreSchema:
            json_schema = handler(core_schema)
            json_schema.update(title='CustomType title', type='string')
            return json_schema

    class Model(BaseModel):
        data0: Gen
        data1: Gen[CustomType] = Field(title='Data1 title', description='Data 1 description')
        data2: GenTwoParams[CustomType, UUID4] = Field(title='Data2 title', description='Data 2')
        # check Tuple because changes in code touch that type
        data3: Tuple
        data4: Tuple[CustomType]
        data5: Tuple[CustomType, str]

        model_config = {'arbitrary_types_allowed': True}

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        '$defs': {'CustomType': {'enum': ['a', 'b'], 'title': 'CustomType'}},
        'properties': {
            'data0': {
                'anyOf': [{'type': 'string'}, {'items': {'type': 'string'}, 'type': 'array'}],
                'title': 'Gen title',
            },
            'data1': {
                'anyOf': [{'$ref': '#/$defs/CustomType'}, {'items': {'$ref': '#/$defs/CustomType'}, 'type': 'array'}],
                'description': 'Data 1 description',
                'title': 'Data1 title',
            },
            'data2': {
                'description': 'Data 2',
                'examples': 'examples',
                'prefixItems': [{'$ref': '#/$defs/CustomType'}, {'format': 'uuid4', 'type': 'string'}],
                'title': 'Data2 title',
                'type': 'array',
            },
            'data3': {'items': {}, 'title': 'Data3', 'type': 'array'},
            'data4': {
                'maxItems': 1,
                'minItems': 1,
                'prefixItems': [{'$ref': '#/$defs/CustomType'}],
                'title': 'Data4',
                'type': 'array',
            },
            'data5': {
                'maxItems': 2,
                'minItems': 2,
                'prefixItems': [{'$ref': '#/$defs/CustomType'}, {'type': 'string'}],
                'title': 'Data5',
                'type': 'array',
            },
        },
        'required': ['data0', 'data1', 'data2', 'data3', 'data4', 'data5'],
        'title': 'Model',
        'type': 'object',
    }


def test_nested_generic():
    """
    Test a nested BaseModel that is also a Generic
    """

    class Ref(BaseModel, Generic[T]):
        uuid: str

        def resolve(self) -> T:
            ...

    class Model(BaseModel):
        ref: Ref['Model']

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        '$defs': {
            'Ref_Model_': {
                'title': 'Ref[Model]',
                'type': 'object',
                'properties': {
                    'uuid': {'title': 'Uuid', 'type': 'string'},
                },
                'required': ['uuid'],
            },
        },
        'properties': {
            'ref': {'$ref': '#/$defs/Ref_Model_'},
        },
        'required': ['ref'],
    }


def test_nested_generic_model():
    """
    Test a nested generic model
    """

    class Box(BaseModel, Generic[T]):
        uuid: str
        data: T

    class Model(BaseModel):
        box_str: Box[str]
        box_int: Box[int]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        '$defs': {
            'Box_str_': Box[str].model_json_schema(),
            'Box_int_': Box[int].model_json_schema(),
        },
        'properties': {
            'box_str': {'$ref': '#/$defs/Box_str_'},
            'box_int': {'$ref': '#/$defs/Box_int_'},
        },
        'required': ['box_str', 'box_int'],
    }


def test_complex_nested_generic():
    """
    Handle a union of a generic.
    """

    class Ref(BaseModel, Generic[T]):
        uuid: str

        def resolve(self) -> T:
            ...

    class Model(BaseModel):
        uuid: str
        model: Union[Ref['Model'], 'Model']

        def resolve(self) -> 'Model':
            ...

    Model.model_rebuild()

    assert Model.model_json_schema() == {
        '$defs': {
            'Model': {
                'title': 'Model',
                'type': 'object',
                'properties': {
                    'uuid': {'title': 'Uuid', 'type': 'string'},
                    'model': {
                        'title': 'Model',
                        'anyOf': [
                            {'$ref': '#/$defs/Ref_Model_'},
                            {'$ref': '#/$defs/Model'},
                        ],
                    },
                },
                'required': ['uuid', 'model'],
            },
            'Ref_Model_': {
                'title': 'Ref[Model]',
                'type': 'object',
                'properties': {'uuid': {'title': 'Uuid', 'type': 'string'}},
                'required': ['uuid'],
            },
        },
        'allOf': [{'$ref': '#/$defs/Model'}],
    }


def test_modify_schema_dict_keys() -> None:
    class MyType:
        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return {'test': 'passed'}

    class MyModel(BaseModel):
        my_field: Dict[str, MyType]

        model_config = dict(arbitrary_types_allowed=True)

    assert MyModel.model_json_schema() == {
        'properties': {
            'my_field': {'additionalProperties': {'test': 'passed'}, 'title': 'My Field', 'type': 'object'}  # <----
        },
        'required': ['my_field'],
        'title': 'MyModel',
        'type': 'object',
    }


def test_remove_anyof_redundancy() -> None:
    class A:
        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return handler({'type': 'str'})

    class B:
        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return handler({'type': 'str'})

    class MyModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        # Union of two objects should give a JSON with an `anyOf` field, but in this case
        # since the fields are the same, the `anyOf` is removed.
        field: Union[A, B]

    assert MyModel.model_json_schema() == {
        'properties': {'field': {'title': 'Field', 'type': 'string'}},
        'required': ['field'],
        'title': 'MyModel',
        'type': 'object',
    }


def test_discriminated_union():
    class Cat(BaseModel):
        pet_type: Literal['cat']

    class Dog(BaseModel):
        pet_type: Literal['dog']

    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']

    class Model(BaseModel):
        pet: Union[Cat, Dog, Lizard] = Field(..., discriminator='pet_type')

    assert Model.model_json_schema() == {
        '$defs': {
            'Cat': {
                'properties': {'pet_type': {'const': 'cat', 'title': 'Pet Type'}},
                'required': ['pet_type'],
                'title': 'Cat',
                'type': 'object',
            },
            'Dog': {
                'properties': {'pet_type': {'const': 'dog', 'title': 'Pet Type'}},
                'required': ['pet_type'],
                'title': 'Dog',
                'type': 'object',
            },
            'Lizard': {
                'properties': {'pet_type': {'enum': ['reptile', 'lizard'], 'title': 'Pet Type'}},
                'required': ['pet_type'],
                'title': 'Lizard',
                'type': 'object',
            },
        },
        'properties': {
            'pet': {
                'discriminator': {
                    'mapping': {
                        'cat': '#/$defs/Cat',
                        'dog': '#/$defs/Dog',
                        'lizard': '#/$defs/Lizard',
                        'reptile': '#/$defs/Lizard',
                    },
                    'propertyName': 'pet_type',
                },
                'oneOf': [
                    {'$ref': '#/$defs/Cat'},
                    {'$ref': '#/$defs/Dog'},
                    {'$ref': '#/$defs/Lizard'},
                ],
                'title': 'Pet',
            }
        },
        'required': ['pet'],
        'title': 'Model',
        'type': 'object',
    }


def test_discriminated_annotated_union():
    class Cat(BaseModel):
        pet_type: Literal['cat']

    class Dog(BaseModel):
        pet_type: Literal['dog']

    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']

    class Model(BaseModel):
        pet: Annotated[Union[Cat, Dog, Lizard], Field(..., discriminator='pet_type')]

    assert Model.model_json_schema() == {
        '$defs': {
            'Cat': {
                'properties': {'pet_type': {'const': 'cat', 'title': 'Pet Type'}},
                'required': ['pet_type'],
                'title': 'Cat',
                'type': 'object',
            },
            'Dog': {
                'properties': {'pet_type': {'const': 'dog', 'title': 'Pet Type'}},
                'required': ['pet_type'],
                'title': 'Dog',
                'type': 'object',
            },
            'Lizard': {
                'properties': {'pet_type': {'enum': ['reptile', 'lizard'], 'title': 'Pet Type'}},
                'required': ['pet_type'],
                'title': 'Lizard',
                'type': 'object',
            },
        },
        'properties': {
            'pet': {
                'discriminator': {
                    'mapping': {
                        'cat': '#/$defs/Cat',
                        'dog': '#/$defs/Dog',
                        'lizard': '#/$defs/Lizard',
                        'reptile': '#/$defs/Lizard',
                    },
                    'propertyName': 'pet_type',
                },
                'oneOf': [
                    {'$ref': '#/$defs/Cat'},
                    {'$ref': '#/$defs/Dog'},
                    {'$ref': '#/$defs/Lizard'},
                ],
                'title': 'Pet',
            }
        },
        'required': ['pet'],
        'title': 'Model',
        'type': 'object',
    }


def test_nested_discriminated_union():
    class BlackCatWithHeight(BaseModel):
        color: Literal['black']
        info: Literal['height']
        height: float

    class BlackCatWithWeight(BaseModel):
        color: Literal['black']
        info: Literal['weight']
        weight: float

    BlackCat = Annotated[Union[BlackCatWithHeight, BlackCatWithWeight], Field(discriminator='info')]

    class WhiteCat(BaseModel):
        color: Literal['white']
        white_cat_info: str

    class Cat(BaseModel):
        pet: Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

    assert Cat.model_json_schema() == {
        '$defs': {
            'BlackCatWithHeight': {
                'properties': {
                    'color': {'const': 'black', 'title': 'Color'},
                    'height': {'title': 'Height', 'type': 'number'},
                    'info': {'const': 'height', 'title': 'Info'},
                },
                'required': ['color', 'info', 'height'],
                'title': 'BlackCatWithHeight',
                'type': 'object',
            },
            'BlackCatWithWeight': {
                'properties': {
                    'color': {'const': 'black', 'title': 'Color'},
                    'info': {'const': 'weight', 'title': 'Info'},
                    'weight': {'title': 'Weight', 'type': 'number'},
                },
                'required': ['color', 'info', 'weight'],
                'title': 'BlackCatWithWeight',
                'type': 'object',
            },
            'WhiteCat': {
                'properties': {
                    'color': {'const': 'white', 'title': 'Color'},
                    'white_cat_info': {'title': 'White Cat Info', 'type': 'string'},
                },
                'required': ['color', 'white_cat_info'],
                'title': 'WhiteCat',
                'type': 'object',
            },
        },
        'properties': {
            'pet': {
                'discriminator': {
                    'mapping': {
                        'black': {
                            'discriminator': {
                                'mapping': {
                                    'height': '#/$defs/BlackCatWithHeight',
                                    'weight': '#/$defs/BlackCatWithWeight',
                                },
                                'propertyName': 'info',
                            },
                            'oneOf': [{'$ref': '#/$defs/BlackCatWithHeight'}, {'$ref': '#/$defs/BlackCatWithWeight'}],
                        },
                        'white': '#/$defs/WhiteCat',
                    },
                    'propertyName': 'color',
                },
                'oneOf': [
                    {
                        'discriminator': {
                            'mapping': {'height': '#/$defs/BlackCatWithHeight', 'weight': '#/$defs/BlackCatWithWeight'},
                            'propertyName': 'info',
                        },
                        'oneOf': [{'$ref': '#/$defs/BlackCatWithHeight'}, {'$ref': '#/$defs/BlackCatWithWeight'}],
                    },
                    {'$ref': '#/$defs/WhiteCat'},
                ],
                'title': 'Pet',
            }
        },
        'required': ['pet'],
        'title': 'Cat',
        'type': 'object',
    }


def test_deeper_nested_discriminated_annotated_union():
    class BlackCatWithHeight(BaseModel):
        pet_type: Literal['cat']
        color: Literal['black']
        info: Literal['height']
        black_infos: str

    class BlackCatWithWeight(BaseModel):
        pet_type: Literal['cat']
        color: Literal['black']
        info: Literal['weight']
        black_infos: str

    BlackCat = Annotated[Union[BlackCatWithHeight, BlackCatWithWeight], Field(discriminator='info')]

    class WhiteCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['white']
        white_infos: str

    Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

    class Dog(BaseModel):
        pet_type: Literal['dog']
        dog_name: str

    Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]

    class Model(BaseModel):
        pet: Pet
        number: int

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        '$defs': {
            'BlackCatWithHeight': {
                'properties': {
                    'black_infos': {'title': 'Black Infos', 'type': 'string'},
                    'color': {'const': 'black', 'title': 'Color'},
                    'info': {'const': 'height', 'title': 'Info'},
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                },
                'required': ['pet_type', 'color', 'info', 'black_infos'],
                'title': 'BlackCatWithHeight',
                'type': 'object',
            },
            'BlackCatWithWeight': {
                'properties': {
                    'black_infos': {'title': 'Black Infos', 'type': 'string'},
                    'color': {'const': 'black', 'title': 'Color'},
                    'info': {'const': 'weight', 'title': 'Info'},
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                },
                'required': ['pet_type', 'color', 'info', 'black_infos'],
                'title': 'BlackCatWithWeight',
                'type': 'object',
            },
            'Dog': {
                'properties': {
                    'dog_name': {'title': 'Dog Name', 'type': 'string'},
                    'pet_type': {'const': 'dog', 'title': 'Pet Type'},
                },
                'required': ['pet_type', 'dog_name'],
                'title': 'Dog',
                'type': 'object',
            },
            'WhiteCat': {
                'properties': {
                    'color': {'const': 'white', 'title': 'Color'},
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                    'white_infos': {'title': 'White Infos', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'white_infos'],
                'title': 'WhiteCat',
                'type': 'object',
            },
        },
        'properties': {
            'number': {'title': 'Number', 'type': 'integer'},
            'pet': {
                'discriminator': {
                    'mapping': {
                        'cat': {
                            'discriminator': {
                                'mapping': {
                                    'black': {
                                        'discriminator': {
                                            'mapping': {
                                                'height': '#/$defs/BlackCatWithHeight',
                                                'weight': '#/$defs/BlackCatWithWeight',
                                            },
                                            'propertyName': 'info',
                                        },
                                        'oneOf': [
                                            {'$ref': '#/$defs/BlackCatWithHeight'},
                                            {'$ref': '#/$defs/BlackCatWithWeight'},
                                        ],
                                    },
                                    'white': '#/$defs/WhiteCat',
                                },
                                'propertyName': 'color',
                            },
                            'oneOf': [
                                {
                                    'discriminator': {
                                        'mapping': {
                                            'height': '#/$defs/BlackCatWithHeight',
                                            'weight': '#/$defs/BlackCatWithWeight',
                                        },
                                        'propertyName': 'info',
                                    },
                                    'oneOf': [
                                        {'$ref': '#/$defs/BlackCatWithHeight'},
                                        {'$ref': '#/$defs/BlackCatWithWeight'},
                                    ],
                                },
                                {'$ref': '#/$defs/WhiteCat'},
                            ],
                        },
                        'dog': '#/$defs/Dog',
                    },
                    'propertyName': 'pet_type',
                },
                'oneOf': [
                    {
                        'discriminator': {
                            'mapping': {
                                'black': {
                                    'discriminator': {
                                        'mapping': {
                                            'height': '#/$defs/BlackCatWithHeight',
                                            'weight': '#/$defs/BlackCatWithWeight',
                                        },
                                        'propertyName': 'info',
                                    },
                                    'oneOf': [
                                        {'$ref': '#/$defs/BlackCatWithHeight'},
                                        {'$ref': '#/$defs/BlackCatWithWeight'},
                                    ],
                                },
                                'white': '#/$defs/WhiteCat',
                            },
                            'propertyName': 'color',
                        },
                        'oneOf': [
                            {
                                'discriminator': {
                                    'mapping': {
                                        'height': '#/$defs/BlackCatWithHeight',
                                        'weight': '#/$defs/BlackCatWithWeight',
                                    },
                                    'propertyName': 'info',
                                },
                                'oneOf': [
                                    {'$ref': '#/$defs/BlackCatWithHeight'},
                                    {'$ref': '#/$defs/BlackCatWithWeight'},
                                ],
                            },
                            {'$ref': '#/$defs/WhiteCat'},
                        ],
                    },
                    {'$ref': '#/$defs/Dog'},
                ],
                'title': 'Pet',
            },
        },
        'required': ['pet', 'number'],
        'title': 'Model',
        'type': 'object',
    }


def test_discriminated_annotated_union_literal_enum():
    class PetType(Enum):
        cat = 'cat'
        dog = 'dog'

    class PetColor(str, Enum):
        black = 'black'
        white = 'white'

    class PetInfo(Enum):
        height = 0
        weight = 1

    class BlackCatWithHeight(BaseModel):
        pet_type: Literal[PetType.cat]
        color: Literal[PetColor.black]
        info: Literal[PetInfo.height]
        black_infos: str

    class BlackCatWithWeight(BaseModel):
        pet_type: Literal[PetType.cat]
        color: Literal[PetColor.black]
        info: Literal[PetInfo.weight]
        black_infos: str

    BlackCat = Annotated[Union[BlackCatWithHeight, BlackCatWithWeight], Field(discriminator='info')]

    class WhiteCat(BaseModel):
        pet_type: Literal[PetType.cat]
        color: Literal[PetColor.white]
        white_infos: str

    Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

    class Dog(BaseModel):
        pet_type: Literal[PetType.dog]
        dog_name: str

    Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]

    class Model(BaseModel):
        pet: Pet
        number: int

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        '$defs': {
            'BlackCatWithHeight': {
                'properties': {
                    'black_infos': {'title': 'Black Infos', 'type': 'string'},
                    'color': {'const': 'black', 'title': 'Color'},
                    'info': {'const': 0, 'title': 'Info'},
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                },
                'required': ['pet_type', 'color', 'info', 'black_infos'],
                'title': 'BlackCatWithHeight',
                'type': 'object',
            },
            'BlackCatWithWeight': {
                'properties': {
                    'black_infos': {'title': 'Black Infos', 'type': 'string'},
                    'color': {'const': 'black', 'title': 'Color'},
                    'info': {'const': 1, 'title': 'Info'},
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                },
                'required': ['pet_type', 'color', 'info', 'black_infos'],
                'title': 'BlackCatWithWeight',
                'type': 'object',
            },
            'Dog': {
                'properties': {
                    'dog_name': {'title': 'Dog Name', 'type': 'string'},
                    'pet_type': {'const': 'dog', 'title': 'Pet Type'},
                },
                'required': ['pet_type', 'dog_name'],
                'title': 'Dog',
                'type': 'object',
            },
            'WhiteCat': {
                'properties': {
                    'color': {'const': 'white', 'title': 'Color'},
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                    'white_infos': {'title': 'White Infos', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'white_infos'],
                'title': 'WhiteCat',
                'type': 'object',
            },
        },
        'properties': {
            'number': {'title': 'Number', 'type': 'integer'},
            'pet': {
                'discriminator': {
                    'mapping': {
                        'cat': {
                            'discriminator': {
                                'mapping': {
                                    'black': {
                                        'discriminator': {
                                            'mapping': {
                                                '0': '#/$defs/BlackCatWithHeight',
                                                '1': '#/$defs/BlackCatWithWeight',
                                            },
                                            'propertyName': 'info',
                                        },
                                        'oneOf': [
                                            {'$ref': '#/$defs/BlackCatWithHeight'},
                                            {'$ref': '#/$defs/BlackCatWithWeight'},
                                        ],
                                    },
                                    'white': '#/$defs/WhiteCat',
                                },
                                'propertyName': 'color',
                            },
                            'oneOf': [
                                {
                                    'discriminator': {
                                        'mapping': {
                                            '0': '#/$defs/BlackCatWithHeight',
                                            '1': '#/$defs/BlackCatWithWeight',
                                        },
                                        'propertyName': 'info',
                                    },
                                    'oneOf': [
                                        {'$ref': '#/$defs/BlackCatWithHeight'},
                                        {'$ref': '#/$defs/BlackCatWithWeight'},
                                    ],
                                },
                                {'$ref': '#/$defs/WhiteCat'},
                            ],
                        },
                        'dog': '#/$defs/Dog',
                    },
                    'propertyName': 'pet_type',
                },
                'oneOf': [
                    {
                        'discriminator': {
                            'mapping': {
                                'black': {
                                    'discriminator': {
                                        'mapping': {
                                            '0': '#/$defs/BlackCatWithHeight',
                                            '1': '#/$defs/BlackCatWithWeight',
                                        },
                                        'propertyName': 'info',
                                    },
                                    'oneOf': [
                                        {'$ref': '#/$defs/BlackCatWithHeight'},
                                        {'$ref': '#/$defs/BlackCatWithWeight'},
                                    ],
                                },
                                'white': '#/$defs/WhiteCat',
                            },
                            'propertyName': 'color',
                        },
                        'oneOf': [
                            {
                                'discriminator': {
                                    'mapping': {'0': '#/$defs/BlackCatWithHeight', '1': '#/$defs/BlackCatWithWeight'},
                                    'propertyName': 'info',
                                },
                                'oneOf': [
                                    {'$ref': '#/$defs/BlackCatWithHeight'},
                                    {'$ref': '#/$defs/BlackCatWithWeight'},
                                ],
                            },
                            {'$ref': '#/$defs/WhiteCat'},
                        ],
                    },
                    {'$ref': '#/$defs/Dog'},
                ],
                'title': 'Pet',
            },
        },
        'required': ['pet', 'number'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.xfail(reason='json schema generation for tagged unions is fundamentally incompatible with references')
def test_alias_same():
    class Cat(BaseModel):
        pet_type: Literal['cat'] = Field(alias='typeOfPet')
        c: str

    class Dog(BaseModel):
        pet_type: Literal['dog'] = Field(alias='typeOfPet')
        d: str

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        '$defs': {
            'Cat': {
                'properties': {
                    'c': {'title': 'C', 'type': 'string'},
                    'typeOfPet': {'const': 'cat', 'title': 'Typeofpet'},
                },
                'required': ['typeOfPet', 'c'],
                'title': 'Cat',
                'type': 'object',
            },
            'Dog': {
                'properties': {
                    'd': {'title': 'D', 'type': 'string'},
                    'typeOfPet': {'const': 'dog', 'title': 'Typeofpet'},
                },
                'required': ['typeOfPet', 'd'],
                'title': 'Dog',
                'type': 'object',
            },
        },
        'properties': {
            'number': {'title': 'Number', 'type': 'integer'},
            'pet': {
                'oneOf': [{'$ref': '#/$defs/Cat'}, {'$ref': '#/$defs/Dog'}],
                'title': 'Pet',
                'discriminator': 'something',
            },
        },
        'required': ['pet', 'number'],
        'title': 'Model',
        'type': 'object',
    }


def test_nested_python_dataclasses():
    """
    Test schema generation for nested python dataclasses
    """

    from dataclasses import dataclass as python_dataclass

    @python_dataclass
    class ChildModel:
        name: str

    @python_dataclass
    class NestedModel:
        """
        Custom description
        """

        # Note: the Custom description will not be preserved as this is a vanilla dataclass
        # This is the same behavior as in v1
        child: List[ChildModel]

    assert model_json_schema(dataclass(NestedModel)) == {
        '$defs': {
            'ChildModel': {
                'properties': {'name': {'title': 'Name', 'type': 'string'}},
                'required': ['name'],
                'title': 'ChildModel',
                'type': 'object',
            }
        },
        'properties': {'child': {'items': {'$ref': '#/$defs/ChildModel'}, 'title': 'Child', 'type': 'array'}},
        'required': ['child'],
        'title': 'NestedModel',
        'type': 'object',
    }


def test_discriminated_union_in_list():
    class BlackCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['black']
        black_name: str

    class WhiteCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['white']
        white_name: str

    Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

    class Dog(BaseModel):
        pet_type: Literal['dog']
        name: str

    Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]

    class Model(BaseModel):
        pets: Pet
        n: int

    assert Model.model_json_schema() == {
        '$defs': {
            'BlackCat': {
                'properties': {
                    'black_name': {'title': 'Black Name', 'type': 'string'},
                    'color': {'const': 'black', 'title': 'Color'},
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                },
                'required': ['pet_type', 'color', 'black_name'],
                'title': 'BlackCat',
                'type': 'object',
            },
            'Dog': {
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'pet_type': {'const': 'dog', 'title': 'Pet Type'},
                },
                'required': ['pet_type', 'name'],
                'title': 'Dog',
                'type': 'object',
            },
            'WhiteCat': {
                'properties': {
                    'color': {'const': 'white', 'title': 'Color'},
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                    'white_name': {'title': 'White Name', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'white_name'],
                'title': 'WhiteCat',
                'type': 'object',
            },
        },
        'properties': {
            'n': {'title': 'N', 'type': 'integer'},
            'pets': {
                'discriminator': {
                    'mapping': {
                        'cat': {
                            'discriminator': {
                                'mapping': {'black': '#/$defs/BlackCat', 'white': '#/$defs/WhiteCat'},
                                'propertyName': 'color',
                            },
                            'oneOf': [{'$ref': '#/$defs/BlackCat'}, {'$ref': '#/$defs/WhiteCat'}],
                        },
                        'dog': '#/$defs/Dog',
                    },
                    'propertyName': 'pet_type',
                },
                'oneOf': [
                    {
                        'discriminator': {
                            'mapping': {'black': '#/$defs/BlackCat', 'white': '#/$defs/WhiteCat'},
                            'propertyName': 'color',
                        },
                        'oneOf': [{'$ref': '#/$defs/BlackCat'}, {'$ref': '#/$defs/WhiteCat'}],
                    },
                    {'$ref': '#/$defs/Dog'},
                ],
                'title': 'Pets',
            },
        },
        'required': ['pets', 'n'],
        'title': 'Model',
        'type': 'object',
    }


def test_model_with_type_attributes():
    class Foo:
        a: float

    class Bar(BaseModel):
        b: int

    class Baz(BaseModel):
        a: Type[Foo]
        b: Type[Bar]

    assert Baz.model_json_schema() == {
        'title': 'Baz',
        'type': 'object',
        'properties': {'a': {'title': 'A'}, 'b': {'title': 'B'}},
        'required': ['a', 'b'],
    }


@pytest.mark.parametrize('secret_cls', [SecretStr, SecretBytes])
@pytest.mark.parametrize(
    'field_kw,schema_kw',
    [
        # [{}, {}],
        [{'min_length': 6}, {'minLength': 6}],
        [{'max_length': 10}, {'maxLength': 10}],
        [{'min_length': 6, 'max_length': 10}, {'minLength': 6, 'maxLength': 10}],
    ],
    ids=['min-constraint', 'max-constraint', 'min-max-constraints'],
)
def test_secrets_schema(secret_cls, field_kw, schema_kw):
    class Foobar(BaseModel):
        password: secret_cls = Field(**field_kw)

    assert Foobar.model_json_schema() == {
        'title': 'Foobar',
        'type': 'object',
        'properties': {
            'password': {'title': 'Password', 'type': 'string', 'writeOnly': True, 'format': 'password', **schema_kw}
        },
        'required': ['password'],
    }


def test_override_generate_json_schema():
    class MyGenerateJsonSchema(GenerateJsonSchema):
        def generate(self, schema, mode='validation'):
            json_schema = super().generate(schema, mode=mode)
            json_schema['$schema'] = self.schema_dialect
            return json_schema

    class MyBaseModel(BaseModel):
        @classmethod
        def model_json_schema(
            cls,
            by_alias: bool = True,
            ref_template: str = DEFAULT_REF_TEMPLATE,
            schema_generator: Type[GenerateJsonSchema] = MyGenerateJsonSchema,
            mode='validation',
        ) -> Dict[str, Any]:
            return super().model_json_schema(by_alias, ref_template, schema_generator, mode)

    class MyModel(MyBaseModel):
        x: int

    assert MyModel.model_json_schema() == {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        'properties': {'x': {'title': 'X', 'type': 'integer'}},
        'required': ['x'],
        'title': 'MyModel',
        'type': 'object',
    }


def test_generate_json_schema_generate_twice():
    generator = GenerateJsonSchema()

    class Model(BaseModel):
        title: str

    generator.generate(Model.__pydantic_core_schema__)

    with pytest.raises(
        PydanticUserError,
        match=re.escape(
            'This JSON schema generator has already been used to generate a JSON schema. '
            'You must create a new instance of GenerateJsonSchema to generate a new JSON schema.'
        ),
    ):
        generator.generate(Model.__pydantic_core_schema__)

    generator = GenerateJsonSchema()
    generator.generate_definitions([(Model, 'validation', Model.__pydantic_core_schema__)])

    with pytest.raises(
        PydanticUserError,
        match=re.escape(
            'This JSON schema generator has already been used to generate a JSON schema. '
            'You must create a new instance of GenerateJsonSchema to generate a new JSON schema.'
        ),
    ):
        generator.generate_definitions([(Model, 'validation', Model.__pydantic_core_schema__)])


def test_nested_default_json_schema():
    class InnerModel(BaseModel):
        foo: str = 'bar'
        baz: str = Field(default='foobar', alias='my_alias')

    class OuterModel(BaseModel):
        nested_field: InnerModel = InnerModel()

    assert OuterModel.model_json_schema() == {
        '$defs': {
            'InnerModel': {
                'properties': {
                    'foo': {'default': 'bar', 'title': 'Foo', 'type': 'string'},
                    'my_alias': {'default': 'foobar', 'title': 'My Alias', 'type': 'string'},
                },
                'title': 'InnerModel',
                'type': 'object',
            }
        },
        'properties': {
            'nested_field': {'allOf': [{'$ref': '#/$defs/InnerModel'}], 'default': {'my_alias': 'foobar', 'foo': 'bar'}}
        },
        'title': 'OuterModel',
        'type': 'object',
    }


@pytest.mark.xfail(
    reason=(
        'We are calling __get_pydantic_json_schema__ too many times.'
        ' The second time we analyze a model we get the CoreSchema from __pydantic_core_schema__.'
        ' But then we proceed to append to the metadata json schema functions.'
    )
)
def test_get_pydantic_core_schema_calls() -> None:
    """Verify when/how many times `__get_pydantic_core_schema__` gets called"""

    calls: List[str] = []

    class Model(BaseModel):
        @classmethod
        def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            calls.append('Model::before')
            json_schema = handler(schema)
            calls.append('Model::after')
            return json_schema

    schema = Model.model_json_schema()
    expected: JsonSchemaValue = {'type': 'object', 'properties': {}, 'title': 'Model'}

    assert schema == expected
    assert calls == ['Model::before', 'Model::after']

    calls.clear()

    class CustomAnnotation(NamedTuple):
        name: str

        def __get_pydantic_json_schema__(self, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            calls.append(f'CustomAnnotation({self.name})::before')
            json_schema = handler(schema)
            calls.append(f'CustomAnnotation({self.name})::after')
            return json_schema

    AnnotatedType = Annotated[str, CustomAnnotation('foo'), CustomAnnotation('bar')]

    schema = TypeAdapter(AnnotatedType).json_schema()
    expected: JsonSchemaValue = {'type': 'string'}

    assert schema == expected
    assert calls == [
        'CustomAnnotation(bar)::before',
        'CustomAnnotation(foo)::before',
        'CustomAnnotation(foo)::after',
        'CustomAnnotation(bar)::after',
    ]

    calls.clear()

    class OuterModel(BaseModel):
        x: Model

        @classmethod
        def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            calls.append('OuterModel::before')
            json_schema = handler(schema)
            calls.append('OuterModel::after')
            return json_schema

    schema = OuterModel.model_json_schema()
    expected: JsonSchemaValue = {
        'type': 'object',
        'properties': {'x': {'$ref': '#/$defs/Model'}},
        'required': ['x'],
        'title': 'OuterModel',
        '$defs': {'Model': {'type': 'object', 'properties': {}, 'title': 'Model'}},
    }

    assert schema == expected
    assert calls == [
        'OuterModel::before',
        'Model::before',
        'Model::after',
        'OuterModel::after',
    ]

    calls.clear()

    AnnotatedModel = Annotated[Model, CustomAnnotation('foo')]

    schema = TypeAdapter(AnnotatedModel).json_schema()
    expected: JsonSchemaValue = {}

    assert schema == expected
    assert calls == [
        'CustomAnnotation(foo)::before',
        'Model::before',
        'Model::after',
        'CustomAnnotation(foo)::after',
    ]

    calls.clear()

    class OuterModelWithAnnotatedField(BaseModel):
        x: AnnotatedModel

    schema = OuterModelWithAnnotatedField.model_json_schema()
    expected: JsonSchemaValue = {
        'type': 'object',
        'properties': {'x': {'$ref': '#/$defs/Model'}},
        'required': ['x'],
        'title': 'OuterModel',
        '$defs': {'Model': {'type': 'object', 'properties': {}, 'title': 'Model'}},
    }

    assert schema == expected
    assert calls == [
        'OuterModel::before',
        'CustomAnnotation(foo)::before',
        'Model::before',
        'Model::after',
        'CustomAnnotation(foo)::after',
        'OuterModel::after',
    ]

    calls.clear()


def test_annotated_get_json_schema() -> None:
    calls: List[int] = []

    class CustomType(str):
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            return handler(str)

        @classmethod
        def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            calls.append(1)
            json_schema = handler(schema)
            return json_schema

    TypeAdapter(Annotated[CustomType, 123]).json_schema()

    assert sum(calls) == 1


def test_model_with_strict_mode():
    class Model(BaseModel):
        model_config = ConfigDict(strict=True)

        a: str

    assert Model.model_json_schema() == {
        'properties': {'a': {'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }


def test_model_with_schema_extra():
    class Model(BaseModel):
        a: str

        model_config = dict(json_schema_extra={'examples': [{'a': 'Foo'}]})

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'examples': [{'a': 'Foo'}],
    }


def test_model_with_schema_extra_callable():
    class Model(BaseModel):
        name: str = None

        @staticmethod
        def json_schema_extra(schema, model_class):
            schema.pop('properties')
            schema['type'] = 'override'
            assert model_class is Model

        model_config = dict(json_schema_extra=json_schema_extra)

    assert Model.model_json_schema() == {'title': 'Model', 'type': 'override'}


def test_model_with_schema_extra_callable_no_model_class():
    class Model(BaseModel):
        name: str = None

        @classmethod
        def json_schema_extra(cls, schema):
            schema.pop('properties')
            schema['type'] = 'override'

        model_config = dict(json_schema_extra=json_schema_extra)

    assert Model.model_json_schema() == {'title': 'Model', 'type': 'override'}


def test_model_with_schema_extra_callable_config_class():
    with pytest.warns(DeprecationWarning, match='use ConfigDict instead'):

        class Model(BaseModel):
            name: str = None

            class Config:
                @staticmethod
                def json_schema_extra(schema, model_class):
                    schema.pop('properties')
                    schema['type'] = 'override'
                    assert model_class is Model

    assert Model.model_json_schema() == {'title': 'Model', 'type': 'override'}


def test_model_with_schema_extra_callable_no_model_class_config_class():
    with pytest.warns(DeprecationWarning):

        class Model(BaseModel):
            name: str = None

            class Config:
                @staticmethod
                def json_schema_extra(schema):
                    schema.pop('properties')
                    schema['type'] = 'override'

        assert Model.model_json_schema() == {'title': 'Model', 'type': 'override'}


def test_model_with_schema_extra_callable_classmethod():
    with pytest.warns(DeprecationWarning):

        class Model(BaseModel):
            name: str = None

            class Config:
                type = 'foo'

                @classmethod
                def json_schema_extra(cls, schema, model_class):
                    schema.pop('properties')
                    schema['type'] = cls.type
                    assert model_class is Model

        assert Model.model_json_schema() == {'title': 'Model', 'type': 'foo'}


def test_model_with_schema_extra_callable_instance_method():
    with pytest.warns(DeprecationWarning):

        class Model(BaseModel):
            name: str = None

            class Config:
                def json_schema_extra(schema, model_class):
                    schema.pop('properties')
                    schema['type'] = 'override'
                    assert model_class is Model

        assert Model.model_json_schema() == {'title': 'Model', 'type': 'override'}


def test_serialization_validation_interaction():
    class Inner(BaseModel):
        x: Json[int]

    class Outer(BaseModel):
        inner: Inner

    _, v_schema = models_json_schema([(Outer, 'validation')])
    assert v_schema == {
        '$defs': {
            'Inner': {
                'properties': {'x': {'format': 'json-string', 'title': 'X', 'type': 'string'}},
                'required': ['x'],
                'title': 'Inner',
                'type': 'object',
            },
            'Outer': {
                'properties': {'inner': {'$ref': '#/$defs/Inner'}},
                'required': ['inner'],
                'title': 'Outer',
                'type': 'object',
            },
        }
    }

    _, s_schema = models_json_schema([(Outer, 'serialization')])
    assert s_schema == {
        '$defs': {
            'Inner': {
                'properties': {'x': {'title': 'X', 'type': 'integer'}},
                'required': ['x'],
                'title': 'Inner',
                'type': 'object',
            },
            'Outer': {
                'properties': {'inner': {'$ref': '#/$defs/Inner'}},
                'required': ['inner'],
                'title': 'Outer',
                'type': 'object',
            },
        }
    }

    _, vs_schema = models_json_schema([(Outer, 'validation'), (Outer, 'serialization')])
    assert vs_schema == {
        '$defs': {
            'InnerInput': {
                'properties': {'x': {'format': 'json-string', 'title': 'X', 'type': 'string'}},
                'required': ['x'],
                'title': 'Inner',
                'type': 'object',
            },
            'InnerOutput': {
                'properties': {'x': {'title': 'X', 'type': 'integer'}},
                'required': ['x'],
                'title': 'Inner',
                'type': 'object',
            },
            'OuterInput': {
                'properties': {'inner': {'$ref': '#/$defs/InnerInput'}},
                'required': ['inner'],
                'title': 'Outer',
                'type': 'object',
            },
            'OuterOutput': {
                'properties': {'inner': {'$ref': '#/$defs/InnerOutput'}},
                'required': ['inner'],
                'title': 'Outer',
                'type': 'object',
            },
        }
    }


def test_computed_field():
    class Model(BaseModel):
        x: int

        @computed_field
        @property
        def double_x(self) -> int:
            return 2 * self.x

    assert Model.model_json_schema(mode='validation') == {
        'properties': {'x': {'title': 'X', 'type': 'integer'}},
        'required': ['x'],
        'title': 'Model',
        'type': 'object',
    }
    assert Model.model_json_schema(mode='serialization') == {
        'properties': {'double_x': {'title': 'Double X', 'type': 'integer'}, 'x': {'title': 'X', 'type': 'integer'}},
        'required': ['x', 'double_x'],
        'title': 'Model',
        'type': 'object',
    }


def test_serialization_schema_with_exclude():
    class MyGenerateJsonSchema(GenerateJsonSchema):
        def field_is_present(self, field) -> bool:
            # Always include fields in the JSON schema, even if excluded from serialization
            return True

    class Model(BaseModel):
        x: int
        y: int = Field(exclude=True)

    assert Model(x=1, y=1).model_dump() == {'x': 1}

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {'x': {'title': 'X', 'type': 'integer'}},
        'required': ['x'],
        'title': 'Model',
        'type': 'object',
    }
    assert Model.model_json_schema(mode='serialization', schema_generator=MyGenerateJsonSchema) == {
        'properties': {'x': {'title': 'X', 'type': 'integer'}, 'y': {'title': 'Y', 'type': 'integer'}},
        'required': ['x'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('mapping_type', [typing.Dict, typing.Mapping])
def test_mappings_str_int_json_schema(mapping_type: Any):
    class Model(BaseModel):
        str_int_map: mapping_type[str, int]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'str_int_map': {
                'title': 'Str Int Map',
                'type': 'object',
                'additionalProperties': {'type': 'integer'},
            }
        },
        'required': ['str_int_map'],
    }


@pytest.mark.parametrize(('sequence_type'), [pytest.param(List), pytest.param(Sequence)])
def test_sequence_schema(sequence_type):
    class Model(BaseModel):
        field: sequence_type[int]

    assert Model.model_json_schema() == {
        'properties': {
            'field': {'items': {'type': 'integer'}, 'title': 'Field', 'type': 'array'},
        },
        'required': ['field'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize(('sequence_type',), [pytest.param(List), pytest.param(Sequence)])
def test_sequences_int_json_schema(sequence_type):
    class Model(BaseModel):
        int_seq: sequence_type[int]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'int_seq': {
                'title': 'Int Seq',
                'type': 'array',
                'items': {'type': 'integer'},
            },
        },
        'required': ['int_seq'],
    }
    assert Model.model_validate_json('{"int_seq": [1, 2, 3]}')


@pytest.mark.parametrize(
    'field_schema,model_schema',
    [
        (None, {'properties': {}, 'title': 'Model', 'type': 'object'}),
        (
            {'a': 'b'},
            {'properties': {'x': {'a': 'b', 'title': 'X'}}, 'required': ['x'], 'title': 'Model', 'type': 'object'},
        ),
    ],
)
@pytest.mark.parametrize('instance_of', [True, False])
def test_arbitrary_type_json_schema(field_schema, model_schema, instance_of):
    class ArbitraryClass:
        pass

    if instance_of:

        class Model(BaseModel):
            x: Annotated[InstanceOf[ArbitraryClass], WithJsonSchema(field_schema)]

    else:

        class Model(BaseModel):
            model_config = dict(arbitrary_types_allowed=True)

            x: Annotated[ArbitraryClass, WithJsonSchema(field_schema)]

    assert Model.model_json_schema() == model_schema


def test_root_model():
    class A(RootModel[int]):
        pass

    assert A.model_json_schema() == {'type': 'integer'}

    class B(RootModel[A]):
        pass

    assert B.model_json_schema() == {'type': 'integer'}


def test_get_json_schema_is_passed_the_same_schema_handler_was_called_with() -> None:
    class CustomInt(int):
        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return handler(int)

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            assert core_schema['type'] == 'function-after'
            inner = core_schema['schema']
            assert inner['type'] == 'int'
            inner = inner.copy()
            inner['gt'] = 0
            core_schema = {**core_schema, 'schema': inner}
            return handler(core_schema)

    class Marker:
        def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(lambda x: x, handler(source_type))

        def __get_pydantic_json_schema__(
            self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return handler(core_schema)

    js_schema = TypeAdapter(Annotated[CustomInt, Marker()]).json_schema()

    # insert_assert(js_schema)
    assert js_schema == {'type': 'integer', 'exclusiveMinimum': 0}


def test_get_json_schema_gets_called_if_schema_is_replaced() -> None:
    class CustomInt(int):
        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return handler(int)

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            assert core_schema['type'] == 'str'
            core_schema = {**core_schema, 'min_length': 1}
            return handler(core_schema)

    class Marker:
        def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(lambda x: x, handler(source_type))

        def __get_pydantic_json_schema__(
            self, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return handler({'type': 'str'})

    js_schema = TypeAdapter(Annotated[CustomInt, Marker()]).json_schema()

    # insert_assert(js_schema)
    assert js_schema == {'type': 'string', 'minLength': 1}


def test_core_metadata_core_schema_metadata():
    with pytest.raises(TypeError, match=re.escape("CoreSchema metadata should be a dict; got 'test'.")):
        CoreMetadataHandler({'metadata': 'test'})

    core_metadata_handler = CoreMetadataHandler({})
    core_metadata_handler._schema = {}
    assert core_metadata_handler.metadata == {}
    core_metadata_handler._schema = {'metadata': 'test'}
    with pytest.raises(TypeError, match=re.escape("CoreSchema metadata should be a dict; got 'test'.")):
        core_metadata_handler.metadata


def test_build_metadata_dict_initial_metadata():
    assert build_metadata_dict(initial_metadata={'foo': 'bar'}) == {'foo': 'bar', 'pydantic_js_functions': []}

    with pytest.raises(TypeError, match=re.escape("CoreSchema metadata should be a dict; got 'test'.")):
        build_metadata_dict(initial_metadata='test')


def test_core_metadata_get_json_schema():
    core_metadata_handler = CoreMetadataHandler({})
    assert core_metadata_handler.get_json_schema({}, lambda c: c) == {}

    core_metadata_handler = CoreMetadataHandler(
        {'metadata': {'pydantic_js_function': lambda c, h: f'schema = {c}, {h.__name__}'}}
    )
    assert core_metadata_handler.get_json_schema({'foo': 'bar'}, lambda c: c) == "schema = {'foo': 'bar'}, <lambda>"


def test_type_adapter_json_schemas_title_description():
    class Model(BaseModel):
        a: str

    _, json_schema = TypeAdapter.json_schemas([(Model, 'validation', TypeAdapter(Model))])
    assert 'title' not in json_schema
    assert 'description' not in json_schema

    _, json_schema = TypeAdapter.json_schemas(
        [(Model, 'validation', TypeAdapter(Model))],
        title='test title',
        description='test description',
    )
    assert json_schema['title'] == 'test title'
    assert json_schema['description'] == 'test description'


def test_type_adapter_json_schemas_without_definitions():
    _, json_schema = TypeAdapter.json_schemas(
        [(int, 'validation', TypeAdapter(int))],
        ref_template='#/components/schemas/{model}',
    )

    assert 'definitions' not in json_schema


def test_custom_chain_schema():
    class MySequence:
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            list_schema = core_schema.list_schema()
            return core_schema.chain_schema([list_schema])

    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        a: MySequence

    assert Model.model_json_schema() == {
        'properties': {'a': {'items': {}, 'title': 'A', 'type': 'array'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }


def test_json_or_python_schema():
    class MyJsonOrPython:
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            int_schema = core_schema.int_schema()
            return core_schema.json_or_python_schema(json_schema=int_schema, python_schema=int_schema)

    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        a: MyJsonOrPython

    assert Model.model_json_schema() == {
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }


def test_lax_or_strict_schema():
    class MyLaxOrStrict:
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            int_schema = core_schema.int_schema()
            return core_schema.lax_or_strict_schema(lax_schema=int_schema, strict_schema=int_schema, strict=True)

    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        a: MyLaxOrStrict

    assert Model.model_json_schema() == {
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.xfail(reason='Need to fix JSON schema customization for Enum')
def test_override_enum_json_schema():
    class CustomType(Enum):
        A = 'a'
        B = 'b'

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> core_schema.CoreSchema:
            json_schema = handler(core_schema)
            json_schema.update(title='CustomType title', type='string')
            return json_schema

    class Model(BaseModel):
        x: CustomType

    assert Model.model_json_schema() == {
        'type': 'object',
        'properties': {'x': {'$ref': '#/$defs/CustomType'}},
        'required': ['x'],
        'title': 'Model',
        '$defs': {
            'CustomType': {
                'enum': ['a', 'b'],
                'title': 'CustomType title',  # <----------- this is not getting set properly
            }
        },
    }


def test_json_schema_extras_on_ref() -> None:
    @dataclass
    class JsonSchemaExamples:
        examples: Dict[str, Any]

        def __get_pydantic_json_schema__(
            self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            json_schema = handler(core_schema)
            assert json_schema.keys() == {'$ref'}
            json_schema['examples'] = to_json(self.examples)
            return json_schema

    @dataclass
    class JsonSchemaTitle:
        title: str

        def __get_pydantic_json_schema__(
            self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            json_schema = handler(core_schema)
            assert json_schema.keys() == {'allOf', 'examples'}
            json_schema['title'] = self.title
            return json_schema

    class Model(BaseModel):
        name: str
        age: int

    ta = TypeAdapter(
        Annotated[Model, JsonSchemaExamples({'foo': Model(name='John', age=28)}), JsonSchemaTitle('ModelTitle')]
    )

    # insert_assert(ta.json_schema())
    assert ta.json_schema() == {
        '$defs': {
            'Model': {
                'properties': {'age': {'title': 'Age', 'type': 'integer'}, 'name': {'title': 'Name', 'type': 'string'}},
                'required': ['name', 'age'],
                'title': 'Model',
                'type': 'object',
            }
        },
        'allOf': [{'$ref': '#/$defs/Model'}],
        'examples': b'{"foo":{"name":"John","age":28}}',
        'title': 'ModelTitle',
    }
