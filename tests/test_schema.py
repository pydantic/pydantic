import json
import math
import os
import re
import sys
import tempfile
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
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

import pytest
from typing_extensions import Annotated, Literal

from pydantic import BaseModel, Extra, Field, ValidationError, confrozenset, conlist, conset, validator
from pydantic.color import Color
from pydantic.dataclasses import dataclass
from pydantic.fields import ModelField
from pydantic.generics import GenericModel
from pydantic.networks import AnyUrl, EmailStr, IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork, NameEmail, stricturl
from pydantic.schema import (
    get_flat_models_from_model,
    get_flat_models_from_models,
    get_model_name_map,
    model_process_schema,
    model_schema,
    schema,
)
from pydantic.types import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    ConstrainedBytes,
    ConstrainedDate,
    ConstrainedDecimal,
    ConstrainedFloat,
    ConstrainedInt,
    ConstrainedStr,
    DirectoryPath,
    FilePath,
    Json,
    NegativeFloat,
    NegativeInt,
    NoneBytes,
    NoneStr,
    NoneStrBytes,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PositiveFloat,
    PositiveInt,
    PyObject,
    SecretBytes,
    SecretStr,
    StrBytes,
    StrictBool,
    StrictStr,
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


def test_key():
    class ApplePie(BaseModel):
        """
        This is a test.
        """

        a: float
        b: int = 10

    s = {
        'type': 'object',
        'properties': {'a': {'type': 'number', 'title': 'A'}, 'b': {'type': 'integer', 'title': 'B', 'default': 10}},
        'required': ['a'],
        'title': 'ApplePie',
        'description': 'This is a test.',
    }
    assert ApplePie.__schema_cache__.keys() == set()
    assert ApplePie.schema() == s
    assert ApplePie.__schema_cache__.keys() == {(True, '#/definitions/{model}')}
    assert ApplePie.schema() == s


def test_by_alias():
    class ApplePie(BaseModel):
        a: float
        b: int = 10

        class Config:
            title = 'Apple Pie'
            fields = {'a': 'Snap', 'b': 'Crackle'}

    assert ApplePie.schema() == {
        'type': 'object',
        'title': 'Apple Pie',
        'properties': {
            'Snap': {'type': 'number', 'title': 'Snap'},
            'Crackle': {'type': 'integer', 'title': 'Crackle', 'default': 10},
        },
        'required': ['Snap'],
    }
    assert list(ApplePie.schema(by_alias=True)['properties'].keys()) == ['Snap', 'Crackle']
    assert list(ApplePie.schema(by_alias=False)['properties'].keys()) == ['a', 'b']


def test_ref_template():
    class KeyLimePie(BaseModel):
        x: str = None

    class ApplePie(BaseModel):
        a: float = None
        key_lime: KeyLimePie = None

        class Config:
            title = 'Apple Pie'

    assert ApplePie.schema(ref_template='foobar/{model}.json') == {
        'title': 'Apple Pie',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'number'}, 'key_lime': {'$ref': 'foobar/KeyLimePie.json'}},
        'definitions': {
            'KeyLimePie': {
                'title': 'KeyLimePie',
                'type': 'object',
                'properties': {'x': {'title': 'X', 'type': 'string'}},
            },
        },
    }
    assert ApplePie.schema()['properties']['key_lime'] == {'$ref': '#/definitions/KeyLimePie'}
    json_schema = ApplePie.schema_json(ref_template='foobar/{model}.json')
    assert 'foobar/KeyLimePie.json' in json_schema
    assert '#/definitions/KeyLimePie' not in json_schema


def test_by_alias_generator():
    class ApplePie(BaseModel):
        a: float
        b: int = 10

        class Config:
            @staticmethod
            def alias_generator(x):
                return x.upper()

    assert ApplePie.schema() == {
        'title': 'ApplePie',
        'type': 'object',
        'properties': {'A': {'title': 'A', 'type': 'number'}, 'B': {'title': 'B', 'default': 10, 'type': 'integer'}},
        'required': ['A'],
    }
    assert ApplePie.schema(by_alias=False)['properties'].keys() == {'a', 'b'}


def test_sub_model():
    class Foo(BaseModel):
        """hello"""

        b: float

    class Bar(BaseModel):
        a: int
        b: Foo = None

    assert Bar.schema() == {
        'type': 'object',
        'title': 'Bar',
        'definitions': {
            'Foo': {
                'type': 'object',
                'title': 'Foo',
                'description': 'hello',
                'properties': {'b': {'type': 'number', 'title': 'B'}},
                'required': ['b'],
            }
        },
        'properties': {'a': {'type': 'integer', 'title': 'A'}, 'b': {'$ref': '#/definitions/Foo'}},
        'required': ['a'],
    }


def test_schema_class():
    class Model(BaseModel):
        foo: int = Field(4, title='Foo is Great')
        bar: str = Field(..., description='this description of bar')

    with pytest.raises(ValidationError):
        Model()

    m = Model(bar=123)
    assert m.dict() == {'foo': 4, 'bar': '123'}

    assert Model.schema() == {
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
    assert str(s) == "default=4 title='Foo is Great' extra={}"
    assert repr(s) == "FieldInfo(default=4, title='Foo is Great', extra={})"


def test_schema_class_by_alias():
    class Model(BaseModel):
        foo: int = Field(4, alias='foofoo')

    assert list(Model.schema()['properties'].keys()) == ['foofoo']
    assert list(Model.schema(by_alias=False)['properties'].keys()) == ['foo']


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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'foo': {'$ref': '#/definitions/FooEnum'},
            'bar': {'$ref': '#/definitions/BarEnum'},
            'spam': {'$ref': '#/definitions/SpamEnum'},
        },
        'required': ['foo', 'bar'],
        'definitions': {
            'FooEnum': {'title': 'FooEnum', 'description': 'An enumeration.', 'enum': ['f', 'b']},
            'BarEnum': {'title': 'BarEnum', 'description': 'An enumeration.', 'type': 'integer', 'enum': [1, 2]},
            'SpamEnum': {'title': 'SpamEnum', 'description': 'An enumeration.', 'type': 'string', 'enum': ['f', 'b']},
        },
    }


