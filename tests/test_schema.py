import json
from decimal import Decimal
from enum import Enum, IntEnum

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
        'title': 'ApplePie',
        'description': 'This is a test.',
        'properties': {
            'a': {
                'type': 'float',
                'required': True,
                'title': 'A',
            },
            'b': {
                'type': 'int',
                'required': False,
                'title': 'B',
                'default': 10,
            },
        },
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
            'Snap': {
                'type': 'float',
                'required': True,
                'title': 'Snap',
            },
            'Crackle': {
                'type': 'int',
                'required': False,
                'title': 'Crackle',
                'default': 10,
            },
        },
    }
    assert ApplePie.schema() == s
    assert ApplePie.schema() == s
    assert list(ApplePie.schema(by_alias=True)['properties'].keys()) == ['Snap', 'Crackle']
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
            'a': {
                'type': 'int',
                'title': 'A',
                'required': True,
            },
            'b': {
                'type': 'object',
                'title': 'Foo',
                'properties': {
                    'b': {
                        'type': 'float',
                        'title': 'B',
                        'required': True,
                    },
                },
                'description': 'hello',
                'required': False,
            },
        },
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
            'foo': {
                'type': 'int',
                'title': 'Foo is Great',
                'required': False,
                'default': 4,
            },
            'bar': {
                'type': 'str',
                'title': 'Bar',
                'required': True,
                'description': 'this description of bar',
            },
        },
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
        spam: SpamEnum = Schema(None, choice_names={'f': 'Sausage'})

    assert Model.schema() == {
        'type': 'object',
        'title': 'Model',
        'properties': {
            'foo': {
                'type': 'enum',
                'title': 'Foo',
                'required': True,
                'choices': [
                    ('f', 'Foo'),
                    ('b', 'Bar'),
                ],
            },
            'bar': {
                'type': 'int',
                'title': 'Bar',
                'required': True,
                'choices': [
                    (1, 'Foo'),
                    (2, 'Bar'),
                ],
            },
            'spam': {
                'type': 'str',
                'title': 'Spam',
                'required': False,
                'choices': [
                    ('f', 'Sausage'),
                    ('b', 'Bar'),
                ],
            },
        },
    }


def test_json_schema():
    class Model(BaseModel):
        a = b'foobar'
        b = Decimal('12.34')

    with pytest.raises(TypeError):
        json.dumps(Model.schema())

    assert Model.schema_json(indent=2) == (
        '{\n'
        '  "type": "object",\n'
        '  "title": "Model",\n'
        '  "properties": {\n'
        '    "a": {\n'
        '      "type": "bytes",\n'
        '      "title": "A",\n'
        '      "required": false,\n'
        '      "default": "foobar"\n'
        '    },\n'
        '    "b": {\n'
        '      "type": "Decimal",\n'
        '      "title": "B",\n'
        '      "required": false,\n'
        '      "default": 12.34\n'
        '    }\n'
        '  }\n'
        '}'
    )
