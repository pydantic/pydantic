from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

import pytest

from pydantic import BaseModel, Schema, ValidationError
from pydantic.schema import get_flat_models_from_model, get_flat_models_from_models, get_model_name_maps, schema
from pydantic.types import (
    DSN,
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    ConstrainedDecimal,
    ConstrainedFloat,
    ConstrainedInt,
    ConstrainedStr,
    DirectoryPath,
    EmailStr,
    FilePath,
    Json,
    NameEmail,
    NegativeFloat,
    NegativeInt,
    NoneBytes,
    NoneStr,
    NoneStrBytes,
    PositiveFloat,
    PositiveInt,
    StrBytes,
    StrictStr,
    UrlStr,
    condecimal,
    confloat,
    conint,
    constr,
    urlstr,
)

from .schema_test_package.modulea.modela import Model as ModelA
from .schema_test_package.moduleb.modelb import Model as ModelB
from .schema_test_package.modulec.modelc import Model as ModelC
from .schema_test_package.moduled.modeld import Model as ModelD


def test_key():
    class ApplePie(BaseModel):
        """
        This is a test.
        """

        a: float
        b: int = 10

    s = {
        'type': 'object',
        'properties': {
            'a': {'type': 'number', 'title': 'A'},
            'b': {'type': 'integer', 'title': 'B', 'default': 10},
        },
        'required': ['a'],
        'title': 'ApplePie',
        'description': 'This is a test.',
    }
    assert True not in ApplePie._schema_cache
    assert False not in ApplePie._schema_cache
    assert ApplePie.schema() == s
    assert True in ApplePie._schema_cache
    assert False not in ApplePie._schema_cache
    assert ApplePie.schema() == s


def test_by_alias():
    class ApplePie(BaseModel):
        a: float
        b: int = 10

        class Config:
            title = 'Apple Pie'
            fields = {'a': 'Snap', 'b': 'Crackle'}

    s = {
        'type': 'object',
        'title': 'Apple Pie',
        'properties': {
            'Snap': {'type': 'number', 'title': 'Snap'},
            'Crackle': {'type': 'integer', 'title': 'Crackle', 'default': 10},
        },
        'required': ['Snap'],
    }
    assert ApplePie.schema() == s
    assert list(ApplePie.schema(by_alias=True)['properties'].keys()) == [
        'Snap',
        'Crackle',
    ]
    assert list(ApplePie.schema(by_alias=False)['properties'].keys()) == ['a', 'b']


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
        'properties': {
            'a': {'type': 'integer', 'title': 'A'},
            'b': {'$ref': '#/definitions/Foo'},
        },
        'required': ['a'],
    }


def test_schema_class():
    class Model(BaseModel):
        foo: int = Schema(4, title='Foo is Great')
        bar: str = Schema(..., description='this description of bar')

    with pytest.raises(ValidationError):
        Model()

    m = Model(bar=123)
    assert m.dict() == {'foo': 4, 'bar': '123'}

    assert Model.schema() == {
        'type': 'object',
        'title': 'Model',
        'properties': {
            'foo': {'type': 'integer', 'title': 'Foo is Great', 'default': 4},
            'bar': {
                'type': 'string',
                'title': 'Bar',
                'description': 'this description of bar',
            },
        },
        'required': ['bar'],
    }


def test_schema_class_by_alias():
    class Model(BaseModel):
        foo: int = Schema(4, alias='foofoo')

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
        spam: SpamEnum = Schema(None)

    assert Model.schema() == {
        'type': 'object',
        'title': 'Model',
        'properties': {
            'foo': {'title': 'Foo', 'enum': ['f', 'b']},
            'bar': {'type': 'integer', 'title': 'Bar', 'enum': [1, 2]},
            'spam': {'type': 'string', 'title': 'Spam', 'enum': ['f', 'b']},
        },
        'required': ['foo', 'bar'],
    }


def test_json_schema():
    class Model(BaseModel):
        a = b'foobar'
        b = Decimal('12.34')

    assert Model.schema_json(indent=2) == (
        '{\n'
        '  "title": "Model",\n'
        '  "type": "object",\n'
        '  "properties": {\n'
        '    "a": {\n'
        '      "title": "A",\n'
        '      "default": "foobar",\n'
        '      "type": "string",\n'
        '      "format": "binary"\n'
        '    },\n'
        '    "b": {\n'
        '      "title": "B",\n'
        '      "default": 12.34,\n'
        '      "type": "number"\n'
        '    }\n'
        '  }\n'
        '}'
    )


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
        'properties': {
            'b': {'type': 'array', 'items': {'$ref': '#/definitions/Foo'}, 'title': 'B'}
        },
        'required': ['b'],
    }


def test_optional():
    class Model(BaseModel):
        a: Optional[str]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'type': 'string', 'title': 'A'}},
    }