def test_enum_modify_schema():
    class SpamEnum(str, Enum):
        foo = 'f'
        bar = 'b'

        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema['tsEnumNames'] = [e.name for e in cls]

    class Model(BaseModel):
        spam: SpamEnum = Field(None)

    assert Model.schema() == {
        'definitions': {
            'SpamEnum': {
                'description': 'An enumeration.',
                'enum': ['f', 'b'],
                'title': 'SpamEnum',
                'tsEnumNames': ['foo', 'bar'],
                'type': 'string',
            }
        },
        'properties': {'spam': {'$ref': '#/definitions/SpamEnum'}},
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

    assert Model.schema() == {
        'definitions': {
            'FooBarEnum': {
                'description': 'An enumeration.',
                'enum': ['foo', 'bar'],
                'title': 'FooBarEnum',
                'type': 'string',
            }
        },
        'properties': {
            'pikalias': {
                'allOf': [{'$ref': '#/definitions/FooBarEnum'}],
                'description': 'Pika is definitely the best!',
                'title': 'Pikapika!',
            },
            'bulbialias': {
                'allOf': [{'$ref': '#/definitions/FooBarEnum'}],
                'description': 'Bulbi is not...',
                'title': 'Bulbibulbi!',
                'default': 'foo',
            },
            'cara': {'$ref': '#/definitions/FooBarEnum'},
        },
        'required': ['pikalias', 'cara'],
        'title': 'Model',
        'type': 'object',
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

    assert Foo.schema() == {
        'definitions': {
            'Pika': {
                'properties': {'a': {'title': 'A', 'type': 'string'}},
                'required': ['a'],
                'title': 'Pika',
                'type': 'object',
            },
            'Names': {
                'description': 'An enumeration.',
                'enum': ['Rick', 'Morty', 'Summer'],
                'title': 'Names',
                'type': 'string',
            },
        },
        'properties': {
            'enum': {'$ref': '#/definitions/Names'},
            'model': {'$ref': '#/definitions/Pika'},
            'titled_enum': {
                'allOf': [{'$ref': '#/definitions/Names'}],
                'description': 'Description of enum',
                'title': 'Title of enum',
            },
            'titled_model': {
                'allOf': [{'$ref': '#/definitions/Pika'}],
                'description': 'Description of model',
                'title': 'Title of model',
            },
        },
        'required': ['enum', 'titled_enum', 'model', 'titled_model'],
        'title': 'Foo',
        'type': 'object',
    }


def test_enum_includes_extra_without_other_params():
    class Names(str, Enum):
        rick = 'Rick'
        morty = 'Morty'
        summer = 'Summer'

    class Foo(BaseModel):
        enum: Names
        extra_enum: Names = Field(..., extra='Extra field')

    assert Foo.schema() == {
        'definitions': {
            'Names': {
                'description': 'An enumeration.',
                'enum': ['Rick', 'Morty', 'Summer'],
                'title': 'Names',
                'type': 'string',
            },
        },
        'properties': {
            'enum': {'$ref': '#/definitions/Names'},
            'extra_enum': {'allOf': [{'$ref': '#/definitions/Names'}], 'extra': 'Extra field'},
        },
        'required': ['enum', 'extra_enum'],
        'title': 'Foo',
        'type': 'object',
    }


def test_list_enum_schema_extras():
    class FoodChoice(str, Enum):
        spam = 'spam'
        egg = 'egg'
        chips = 'chips'

    class Model(BaseModel):
        foods: List[FoodChoice] = Field(examples=[['spam', 'egg']])

    assert Model.schema() == {
        'definitions': {
            'FoodChoice': {
                'description': 'An enumeration.',
                'enum': ['spam', 'egg', 'chips'],
                'title': 'FoodChoice',
                'type': 'string',
            }
        },
        'properties': {
            'foods': {'type': 'array', 'items': {'$ref': '#/definitions/FoodChoice'}, 'examples': [['spam', 'egg']]},
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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'enum': {'$ref': '#/definitions/FooBar'}},
        'required': ['enum'],
        'definitions': {
            'FooBar': {
                'title': 'FooBar',
                'description': 'This is docstring which needs to be cleaned up',
                'enum': ['foo', 'bar'],
                'type': 'string',
            }
        },
    }


def test_json_schema():
    class Model(BaseModel):
        a = b'foobar'
        b = Decimal('12.34')

    assert json.loads(Model.schema_json(indent=2)) == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'default': 'foobar', 'type': 'string', 'format': 'binary'},
            'b': {'title': 'B', 'default': 12.34, 'type': 'number'},
        },
    }


def test_list_sub_model():
    class Foo(BaseModel):
        a: float

    class Bar(BaseModel):
        b: List[Foo]

    assert Bar.schema() == {
        'title': 'Bar',
        'type': 'object',
        'definitions': {
            'Foo': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'type': 'number', 'title': 'A'}},
                'required': ['a'],
            }
        },
        'properties': {'b': {'type': 'array', 'items': {'$ref': '#/definitions/Foo'}, 'title': 'B'}},
        'required': ['b'],
    }


def test_optional():
    class Model(BaseModel):
        a: Optional[str]

    assert Model.schema() == {'title': 'Model', 'type': 'object', 'properties': {'a': {'type': 'string', 'title': 'A'}}}


def test_any():
    class Model(BaseModel):
        a: Any
        b: object

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A'},
            'b': {'title': 'B'},
        },
    }


def test_set():
    class Model(BaseModel):
        a: Set[int]
        b: set
        c: set = {1}

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'array', 'uniqueItems': True, 'items': {'type': 'integer'}},
            'b': {'title': 'B', 'type': 'array', 'items': {}, 'uniqueItems': True},
            'c': {'title': 'C', 'type': 'array', 'items': {}, 'default': [1], 'uniqueItems': True},
        },
        'required': ['a', 'b'],
    }


def test_const_str():
    class Model(BaseModel):
        a: str = Field('some string', const=True)

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'const': 'some string', 'default': 'some string'}},
    }


def test_const_false():
    class Model(BaseModel):
        a: str = Field('some string', const=False)

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'default': 'some string'}},
    }


@pytest.mark.parametrize(
    'field_type,extra_props',
    [
        (tuple, {'items': {}}),
        (
            Tuple[str, int, Union[str, int, float], float],
            {
                'items': [
                    {'type': 'string'},
                    {'type': 'integer'},
                    {'anyOf': [{'type': 'string'}, {'type': 'integer'}, {'type': 'number'}]},
                    {'type': 'number'},
                ],
                'minItems': 4,
                'maxItems': 4,
            },
        ),
        (Tuple[str], {'items': [{'type': 'string'}], 'minItems': 1, 'maxItems': 1}),
        (Tuple[()], {'maxItems': 0, 'minItems': 0}),
    ],
)
def test_tuple(field_type, extra_props):
    class Model(BaseModel):
        a: field_type

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'array', **extra_props}},
        'required': ['a'],
    }


def test_deque():
    class Model(BaseModel):
        a: Deque[str]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'array', 'items': {'type': 'string'}}},
        'required': ['a'],
    }


def test_bool():
    class Model(BaseModel):
        a: bool

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'boolean'}},
        'required': ['a'],
    }


def test_strict_bool():
    class Model(BaseModel):
        a: StrictBool

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'boolean'}},
        'required': ['a'],
    }


def test_dict():
    class Model(BaseModel):
        a: dict

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'object'}},
        'required': ['a'],
    }


