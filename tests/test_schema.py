from enum import Enum, IntEnum

from pydantic import BaseModel


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


def test_choices():
    FooEnum = Enum('FooEnum', {'foo': 'f', 'bar': 'b'})
    BarEnum = IntEnum('BarEnum', {'foo': 1, 'bar': 2})

    class Model(BaseModel):
        foo: FooEnum
        bar: BarEnum

    assert Model.schema() == {
        'type': 'object',
        'title': 'Model',
        'properties': {
            'foo': {
                'type': 'enum',
                'title': 'Foo',
                'required': True,
                'choices': [
                    ('f', 'foo'),
                    ('b', 'bar'),
                ],
            },
            'bar': {
                'type': 'int',
                'title': 'Bar',
                'required': True,
                'choices': [
                    (1, 'foo'),
                    (2, 'bar'),
                ],
            },
        },
    }