def test_any():
    class Model(BaseModel):
        a: Any

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A'}},
        'required': ['a'],
    }


def test_set():
    class Model(BaseModel):
        a: Set[int]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {
                'title': 'A',
                'type': 'array',
                'uniqueItems': True,
                'items': {'type': 'integer'},
            }
        },
        'required': ['a'],
    }


def test_tuple():
    class Model(BaseModel):
        a: Tuple[str, int, Union[str, int, float], float]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {
                'title': 'A',
                'type': 'array',
                'items': [
                    {'type': 'string'},
                    {'type': 'integer'},
                    {
                        'anyOf': [
                            {'type': 'string'},
                            {'type': 'integer'},
                            {'type': 'number'},
                        ]
                    },
                    {'type': 'number'},
                ],
            }
        },
        'required': ['a'],
    }


def test_list_union_dict():
    class Foo(BaseModel):
        a: float

    class Model(BaseModel):
        """party time"""

        a: Union[int, str]
        b: List[int]
        c: Dict[str, Foo]
        d: Union[None, Foo]
        e: Dict[str, Any]

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'description': 'party time',
        'type': 'object',
        'definitions': {
            'Foo': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'number'}},
                'required': ['a'],
            }
        },
        'properties': {
            'a': {'title': 'A', 'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            'b': {'title': 'B', 'type': 'array', 'items': {'type': 'integer'}},
            'c': {
                'title': 'C',
                'type': 'object',
                'additionalProperties': {'$ref': '#/definitions/Foo'},
            },
            'd': {'$ref': '#/definitions/Foo'},
            'e': {'title': 'E', 'type': 'object'},
        },
        'required': ['a', 'b', 'c', 'e'],
    }


def test_date_types():
    class Model(BaseModel):
        a: datetime
        b: date
        c: time
        d: timedelta

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'string', 'format': 'date-time'},
            'b': {'title': 'B', 'type': 'string', 'format': 'date'},
            'c': {'title': 'C', 'type': 'string', 'format': 'time'},
            'd': {'title': 'D', 'type': 'string', 'format': 'time-delta'},
        },
        'required': ['a', 'b', 'c', 'd'],
    }


def test_str_basic_types():
    class Model(BaseModel):
        a: NoneStr
        b: NoneBytes
        c: StrBytes
        d: NoneStrBytes

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'string'},
            'b': {'title': 'B', 'type': 'string', 'format': 'binary'},
            'c': {
                'title': 'C',
                'anyOf': [{'type': 'string'}, {'type': 'string', 'format': 'binary'}],
            },
            'd': {
                'title': 'D',
                'anyOf': [{'type': 'string'}, {'type': 'string', 'format': 'binary'}],
            },
        },
        'required': ['c'],
    }


def test_str_constrained_types():
    class Model(BaseModel):
        a: StrictStr
        b: ConstrainedStr
        c: constr(min_length=3, max_length=5, regex='^text$')

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'string'},
            'b': {'title': 'B', 'type': 'string'},
            'c': {
                'title': 'C',
                'type': 'string',
                'minLength': 3,
                'maxLength': 5,
                'pattern': '^text$',
            },
        },
        'required': ['a', 'b', 'c'],
    }


def test_special_str_types():
    class Model(BaseModel):
        a: EmailStr
        b: UrlStr
        c: urlstr(min_length=5, max_length=10)
        d: NameEmail
        e: DSN

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'string', 'format': 'email'},
            'b': {
                'title': 'B',
                'type': 'string',
                'format': 'uri',
                'minLength': 1,
                'maxLength': 2 ** 16,
            },
            'c': {
                'title': 'C',
                'type': 'string',
                'format': 'uri',
                'minLength': 5,
                'maxLength': 10,
            },
            'd': {'title': 'D', 'type': 'string', 'format': 'name-email'},
            'e': {'title': 'E', 'type': 'string', 'format': 'dsn'},
        },
        'required': ['a', 'b', 'c', 'd', 'e'],
    }


def test_special_int_types():
    class Model(BaseModel):
        a: ConstrainedInt
        b: conint(gt=5, lt=10)
        c: conint(ge=5, le=10)
        d: PositiveInt
        e: NegativeInt

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'integer'},
            'b': {
                'title': 'B',
                'type': 'integer',
                'exclusiveMinimum': 5,
                'exclusiveMaximum': 10,
            },
            'c': {'title': 'C', 'type': 'integer', 'minimum': 5, 'maximum': 10},
            'd': {'title': 'D', 'type': 'integer', 'exclusiveMinimum': 0},
            'e': {'title': 'E', 'type': 'integer', 'exclusiveMaximum': 0},
        },
        'required': ['a', 'b', 'c', 'd', 'e'],
    }