def test_list():
    class Model(BaseModel):
        a: list

    assert Model.schema() == {
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
                'definitions': {
                    'Foo': {
                        'title': 'Foo',
                        'type': 'object',
                        'properties': {'a': {'title': 'A', 'type': 'number'}},
                        'required': ['a'],
                    }
                },
                'properties': {
                    'a': {'title': 'A', 'type': 'object', 'additionalProperties': {'$ref': '#/definitions/Foo'}}
                },
                'required': ['a'],
            },
        ),
        (
            Union[None, Foo],
            {
                'definitions': {
                    'Foo': {
                        'title': 'Foo',
                        'type': 'object',
                        'properties': {'a': {'title': 'A', 'type': 'number'}},
                        'required': ['a'],
                    }
                },
                'properties': {'a': {'$ref': '#/definitions/Foo'}},
            },
        ),
        (Dict[str, Any], {'properties': {'a': {'title': 'A', 'type': 'object'}}, 'required': ['a']}),
    ],
)
def test_list_union_dict(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {'title': 'Model', 'type': 'object'}
    base_schema.update(expected_schema)

    assert Model.schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (datetime, {'type': 'string', 'format': 'date-time'}),
        (date, {'type': 'string', 'format': 'date'}),
        (time, {'type': 'string', 'format': 'time'}),
        (timedelta, {'type': 'number', 'format': 'time-delta'}),
    ],
)
def test_date_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    attribute_schema = {'title': 'A'}
    attribute_schema.update(expected_schema)

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': attribute_schema}, 'required': ['a']}

    assert Model.schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (ConstrainedDate, {}),
        (condate(), {}),
        (
            condate(gt=date(2010, 1, 1), lt=date(2021, 2, 2)),
            {'exclusiveMinimum': '2010-01-01', 'exclusiveMaximum': '2021-02-02'},
        ),
        (condate(ge=date(2010, 1, 1), le=date(2021, 2, 2)), {'minimum': '2010-01-01', 'maximum': '2021-02-02'}),
    ],
)
def test_date_constrained_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    assert json.loads(Model.schema_json()) == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'format': 'date', **expected_schema}},
        'required': ['a'],
    }


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (NoneStr, {'properties': {'a': {'title': 'A', 'type': 'string'}}}),
        (NoneBytes, {'properties': {'a': {'title': 'A', 'type': 'string', 'format': 'binary'}}}),
        (
            StrBytes,
            {
                'properties': {
                    'a': {'title': 'A', 'anyOf': [{'type': 'string'}, {'type': 'string', 'format': 'binary'}]}
                },
                'required': ['a'],
            },
        ),
        (
            NoneStrBytes,
            {
                'properties': {
                    'a': {'title': 'A', 'anyOf': [{'type': 'string'}, {'type': 'string', 'format': 'binary'}]}
                }
            },
        ),
    ],
)
def test_str_basic_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {'title': 'Model', 'type': 'object'}
    base_schema.update(expected_schema)
    assert Model.schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (StrictStr, {'title': 'A', 'type': 'string'}),
        (ConstrainedStr, {'title': 'A', 'type': 'string'}),
        (
            constr(min_length=3, max_length=5, regex='^text$'),
            {'title': 'A', 'type': 'string', 'minLength': 3, 'maxLength': 5, 'pattern': '^text$'},
        ),
    ],
)
def test_str_constrained_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    model_schema = Model.schema()
    assert model_schema['properties']['a'] == expected_schema

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': expected_schema}, 'required': ['a']}

    assert model_schema == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (AnyUrl, {'title': 'A', 'type': 'string', 'format': 'uri', 'minLength': 1, 'maxLength': 2**16}),
        (
            stricturl(min_length=5, max_length=10),
            {'title': 'A', 'type': 'string', 'format': 'uri', 'minLength': 5, 'maxLength': 10},
        ),
    ],
)
def test_special_str_types(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': {}}, 'required': ['a']}
    base_schema['properties']['a'] = expected_schema

    assert Model.schema() == base_schema


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

    assert Model.schema() == base_schema


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

    assert Model.schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (ConstrainedInt, {}),
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

    assert Model.schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (ConstrainedFloat, {}),
        (confloat(gt=5, lt=10), {'exclusiveMinimum': 5, 'exclusiveMaximum': 10}),
        (confloat(ge=5, le=10), {'minimum': 5, 'maximum': 10}),
        (confloat(multiple_of=5), {'multipleOf': 5}),
        (PositiveFloat, {'exclusiveMinimum': 0}),
        (NegativeFloat, {'exclusiveMaximum': 0}),
        (NonNegativeFloat, {'minimum': 0}),
        (NonPositiveFloat, {'maximum': 0}),
        (ConstrainedDecimal, {}),
        (condecimal(gt=5, lt=10), {'exclusiveMinimum': 5, 'exclusiveMaximum': 10}),
        (condecimal(ge=5, le=10), {'minimum': 5, 'maximum': 10}),
        (condecimal(multiple_of=5), {'multipleOf': 5}),
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

    assert Model.schema() == base_schema


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
        'properties': {'a': {'title': 'A', 'type': 'string', 'format': ''}},
        'required': ['a'],
    }
    base_schema['properties']['a']['format'] = expected_schema

    assert Model.schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema', [(FilePath, 'file-path'), (DirectoryPath, 'directory-path'), (Path, 'path')]
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

    assert Model.schema() == base_schema


def test_json_type():
    class Model(BaseModel):
        a: Json
        b: Json[int]
        c: Json[Any]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'string', 'format': 'json-string'},
            'b': {'title': 'B', 'type': 'integer'},
            'c': {'title': 'C', 'type': 'string', 'format': 'json-string'},
        },
        'required': ['b'],
    }


def test_ipv4address_type():
    class Model(BaseModel):
        ip_address: IPv4Address

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip Address', 'type': 'string', 'format': 'ipv4'}},
        'required': ['ip_address'],
    }


def test_ipv6address_type():
    class Model(BaseModel):
        ip_address: IPv6Address

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip Address', 'type': 'string', 'format': 'ipv6'}},
        'required': ['ip_address'],
    }


def test_ipvanyaddress_type():
    class Model(BaseModel):
        ip_address: IPvAnyAddress

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip Address', 'type': 'string', 'format': 'ipvanyaddress'}},
        'required': ['ip_address'],
    }


def test_ipv4interface_type():
    class Model(BaseModel):
        ip_interface: IPv4Interface

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip Interface', 'type': 'string', 'format': 'ipv4interface'}},
        'required': ['ip_interface'],
    }


def test_ipv6interface_type():
    class Model(BaseModel):
        ip_interface: IPv6Interface

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip Interface', 'type': 'string', 'format': 'ipv6interface'}},
        'required': ['ip_interface'],
    }


def test_ipvanyinterface_type():
    class Model(BaseModel):
        ip_interface: IPvAnyInterface

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip Interface', 'type': 'string', 'format': 'ipvanyinterface'}},
        'required': ['ip_interface'],
    }


def test_ipv4network_type():
    class Model(BaseModel):
        ip_network: IPv4Network

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_network': {'title': 'Ip Network', 'type': 'string', 'format': 'ipv4network'}},
        'required': ['ip_network'],
    }


def test_ipv6network_type():
    class Model(BaseModel):
        ip_network: IPv6Network

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_network': {'title': 'Ip Network', 'type': 'string', 'format': 'ipv6network'}},
        'required': ['ip_network'],
    }


def test_ipvanynetwork_type():
    class Model(BaseModel):
        ip_network: IPvAnyNetwork

    model_schema = Model.schema()
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
def test_callable_type(type_, default_value):
    class Model(BaseModel):
        callback: type_ = default_value
        foo: int

    with pytest.warns(UserWarning):
        model_schema = Model.schema()

    assert 'callback' not in model_schema['properties']


def test_error_non_supported_types():
    class Model(BaseModel):
        a: PyObject

    with pytest.raises(ValueError):
        Model.schema()


def create_testing_submodules():
    base_path = Path(tempfile.mkdtemp())
    mod_root_path = base_path / 'pydantic_schema_test'
    os.makedirs(mod_root_path, exist_ok=True)
    open(mod_root_path / '__init__.py', 'w').close()
    for mod in ['a', 'b', 'c']:
        module_name = 'module' + mod
        model_name = 'model' + mod + '.py'
        os.makedirs(mod_root_path / module_name, exist_ok=True)
        open(mod_root_path / module_name / '__init__.py', 'w').close()
        with open(mod_root_path / module_name / model_name, 'w') as f:
            f.write('from pydantic import BaseModel\n' 'class Model(BaseModel):\n' '    a: str\n')
    module_name = 'moduled'
    model_name = 'modeld.py'
    os.makedirs(mod_root_path / module_name, exist_ok=True)
    open(mod_root_path / module_name / '__init__.py', 'w').close()
    with open(mod_root_path / module_name / model_name, 'w') as f:
        f.write('from ..moduleb.modelb import Model')
    sys.path.insert(0, str(base_path))


