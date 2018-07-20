import json
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Set, Tuple, Union

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
                'title': 'B',
                'properties': {
                    'b': {
                        'type': 'float',
                        'title': 'B',
                        'required': True,
                    },
                },
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
        '  "title": "Model",\n'
        '  "type": "object",\n'
        '  "properties": {\n'
        '    "a": {\n'
        '      "title": "A",\n'
        '      "required": false,\n'
        '      "default": "foobar",\n'
        '      "type": "bytes"\n'
        '    },\n'
        '    "b": {\n'
        '      "title": "B",\n'
        '      "required": false,\n'
        '      "default": 12.34,\n'
        '      "type": "Decimal"\n'
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
                'type': 'list',
                'item_type': {
                    'type': 'object',
                    'properties': {
                        'a': {
                            'type': 'float',
                            'title': 'A',
                            'required': True,
                        },
                    },
                },
                'title': 'B',
                'required': True,
            },
        },
    }


def test_optional():
    class Model(BaseModel):
        a: Optional[str]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {
                'type': 'str',
                'title': 'A',
                'required': False,
            },
        },
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
                'required': True,
                'type': 'set',
                'item_type': 'int'
            }
        }
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
                'required': True,
                'type': 'tuple',
                'item_types': [
                    'str',
                    'int',
                    {
                        'type': 'any_of',
                        'types': [
                            'str',
                            'int',
                            'float',
                        ],
                    },
                    'float',
                ],
            },
        },
    }


def test_list_union_dict():
    class Foo(BaseModel):
        a: float

    class Model(BaseModel):
        """party time"""
        a: Union[int, str]
        b: List[int]
        c: Dict[int, Foo]
        d: Union[None, Foo]

    assert Model.schema() == {
        'title': 'Model',
        'description': 'party time',
        'type': 'object',
        'properties': {
            'a': {
                'title': 'A',
                'required': True,
                'type': 'any_of',
                'types': [
                    'int',
                    'str',
                ],
            },
            'b': {
                'title': 'B',
                'required': True,
                'type': 'list',
                'item_type': 'int',
            },
            'c': {
                'title': 'C',
                'required': True,
                'type': 'mapping',
                'item_type': {
                    'type': 'object',
                    'properties': {
                        'a': {
                            'title': 'A',
                            'required': True,
                            'type': 'float',
                        },
                    },
                },
                'key_type': 'int',
            },
            'd': {
                'title': 'D',
                'required': False,
                'type': 'object',
                'properties': {
                    'a': {
                        'title': 'A',
                        'required': True,
                        'type': 'float',
                    },
                },
            },
        },
    }
