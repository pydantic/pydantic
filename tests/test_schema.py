import json
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pytest

from pydantic import BaseModel, Schema, ValidationError


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
        'properties': {
            'a': {'type': 'integer', 'title': 'A'},
            'b': {
                'type': 'object',
                'title': 'Foo',
                'description': 'hello',
                'properties': {'b': {'type': 'number', 'title': 'B'}},
                'required': ['b'],
            },
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

    with pytest.raises(TypeError):
        json.dumps(Model.schema())

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
        'properties': {
            'b': {
                'type': 'array',
                'items': {
                    'title': 'Foo',
                    'type': 'object',
                    'properties': {'a': {'type': 'number', 'title': 'A'}},
                    'required': ['a'],
                },
                'title': 'B',
            }
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
        'properties': {
            'a': {'title': 'A', 'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            'b': {'title': 'B', 'type': 'array', 'items': {'type': 'integer'}},
            'c': {
                'title': 'C',
                'type': 'object',
                'additionalProperties': {
                    'title': 'Foo',
                    'type': 'object',
                    'properties': {'a': {'title': 'A', 'type': 'number'}},
                    'required': ['a'],
                },
            },
            'd': {
                'title': 'Foo',
                'type': 'object',
                'properties': {'a': {'title': 'A', 'type': 'number'}},
                'required': ['a'],
            },
            'e': {'title': 'E', 'type': 'object'},
        },
        'required': ['a', 'b', 'c', 'e'],
    }