def test_flat_models_unique_models():
    create_testing_submodules()
    from pydantic_schema_test.modulea.modela import Model as ModelA
    from pydantic_schema_test.moduleb.modelb import Model as ModelB
    from pydantic_schema_test.moduled.modeld import Model as ModelD

    flat_models = get_flat_models_from_models([ModelA, ModelB, ModelD])
    assert flat_models == {ModelA, ModelB}


def test_flat_models_with_submodels():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: List[Foo]

    class Baz(BaseModel):
        c: Dict[str, Bar]

    flat_models = get_flat_models_from_model(Baz)
    assert flat_models == {Foo, Bar, Baz}


def test_flat_models_with_submodels_from_sequence():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Ingredient(BaseModel):
        name: str

    class Pizza(BaseModel):
        name: str
        ingredients: List[Ingredient]

    flat_models = get_flat_models_from_models([Bar, Pizza])
    assert flat_models == {Foo, Bar, Ingredient, Pizza}


def test_model_name_maps():
    create_testing_submodules()
    from pydantic_schema_test.modulea.modela import Model as ModelA
    from pydantic_schema_test.moduleb.modelb import Model as ModelB
    from pydantic_schema_test.modulec.modelc import Model as ModelC
    from pydantic_schema_test.moduled.modeld import Model as ModelD

    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    flat_models = get_flat_models_from_models([Baz, ModelA, ModelB, ModelC, ModelD])
    model_name_map = get_model_name_map(flat_models)
    assert model_name_map == {
        Foo: 'Foo',
        Bar: 'Bar',
        Baz: 'Baz',
        ModelA: 'pydantic_schema_test__modulea__modela__Model',
        ModelB: 'pydantic_schema_test__moduleb__modelb__Model',
        ModelC: 'pydantic_schema_test__modulec__modelc__Model',
    }


def test_schema_overrides():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo = Foo(a='foo')

    class Baz(BaseModel):
        c: Optional[Bar]

    class Model(BaseModel):
        d: Baz

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'definitions': {
            'Foo': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'string'}},
                'required': ['a'],
            },
            'Bar': {
                'title': 'Bar',
                'type': 'object',
                'properties': {'b': {'title': 'B', 'default': {'a': 'foo'}, 'allOf': [{'$ref': '#/definitions/Foo'}]}},
            },
            'Baz': {'title': 'Baz', 'type': 'object', 'properties': {'c': {'$ref': '#/definitions/Bar'}}},
        },
        'properties': {'d': {'$ref': '#/definitions/Baz'}},
        'required': ['d'],
    }