def test_special_float_types():
    class Model(BaseModel):
        a: ConstrainedFloat
        b: confloat(gt=5, lt=10)
        c: confloat(ge=5, le=10)
        d: PositiveFloat
        e: NegativeFloat
        f: ConstrainedDecimal
        g: condecimal(gt=5, lt=10)
        h: condecimal(ge=5, le=10)

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'number'},
            'b': {
                'title': 'B',
                'type': 'number',
                'exclusiveMinimum': 5,
                'exclusiveMaximum': 10,
            },
            'c': {'title': 'C', 'type': 'number', 'minimum': 5, 'maximum': 10},
            'd': {'title': 'D', 'type': 'number', 'exclusiveMinimum': 0},
            'e': {'title': 'E', 'type': 'number', 'exclusiveMaximum': 0},
            'f': {'title': 'F', 'type': 'number'},
            'g': {
                'title': 'G',
                'type': 'number',
                'exclusiveMinimum': 5,
                'exclusiveMaximum': 10,
            },
            'h': {'title': 'H', 'type': 'number', 'minimum': 5, 'maximum': 10},
        },
        'required': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
    }


def test_uuid_types():
    class Model(BaseModel):
        a: UUID
        b: UUID1
        c: UUID3
        d: UUID4
        e: UUID5

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'string', 'format': 'uuid'},
            'b': {'title': 'B', 'type': 'string', 'format': 'uuid1'},
            'c': {'title': 'C', 'type': 'string', 'format': 'uuid3'},
            'd': {'title': 'D', 'type': 'string', 'format': 'uuid4'},
            'e': {'title': 'E', 'type': 'string', 'format': 'uuid5'},
        },
        'required': ['a', 'b', 'c', 'd', 'e'],
    }


def test_path_types():
    class Model(BaseModel):
        a: FilePath
        b: DirectoryPath

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'string', 'format': 'file-path'},
            'b': {'title': 'B', 'type': 'string', 'format': 'directory-path'},
        },
        'required': ['a', 'b'],
    }


def test_json_type():
    class Model(BaseModel):
        a: Json

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'format': 'json-string'}},
        'required': ['a'],
    }


def test_flat_models_unique_models():
    flat_models = get_flat_models_from_models([ModelA, ModelB, ModelC])
    assert flat_models == set([ModelA, ModelB])


def test_flat_models_with_submodels():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: List[Foo]

    class Baz(BaseModel):
        c: Dict[str, Bar]

    flat_models = get_flat_models_from_model(Baz)
    assert flat_models == set([Foo, Bar, Baz])


def test_flat_models_with_submodels_from_sequence():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    class Ingredient(BaseModel):
        name: str

    class Pizza(BaseModel):
        name: str
        ingredients: List[Ingredient]

    flat_models = get_flat_models_from_models([Baz, Pizza])
    assert flat_models == set([Foo, Bar, Baz, Ingredient, Pizza])


def test_model_name_maps():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    flat_models = get_flat_models_from_models([Baz, ModelA, ModelB, ModelC, ModelD])
    name_model_map, model_name_map = get_model_name_maps(flat_models)
    assert name_model_map == {
        'Foo': Foo,
        'Bar': Bar,
        'Baz': Baz,
        'tests__schema_test_package__modulea__modela__Model': ModelA,
        'tests__schema_test_package__moduleb__modelb__Model': ModelB,
        'tests__schema_test_package__moduled__modeld__Model': ModelD,
    }
    assert model_name_map == {
        Foo: 'Foo',
        Bar: 'Bar',
        Baz: 'Baz',
        ModelA: 'tests__schema_test_package__modulea__modela__Model',
        ModelB: 'tests__schema_test_package__moduleb__modelb__Model',
        ModelD: 'tests__schema_test_package__moduled__modeld__Model',
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
            'Bar': {
                'title': 'Bar',
                'type': 'object',
                'properties': {
                    'b': {
                        'title': 'Foo',
                        'type': 'object',
                        'properties': {'a': {'title': 'A', 'type': 'string'}},
                        'required': ['a'],
                        'default': {'a': 'foo'},
                    }
                },
            },
            'Baz': {
                'title': 'Baz',
                'type': 'object',
                'properties': {'c': {'$ref': '#/definitions/Bar'}},
            },
        },
        'properties': {'d': {'$ref': '#/definitions/Baz'}},
        'required': ['d'],
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
        [Model, Pizza],
        title='Multi-model schema',
        description='Single JSON Schema with multiple definitions',
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


def test_schema_with_ref_prefix():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    model_schema = schema(
        [Bar, Baz],
        title='Multi-model schema',
        description='Custom prefix for $ref fields',
        ref_prefix='#/components/schemas/',  # OpenAPI style
    )
    assert model_schema == {
        'title': 'Multi-model schema',
        'description': 'Custom prefix for $ref fields',
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
        },
    }