def test_schema_overrides_w_union():
    class Foo(BaseModel):
        pass

    class Bar(BaseModel):
        pass

    class Spam(BaseModel):
        a: Union[Foo, Bar] = Field(..., description='xxx')

    assert Spam.schema()['properties'] == {
        'a': {
            'title': 'A',
            'description': 'xxx',
            'anyOf': [{'$ref': '#/definitions/Foo'}, {'$ref': '#/definitions/Bar'}],
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

    model_schema = schema(
        [Model, Pizza], title='Multi-model schema', description='Single JSON Schema with multiple definitions'
    )
    assert model_schema == {
        'title': 'Multi-model schema',
        'description': 'Single JSON Schema with multiple definitions',
        'definitions': {
            'Pizza': {
                'title': 'Pizza',
                'type': 'object',
                'properties': {
                    'name': {'title': 'Name', 'type': 'string'},
                    'ingredients': {
                        'title': 'Ingredients',
                        'type': 'array',
                        'items': {'$ref': '#/definitions/Ingredient'},
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
                'properties': {'d': {'$ref': '#/definitions/Baz'}},
                'required': ['d'],
            },
            'Baz': {
                'title': 'Baz',
                'type': 'object',
                'properties': {'c': {'$ref': '#/definitions/Bar'}},
                'required': ['c'],
            },
            'Bar': {
                'title': 'Bar',
                'type': 'object',
                'properties': {'b': {'$ref': '#/definitions/Foo'}},
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


@pytest.mark.parametrize(
    'ref_prefix,ref_template',
    [
        # OpenAPI style
        ('#/components/schemas/', None),
        (None, '#/components/schemas/{model}'),
        # ref_prefix takes priority
        ('#/components/schemas/', '#/{model}/schemas/'),
    ],
)
def test_schema_with_refs(ref_prefix, ref_template):
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    model_schema = schema([Bar, Baz], ref_prefix=ref_prefix, ref_template=ref_template)
    assert model_schema == {
        'definitions': {
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

    model_schema = schema([Bar, Baz], ref_template='/schemas/{model}.json#/')
    assert model_schema == {
        'definitions': {
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
        schema([Bar, Baz], ref_template='/schemas/{bad_name}.json#/')


def test_schema_no_definitions():
    model_schema = schema([], title='Schema without definitions')
    assert model_schema == {'title': 'Schema without definitions'}


def test_list_default():
    class UserModel(BaseModel):
        friends: List[int] = [1]

    assert UserModel.schema() == {
        'title': 'UserModel',
        'type': 'object',
        'properties': {'friends': {'title': 'Friends', 'default': [1], 'type': 'array', 'items': {'type': 'integer'}}},
    }


def test_enum_str_default():
    class MyEnum(str, Enum):
        FOO = 'foo'

    class UserModel(BaseModel):
        friends: MyEnum = MyEnum.FOO

    assert UserModel.schema()['properties']['friends']['default'] is MyEnum.FOO.value


def test_enum_int_default():
    class MyEnum(IntEnum):
        FOO = 1

    class UserModel(BaseModel):
        friends: MyEnum = MyEnum.FOO

    assert UserModel.schema()['properties']['friends']['default'] is MyEnum.FOO.value


def test_dict_default():
    class UserModel(BaseModel):
        friends: Dict[str, float] = {'a': 1.1, 'b': 2.2}

    assert UserModel.schema() == {
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

    assert Outer.schema() == {
        'definitions': {
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
        'properties': {
            'inner': {'allOf': [{'$ref': '#/definitions/Inner'}], 'default': {'a': {'.': ''}}, 'title': 'Inner'}
        },
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
        ({'regex': '^foo$'}, str, {'type': 'string', 'pattern': '^foo$'}),
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
        ({'gt': 2}, Decimal, {'type': 'number', 'exclusiveMinimum': 2}),
        ({'lt': 5}, Decimal, {'type': 'number', 'exclusiveMaximum': 5}),
        ({'ge': 2}, Decimal, {'type': 'number', 'minimum': 2}),
        ({'le': 5}, Decimal, {'type': 'number', 'maximum': 5}),
        ({'multiple_of': 5}, Decimal, {'type': 'number', 'multipleOf': 5}),
    ],
)
def test_constraints_schema(kwargs, type_, expected_extra):
    class Foo(BaseModel):
        a: type_ = Field('foo', title='A title', description='A description', **kwargs)

    expected_schema = {
        'title': 'Foo',
        'type': 'object',
        'properties': {'a': {'title': 'A title', 'description': 'A description', 'default': 'foo'}},
    }

    expected_schema['properties']['a'].update(expected_extra)
    assert Foo.schema() == expected_schema


@pytest.mark.parametrize(
    'kwargs,type_',
    [
        ({'max_length': 5}, int),
        ({'min_length': 2}, float),
        ({'max_length': 5}, Decimal),
        ({'allow_mutation': False}, bool),
        ({'regex': '^foo$'}, int),
        ({'gt': 2}, str),
        ({'lt': 5}, bytes),
        ({'ge': 2}, str),
        ({'le': 5}, bool),
        ({'gt': 0}, Callable),
        ({'gt': 0}, Callable[[int], int]),
        ({'gt': 0}, conlist(int, min_items=4)),
        ({'gt': 0}, conset(int, min_items=4)),
        ({'gt': 0}, confrozenset(int, min_items=4)),
    ],
)
def test_unenforced_constraints_schema(kwargs, type_):
    with pytest.raises(ValueError, match='On field "a" the following field constraints are set but not enforced'):

        class Foo(BaseModel):
            a: type_ = Field('foo', title='A title', description='A description', **kwargs)


@pytest.mark.parametrize(
    'kwargs,type_,value',
    [
        ({'max_length': 5}, str, 'foo'),
        ({'min_length': 2}, str, 'foo'),
        ({'max_length': 5}, bytes, b'foo'),
        ({'regex': '^foo$'}, str, 'foo'),
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
def test_constraints_schema_validation(kwargs, type_, value):
    class Foo(BaseModel):
        a: type_ = Field('foo', title='A title', description='A description', **kwargs)

    assert Foo(a=value)


@pytest.mark.parametrize(
    'kwargs,type_,value',
    [
        ({'max_length': 5}, str, 'foobar'),
        ({'min_length': 2}, str, 'f'),
        ({'regex': '^foo$'}, str, 'bar'),
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

    assert Foo.schema() == {
        'title': 'Foo',
        'type': 'object',
        'properties': {'a': {'type': 'string', 'title': 'A', 'default': 'foo', 'examples': ['bar']}},
    }


def test_schema_dict_constr():
    regex_str = r'^([a-zA-Z_][a-zA-Z0-9_]*)$'
    ConStrType = constr(regex=regex_str)
    ConStrKeyDict = Dict[ConStrType, str]

    class Foo(BaseModel):
        a: ConStrKeyDict = {}

    assert Foo.schema() == {
        'title': 'Foo',
        'type': 'object',
        'properties': {
            'a': {
                'type': 'object',
                'title': 'A',
                'default': {},
                'additionalProperties': {'type': 'string'},
                'patternProperties': {regex_str: {'type': 'string'}},
            }
        },
    }


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (ConstrainedBytes, {'title': 'A', 'type': 'string', 'format': 'binary'}),
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

    assert Model.schema() == base_schema


def test_optional_dict():
    class Model(BaseModel):
        something: Optional[Dict[str, Any]]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'something': {'title': 'Something', 'type': 'object'}},
    }

    assert Model().dict() == {'something': None}
    assert Model(something={'foo': 'Bar'}).dict() == {'something': {'foo': 'Bar'}}


def test_optional_validator():
    class Model(BaseModel):
        something: Optional[str]

        @validator('something', always=True)
        def check_something(cls, v):
            assert v is None or 'x' not in v, 'should not contain x'
            return v

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'something': {'title': 'Something', 'type': 'string'}},
    }

    assert Model().dict() == {'something': None}
    assert Model(something=None).dict() == {'something': None}
    assert Model(something='hello').dict() == {'something': 'hello'}


def test_field_with_validator():
    class Model(BaseModel):
        something: Optional[int] = None

        @validator('something')
        def check_field(cls, v, *, values, config, field):
            return v

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'something': {'type': 'integer', 'title': 'Something'}},
    }


def test_unparameterized_schema_generation():
    class FooList(BaseModel):
        d: List

    class BarList(BaseModel):
        d: list

    assert model_schema(FooList) == {
        'title': 'FooList',
        'type': 'object',
        'properties': {'d': {'items': {}, 'title': 'D', 'type': 'array'}},
        'required': ['d'],
    }

    foo_list_schema = model_schema(FooList)
    bar_list_schema = model_schema(BarList)
    bar_list_schema['title'] = 'FooList'  # to check for equality
    assert foo_list_schema == bar_list_schema

    class FooDict(BaseModel):
        d: Dict

    class BarDict(BaseModel):
        d: dict

    model_schema(Foo)
    assert model_schema(FooDict) == {
        'title': 'FooDict',
        'type': 'object',
        'properties': {'d': {'title': 'D', 'type': 'object'}},
        'required': ['d'],
    }

    foo_dict_schema = model_schema(FooDict)
    bar_dict_schema = model_schema(BarDict)
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
            'dep': {'$ref': '#/definitions/Dep'},
            'dep_l': {'title': 'Dep L', 'type': 'array', 'items': {'$ref': '#/definitions/Dep'}},
        },
        'required': ['dep', 'dep_l'],
        'definitions': {
            'Dep': {
                'title': 'Dep',
                'type': 'object',
                'properties': {'number': {'title': 'Number', 'type': 'integer'}},
                'required': ['number'],
            }
        },
    }

    assert Model.schema() == expected


def test_root():
    class Model(BaseModel):
        __root__: str

    assert Model.schema() == {'title': 'Model', 'type': 'string'}


def test_root_list():
    class Model(BaseModel):
        __root__: List[str]

    assert Model.schema() == {'title': 'Model', 'type': 'array', 'items': {'type': 'string'}}


def test_root_nested_model():
    class NestedModel(BaseModel):
        a: str

    class Model(BaseModel):
        __root__: List[NestedModel]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'array',
        'items': {'$ref': '#/definitions/NestedModel'},
        'definitions': {
            'NestedModel': {
                'title': 'NestedModel',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'string'}},
                'required': ['a'],
            }
        },
    }


def test_new_type_schema():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', str)

    class Model(BaseModel):
        a: a_type
        b: b_type
        c: c_type

    assert Model.schema() == {
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

    assert Model.schema() == {
        'properties': {
            'a': {'title': 'A', 'type': 'integer', 'enum': [1]},
            'b': {'title': 'B', 'type': 'string', 'enum': ['a']},
            'c': {'title': 'C', 'anyOf': [{'type': 'string', 'enum': ['a']}, {'type': 'integer', 'enum': [1]}]},
            'd': {
                'title': 'D',
                'anyOf': [
                    {'type': 'string', 'enum': ['a', 'b']},
                    {'type': 'integer', 'enum': [1, 2]},
                ],
            },
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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'kind': {'title': 'Kind', 'enum': ['foo'], 'type': 'string'}},
        'required': ['kind'],
    }


def test_color_type():
    class Model(BaseModel):
        color: Color

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'color': {'title': 'Color', 'type': 'string', 'format': 'color'}},
        'required': ['color'],
    }


def test_model_with_schema_extra():
    class Model(BaseModel):
        a: str

        class Config:
            schema_extra = {'examples': [{'a': 'Foo'}]}

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'examples': [{'a': 'Foo'}],
    }


def test_model_with_schema_extra_callable():
    class Model(BaseModel):
        name: str = None

        class Config:
            @staticmethod
            def schema_extra(schema, model_class):
                schema.pop('properties')
                schema['type'] = 'override'
                assert model_class is Model

    assert Model.schema() == {'title': 'Model', 'type': 'override'}


def test_model_with_schema_extra_callable_no_model_class():
    class Model(BaseModel):
        name: str = None

        class Config:
            @staticmethod
            def schema_extra(schema):
                schema.pop('properties')
                schema['type'] = 'override'

    assert Model.schema() == {'title': 'Model', 'type': 'override'}


def test_model_with_schema_extra_callable_classmethod():
    class Model(BaseModel):
        name: str = None

        class Config:
            type = 'foo'

            @classmethod
            def schema_extra(cls, schema, model_class):
                schema.pop('properties')
                schema['type'] = cls.type
                assert model_class is Model

    assert Model.schema() == {'title': 'Model', 'type': 'foo'}


def test_model_with_schema_extra_callable_instance_method():
    class Model(BaseModel):
        name: str = None

        class Config:
            def schema_extra(schema, model_class):
                schema.pop('properties')
                schema['type'] = 'override'
                assert model_class is Model

    assert Model.schema() == {'title': 'Model', 'type': 'override'}


def test_model_with_extra_forbidden():
    class Model(BaseModel):
        a: str

        class Config:
            extra = Extra.forbid

    assert Model.schema() == {
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
        (Optional[int], dict(gt=0), {'title': 'A', 'exclusiveMinimum': 0, 'type': 'integer'}),
        (
            Tuple[int, ...],
            dict(gt=0),
            {'title': 'A', 'exclusiveMinimum': 0, 'type': 'array', 'items': {'exclusiveMinimum': 0, 'type': 'integer'}},
        ),
        (
            Tuple[int, int, int],
            dict(gt=0),
            {
                'title': 'A',
                'type': 'array',
                'items': [
                    {'exclusiveMinimum': 0, 'type': 'integer'},
                    {'exclusiveMinimum': 0, 'type': 'integer'},
                    {'exclusiveMinimum': 0, 'type': 'integer'},
                ],
                'minItems': 3,
                'maxItems': 3,
            },
        ),
        (
            Union[int, float],
            dict(gt=0),
            {
                'title': 'A',
                'anyOf': [{'exclusiveMinimum': 0, 'type': 'integer'}, {'exclusiveMinimum': 0, 'type': 'number'}],
            },
        ),
        (
            List[int],
            dict(gt=0),
            {'title': 'A', 'exclusiveMinimum': 0, 'type': 'array', 'items': {'exclusiveMinimum': 0, 'type': 'integer'}},
        ),
        (
            Dict[str, int],
            dict(gt=0),
            {
                'title': 'A',
                'exclusiveMinimum': 0,
                'type': 'object',
                'additionalProperties': {'exclusiveMinimum': 0, 'type': 'integer'},
            },
        ),
        (
            Union[str, int],
            dict(gt=0, max_length=5),
            {'title': 'A', 'anyOf': [{'maxLength': 5, 'type': 'string'}, {'exclusiveMinimum': 0, 'type': 'integer'}]},
        ),
    ],
)
def test_enforced_constraints(annotation, kwargs, field_schema):
    class Model(BaseModel):
        a: annotation = Field(..., **kwargs)

    schema = Model.schema()
    # debug(schema['properties']['a'])
    assert schema['properties']['a'] == field_schema


def test_real_vs_phony_constraints():
    class Model1(BaseModel):
        foo: int = Field(..., gt=123)

        class Config:
            title = 'Test Model'

    class Model2(BaseModel):
        foo: int = Field(..., exclusiveMinimum=123)

        class Config:
            title = 'Test Model'

    with pytest.raises(ValidationError, match='ensure this value is greater than 123'):
        Model1(foo=122)

    assert Model2(foo=122).dict() == {'foo': 122}

    assert (
        Model1.schema()
        == Model2.schema()
        == {
            'title': 'Test Model',
            'type': 'object',
            'properties': {'foo': {'title': 'Foo', 'exclusiveMinimum': 123, 'type': 'integer'}},
            'required': ['foo'],
        }
    )


def test_subfield_field_info():
    class MyModel(BaseModel):
        entries: Dict[str, List[int]]

    assert MyModel.schema() == {
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

    assert schema([Model]) == {
        'definitions': {
            'Model': {
                'title': 'Model',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'boolean'}},
                'required': ['a'],
            }
        }
    }

    assert model_schema(Model) == {
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

    assert Example.schema() == {
        'title': 'Example',
        'type': 'object',
        'properties': {'example': {'$ref': '#/definitions/ExampleEnum'}},
        'required': ['example'],
        'definitions': {
            'ExampleEnum': {
                'title': 'ExampleEnum',
                'description': 'This is a test description.',
                'enum': ['GT', 'LT', 'GE', 'LE', 'ML', 'MO', 'RE'],
            }
        },
    }


def test_model_process_schema_enum():
    class SpamEnum(str, Enum):
        foo = 'f'
        bar = 'b'

    model_schema, _, _ = model_process_schema(SpamEnum, model_name_map={})
    assert model_schema == {'title': 'SpamEnum', 'description': 'An enumeration.', 'type': 'string', 'enum': ['f', 'b']}


def test_path_modify_schema():
    class MyPath(Path):
        @classmethod
        def __modify_schema__(cls, schema):
            schema.update(foobar=123)

    class Model(BaseModel):
        path1: Path
        path2: MyPath
        path3: List[MyPath]

    assert Model.schema() == {
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

    assert Model.schema() == {
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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'array', 'items': {'type': 'integer'}}},
        'required': ['a'],
    }


def test_new_type():
    new_type = NewType('NewStr', str)

    class Model(BaseModel):
        a: new_type

    assert Model.schema() == {
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

    models = [module.ModelOne, module.ModelTwo, module.NestedModel]
    model_names = set(schema(models)['definitions'].keys())
    expected_model_names = {
        'ModelOne',
        'ModelTwo',
        f'{module.__name__}__ModelOne__NestedModel',
        f'{module.__name__}__ModelTwo__NestedModel',
        f'{module.__name__}__NestedModel',
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

    assert len(Model.schema()['definitions']) == 4
    assert set(Model.schema()['definitions']) == {
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

    class Model(BaseModel):
        data: GenModel[str]
        data1: GenModel

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'data': {'allOf': [{'type': 'string'}], 'title': 'Data'},
            'data1': {
                'title': 'Data1',
            },
        },
        'required': ['data', 'data1'],
    }

    class GenModelModified(GenModel, Generic[T]):
        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema.pop('allOf', None)
            field_schema.update(anyOf=[{'type': 'string'}, {'type': 'array', 'items': {'type': 'string'}}])

    class ModelModified(BaseModel):
        data: GenModelModified[str]
        data1: GenModelModified

    assert ModelModified.schema() == {
        'title': 'ModelModified',
        'type': 'object',
        'properties': {
            'data': {'title': 'Data', 'anyOf': [{'type': 'string'}, {'type': 'array', 'items': {'type': 'string'}}]},
            'data1': {'title': 'Data1', 'anyOf': [{'type': 'string'}, {'type': 'array', 'items': {'type': 'string'}}]},
        },
        'required': ['data', 'data1'],
    }


def test_namedtuple_default():
    class Coordinates(NamedTuple):
        x: float
        y: float

    class LocationBase(BaseModel):
        coords: Coordinates = Coordinates(0, 0)

    assert LocationBase.schema() == {
        'title': 'LocationBase',
        'type': 'object',
        'properties': {
            'coords': {
                'title': 'Coords',
                'default': Coordinates(x=0, y=0),
                'type': 'array',
                'items': [{'title': 'X', 'type': 'number'}, {'title': 'Y', 'type': 'number'}],
                'minItems': 2,
                'maxItems': 2,
            }
        },
    }


def test_advanced_generic_schema():
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
        def __modify_schema__(cls, field_schema):
            the_type = field_schema.pop('allOf', [{'type': 'string'}])[0]
            field_schema.update(title='Gen title', anyOf=[the_type, {'type': 'array', 'items': the_type}])

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
        def __modify_schema__(cls, field_schema):
            field_schema.update(examples='examples')

    class CustomType(Enum):
        A = 'a'
        B = 'b'

        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema.update(title='CustomType title', type='string')

    class Model(BaseModel):
        data0: Gen
        data1: Gen[CustomType] = Field(title='Data1 title', description='Data 1 description')
        data2: GenTwoParams[CustomType, UUID4] = Field(title='Data2 title', description='Data 2')
        # check Tuple because changes in code touch that type
        data3: Tuple
        data4: Tuple[CustomType]
        data5: Tuple[CustomType, str]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'data0': {
                'anyOf': [{'type': 'string'}, {'items': {'type': 'string'}, 'type': 'array'}],
                'title': 'Gen title',
            },
            'data1': {
                'title': 'Gen title',
                'description': 'Data 1 description',
                'anyOf': [
                    {'$ref': '#/definitions/CustomType'},
                    {'type': 'array', 'items': {'$ref': '#/definitions/CustomType'}},
                ],
            },
            'data2': {
                'allOf': [
                    {
                        'items': [{'$ref': '#/definitions/CustomType'}, {'format': 'uuid4', 'type': 'string'}],
                        'type': 'array',
                    }
                ],
                'title': 'Data2 title',
                'description': 'Data 2',
                'examples': 'examples',
            },
            'data3': {'title': 'Data3', 'type': 'array', 'items': {}},
            'data4': {
                'title': 'Data4',
                'type': 'array',
                'items': [{'$ref': '#/definitions/CustomType'}],
                'minItems': 1,
                'maxItems': 1,
            },
            'data5': {
                'title': 'Data5',
                'type': 'array',
                'items': [{'$ref': '#/definitions/CustomType'}, {'type': 'string'}],
                'minItems': 2,
                'maxItems': 2,
            },
        },
        'required': ['data0', 'data1', 'data2', 'data3', 'data4', 'data5'],
        'definitions': {
            'CustomType': {
                'title': 'CustomType title',
                'description': 'An enumeration.',
                'enum': ['a', 'b'],
                'type': 'string',
            }
        },
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
        ref: Ref['Model']  # noqa

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'definitions': {
            'Ref': {
                'title': 'Ref',
                'type': 'object',
                'properties': {
                    'uuid': {'title': 'Uuid', 'type': 'string'},
                },
                'required': ['uuid'],
            },
        },
        'properties': {
            'ref': {'$ref': '#/definitions/Ref'},
        },
        'required': ['ref'],
    }


def test_nested_generic_model():
    """
    Test a nested GenericModel
    """

    class Box(GenericModel, Generic[T]):
        uuid: str
        data: T

    class Model(BaseModel):
        box_str: Box[str]
        box_int: Box[int]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'definitions': {
            'Box_str_': Box[str].schema(),
            'Box_int_': Box[int].schema(),
        },
        'properties': {
            'box_str': {'$ref': '#/definitions/Box_str_'},
            'box_int': {'$ref': '#/definitions/Box_int_'},
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
        model: Union[Ref['Model'], 'Model']  # noqa

        def resolve(self) -> 'Model':  # noqa
            ...

    Model.update_forward_refs()

    assert Model.schema() == {
        'definitions': {
            'Model': {
                'title': 'Model',
                'type': 'object',
                'properties': {
                    'uuid': {'title': 'Uuid', 'type': 'string'},
                    'model': {
                        'title': 'Model',
                        'anyOf': [
                            {'$ref': '#/definitions/Ref'},
                            {'$ref': '#/definitions/Model'},
                        ],
                    },
                },
                'required': ['uuid', 'model'],
            },
            'Ref': {
                'title': 'Ref',
                'type': 'object',
                'properties': {
                    'uuid': {'title': 'Uuid', 'type': 'string'},
                },
                'required': ['uuid'],
            },
        },
        '$ref': '#/definitions/Model',
    }


def test_schema_with_field_parameter():
    class RestrictedAlphabetStr(str):
        @classmethod
        def __modify_schema__(cls, field_schema, field: Optional[ModelField]):
            assert isinstance(field, ModelField)
            alphabet = field.field_info.extra['alphabet']
            field_schema['examples'] = [c * 3 for c in alphabet]

    class MyModel(BaseModel):
        value: RestrictedAlphabetStr = Field(alphabet='ABC')

    assert MyModel.schema() == {
        'title': 'MyModel',
        'type': 'object',
        'properties': {
            'value': {'title': 'Value', 'alphabet': 'ABC', 'examples': ['AAA', 'BBB', 'CCC'], 'type': 'string'}
        },
        'required': ['value'],
    }


def test_discriminated_union():
    class BlackCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['black']

    class WhiteCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['white']

    class Cat(BaseModel):
        __root__: Union[BlackCat, WhiteCat] = Field(..., discriminator='color')

    class Dog(BaseModel):
        pet_type: Literal['dog']

    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']

    class Model(BaseModel):
        pet: Union[Cat, Dog, Lizard] = Field(..., discriminator='pet_type')

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'pet': {
                'title': 'Pet',
                'discriminator': {
                    'propertyName': 'pet_type',
                    'mapping': {
                        'cat': '#/definitions/Cat',
                        'dog': '#/definitions/Dog',
                        'reptile': '#/definitions/Lizard',
                        'lizard': '#/definitions/Lizard',
                    },
                },
                'oneOf': [
                    {'$ref': '#/definitions/Cat'},
                    {'$ref': '#/definitions/Dog'},
                    {'$ref': '#/definitions/Lizard'},
                ],
            }
        },
        'required': ['pet'],
        'definitions': {
            'BlackCat': {
                'title': 'BlackCat',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['black'], 'type': 'string'},
                },
                'required': ['pet_type', 'color'],
            },
            'WhiteCat': {
                'title': 'WhiteCat',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['white'], 'type': 'string'},
                },
                'required': ['pet_type', 'color'],
            },
            'Cat': {
                'title': 'Cat',
                'discriminator': {
                    'propertyName': 'color',
                    'mapping': {'black': '#/definitions/BlackCat', 'white': '#/definitions/WhiteCat'},
                },
                'oneOf': [{'$ref': '#/definitions/BlackCat'}, {'$ref': '#/definitions/WhiteCat'}],
            },
            'Dog': {
                'title': 'Dog',
                'type': 'object',
                'properties': {'pet_type': {'title': 'Pet Type', 'enum': ['dog'], 'type': 'string'}},
                'required': ['pet_type'],
            },
            'Lizard': {
                'title': 'Lizard',
                'type': 'object',
                'properties': {'pet_type': {'title': 'Pet Type', 'enum': ['reptile', 'lizard'], 'type': 'string'}},
                'required': ['pet_type'],
            },
        },
    }


def test_discriminated_annotated_union():
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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'pet': {
                'title': 'Pet',
                'discriminator': {
                    'propertyName': 'pet_type',
                    'mapping': {
                        'cat': {
                            'BlackCatWithHeight': {'$ref': '#/definitions/BlackCatWithHeight'},
                            'BlackCatWithWeight': {'$ref': '#/definitions/BlackCatWithWeight'},
                            'WhiteCat': {'$ref': '#/definitions/WhiteCat'},
                        },
                        'dog': '#/definitions/Dog',
                    },
                },
                'oneOf': [
                    {
                        'oneOf': [
                            {
                                'oneOf': [
                                    {'$ref': '#/definitions/BlackCatWithHeight'},
                                    {'$ref': '#/definitions/BlackCatWithWeight'},
                                ]
                            },
                            {'$ref': '#/definitions/WhiteCat'},
                        ]
                    },
                    {'$ref': '#/definitions/Dog'},
                ],
            },
            'number': {'title': 'Number', 'type': 'integer'},
        },
        'required': ['pet', 'number'],
        'definitions': {
            'BlackCatWithHeight': {
                'title': 'BlackCatWithHeight',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['black'], 'type': 'string'},
                    'info': {'title': 'Info', 'enum': ['height'], 'type': 'string'},
                    'black_infos': {'title': 'Black Infos', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'info', 'black_infos'],
            },
            'BlackCatWithWeight': {
                'title': 'BlackCatWithWeight',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['black'], 'type': 'string'},
                    'info': {'title': 'Info', 'enum': ['weight'], 'type': 'string'},
                    'black_infos': {'title': 'Black Infos', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'info', 'black_infos'],
            },
            'WhiteCat': {
                'title': 'WhiteCat',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['white'], 'type': 'string'},
                    'white_infos': {'title': 'White Infos', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'white_infos'],
            },
            'Dog': {
                'title': 'Dog',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['dog'], 'type': 'string'},
                    'dog_name': {'title': 'Dog Name', 'type': 'string'},
                },
                'required': ['pet_type', 'dog_name'],
            },
        },
    }


def test_discriminated_annotated_union_enum():
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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'pet': {
                'title': 'Pet',
                'discriminator': {
                    'propertyName': 'pet_type',
                    'mapping': {
                        'cat': {
                            'BlackCatWithHeight': {'$ref': '#/definitions/BlackCatWithHeight'},
                            'BlackCatWithWeight': {'$ref': '#/definitions/BlackCatWithWeight'},
                            'WhiteCat': {'$ref': '#/definitions/WhiteCat'},
                        },
                        'dog': '#/definitions/Dog',
                    },
                },
                'oneOf': [
                    {
                        'oneOf': [
                            {
                                'oneOf': [
                                    {'$ref': '#/definitions/BlackCatWithHeight'},
                                    {'$ref': '#/definitions/BlackCatWithWeight'},
                                ]
                            },
                            {'$ref': '#/definitions/WhiteCat'},
                        ]
                    },
                    {'$ref': '#/definitions/Dog'},
                ],
            },
            'number': {'title': 'Number', 'type': 'integer'},
        },
        'required': ['pet', 'number'],
        'definitions': {
            'BlackCatWithHeight': {
                'title': 'BlackCatWithHeight',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['black'], 'type': 'string'},
                    'info': {'title': 'Info', 'enum': [0], 'type': 'integer'},
                    'black_infos': {'title': 'Black Infos', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'info', 'black_infos'],
            },
            'BlackCatWithWeight': {
                'title': 'BlackCatWithWeight',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['black'], 'type': 'string'},
                    'info': {'title': 'Info', 'enum': [1], 'type': 'integer'},
                    'black_infos': {'title': 'Black Infos', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'info', 'black_infos'],
            },
            'WhiteCat': {
                'title': 'WhiteCat',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['white'], 'type': 'string'},
                    'white_infos': {'title': 'White Infos', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'white_infos'],
            },
            'Dog': {
                'title': 'Dog',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['dog'], 'type': 'string'},
                    'dog_name': {'title': 'Dog Name', 'type': 'string'},
                },
                'required': ['pet_type', 'dog_name'],
            },
        },
    }


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

    assert Model.schema() == {
        'type': 'object',
        'title': 'Model',
        'properties': {
            'number': {'title': 'Number', 'type': 'integer'},
            'pet': {
                'oneOf': [{'$ref': '#/definitions/Cat'}, {'$ref': '#/definitions/Dog'}],
                'discriminator': {
                    'mapping': {'cat': '#/definitions/Cat', 'dog': '#/definitions/Dog'},
                    'propertyName': 'typeOfPet',
                },
                'title': 'Pet',
            },
        },
        'required': ['pet', 'number'],
        'definitions': {
            'Cat': {
                'properties': {
                    'c': {'title': 'C', 'type': 'string'},
                    'typeOfPet': {'enum': ['cat'], 'title': 'Typeofpet', 'type': 'string'},
                },
                'required': ['typeOfPet', 'c'],
                'title': 'Cat',
                'type': 'object',
            },
            'Dog': {
                'properties': {
                    'd': {'title': 'D', 'type': 'string'},
                    'typeOfPet': {'enum': ['dog'], 'title': 'Typeofpet', 'type': 'string'},
                },
                'required': ['typeOfPet', 'd'],
                'title': 'Dog',
                'type': 'object',
            },
        },
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
        child: List[ChildModel]

    assert model_schema(dataclass(NestedModel)) == {
        'title': 'NestedModel',
        'type': 'object',
        'properties': {'child': {'title': 'Child', 'type': 'array', 'items': {'$ref': '#/definitions/ChildModel'}}},
        'required': ['child'],
        'definitions': {
            'ChildModel': {
                'title': 'ChildModel',
                'type': 'object',
                'properties': {'name': {'title': 'Name', 'type': 'string'}},
                'required': ['name'],
            }
        },
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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'pets': {
                'title': 'Pets',
                'discriminator': {
                    'propertyName': 'pet_type',
                    'mapping': {
                        'cat': {
                            'BlackCat': {'$ref': '#/definitions/BlackCat'},
                            'WhiteCat': {'$ref': '#/definitions/WhiteCat'},
                        },
                        'dog': '#/definitions/Dog',
                    },
                },
                'oneOf': [
                    {
                        'oneOf': [
                            {'$ref': '#/definitions/BlackCat'},
                            {'$ref': '#/definitions/WhiteCat'},
                        ],
                    },
                    {'$ref': '#/definitions/Dog'},
                ],
            },
            'n': {'title': 'N', 'type': 'integer'},
        },
        'required': ['pets', 'n'],
        'definitions': {
            'BlackCat': {
                'title': 'BlackCat',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['black'], 'type': 'string'},
                    'black_name': {'title': 'Black Name', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'black_name'],
            },
            'WhiteCat': {
                'title': 'WhiteCat',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['cat'], 'type': 'string'},
                    'color': {'title': 'Color', 'enum': ['white'], 'type': 'string'},
                    'white_name': {'title': 'White Name', 'type': 'string'},
                },
                'required': ['pet_type', 'color', 'white_name'],
            },
            'Dog': {
                'title': 'Dog',
                'type': 'object',
                'properties': {
                    'pet_type': {'title': 'Pet Type', 'enum': ['dog'], 'type': 'string'},
                    'name': {'title': 'Name', 'type': 'string'},
                },
                'required': ['pet_type', 'name'],
            },
        },
    }


def test_extra_inheritance():
    class A(BaseModel):
        root: Optional[str]

        class Config:
            fields = {
                'root': {'description': 'root path of data', 'level': 1},
            }

    class Model(A):
        root: str = Field('asa', description='image height', level=3)

    m = Model()
    assert m.schema()['properties'] == {
        'root': {
            'title': 'Root',
            'type': 'string',
            'description': 'image height',
            'default': 'asa',
            'level': 3,
        }
    }


def test_model_with_type_attributes():
    class Foo:
        a: float

    class Bar(BaseModel):
        b: int

    class Baz(BaseModel):
        a: Type[Foo]
        b: Type[Bar]

    assert Baz.schema() == {
        'title': 'Baz',
        'type': 'object',
        'properties': {'a': {'title': 'A'}, 'b': {'title': 'B'}},
        'required': ['a', 'b'],
    }


@pytest.mark.parametrize(
    'regex_val',
    [
        '^text$',
        re.compile('^text$'),
    ],
)
def test_constrained_str_class_dict(regex_val: Union[str, Pattern[str]]):
    class CustomStr(ConstrainedStr):
        regex = regex_val

    class Model(BaseModel):
        a: Dict[CustomStr, Any]

    json_schema = Model.schema()

    assert json_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'patternProperties': {'^text$': {}}, 'title': 'A', 'type': 'object'}},
        'required': ['a'],
    }
