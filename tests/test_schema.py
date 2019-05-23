import os
import sys
import tempfile
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

import pytest

from pydantic import BaseModel, Schema, ValidationError, validator
from pydantic.schema import get_flat_models_from_model, get_flat_models_from_models, get_model_name_map, schema
from pydantic.types import (
    DSN,
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    ConstrainedBytes,
    ConstrainedDecimal,
    ConstrainedFloat,
    ConstrainedInt,
    ConstrainedStr,
    DirectoryPath,
    EmailStr,
    FilePath,
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
    IPvAnyAddress,
    IPvAnyInterface,
    IPvAnyNetwork,
    Json,
    NameEmail,
    NegativeFloat,
    NegativeInt,
    NoneBytes,
    NoneStr,
    NoneStrBytes,
    PositiveFloat,
    PositiveInt,
    PyObject,
    SecretBytes,
    SecretStr,
    StrBytes,
    StrictStr,
    UrlStr,
    conbytes,
    condecimal,
    confloat,
    conint,
    constr,
    urlstr,
)

try:
    import email_validator
except ImportError:
    email_validator = None


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
            'bar': {'type': 'string', 'title': 'Bar', 'description': 'this description of bar'},
        },
        'required': ['bar'],
    }


def test_schema_repr():
    s = Schema(4, title='Foo is Great')
    assert repr(s) == "Schema(default: 4, title: 'Foo is Great', extra: {})"
    assert str(s) == "Schema(default: 4, title: 'Foo is Great', extra: {})"


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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A'}},
        'required': ['a'],
    }


def test_set():
    class Model(BaseModel):
        a: Set[int]
        b: set

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'a': {'title': 'A', 'type': 'array', 'uniqueItems': True, 'items': {'type': 'integer'}},
            'b': {'title': 'B', 'type': 'array', 'items': {}, 'uniqueItems': True},
        },
        'required': ['a', 'b'],
    }


def test_const_str():
    class Model(BaseModel):
        a: str = Schema('some string', const=True)

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'const': 'some string'}},
    }


def test_const_false():
    class Model(BaseModel):
        a: str = Schema('some string', const=False)

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'default': 'some string'}},
    }


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (tuple, {}),
        (
            Tuple[str, int, Union[str, int, float], float],
            [
                {'type': 'string'},
                {'type': 'integer'},
                {'anyOf': [{'type': 'string'}, {'type': 'integer'}, {'type': 'number'}]},
                {'type': 'number'},
            ],
        ),
        (Tuple[str], {'type': 'string'}),
    ],
)
def test_tuple(field_type, expected_schema):
    class Model(BaseModel):
        a: field_type

    base_schema = {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'array', 'items': None}},
        'required': ['a'],
    }
    # noinspection PyTypeChecker
    base_schema['properties']['a']['items'] = expected_schema
    if expected_schema is None:
        base_schema['properties']['a'].pop('items', None)

    assert Model.schema() == base_schema


def test_bool():
    class Model(BaseModel):
        a: bool

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

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': {}}, 'required': ['a']}
    base_schema['properties']['a'] = expected_schema

    assert Model.schema() == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (UrlStr, {'title': 'A', 'type': 'string', 'format': 'uri', 'minLength': 1, 'maxLength': 2 ** 16}),
        (
            urlstr(min_length=5, max_length=10),
            {'title': 'A', 'type': 'string', 'format': 'uri', 'minLength': 5, 'maxLength': 10},
        ),
        (DSN, {'title': 'A', 'type': 'string', 'format': 'dsn'}),
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
        'properties': {'a': {'title': 'A', 'type': inner_type, 'writeOnly': True}},
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

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'format': 'json-string'}},
        'required': ['a'],
    }


def test_ipv4address_type():
    class Model(BaseModel):
        ip_address: IPv4Address

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip_Address', 'type': 'string', 'format': 'ipv4'}},
        'required': ['ip_address'],
    }


def test_ipv6address_type():
    class Model(BaseModel):
        ip_address: IPv6Address

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip_Address', 'type': 'string', 'format': 'ipv6'}},
        'required': ['ip_address'],
    }


def test_ipvanyaddress_type():
    class Model(BaseModel):
        ip_address: IPvAnyAddress

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_address': {'title': 'Ip_Address', 'type': 'string', 'format': 'ipvanyaddress'}},
        'required': ['ip_address'],
    }


def test_ipv4interface_type():
    class Model(BaseModel):
        ip_interface: IPv4Interface

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip_Interface', 'type': 'string', 'format': 'ipv4interface'}},
        'required': ['ip_interface'],
    }


def test_ipv6interface_type():
    class Model(BaseModel):
        ip_interface: IPv6Interface

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip_Interface', 'type': 'string', 'format': 'ipv6interface'}},
        'required': ['ip_interface'],
    }


def test_ipvanyinterface_type():
    class Model(BaseModel):
        ip_interface: IPvAnyInterface

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_interface': {'title': 'Ip_Interface', 'type': 'string', 'format': 'ipvanyinterface'}},
        'required': ['ip_interface'],
    }


def test_ipv4network_type():
    class Model(BaseModel):
        ip_network: IPv4Network

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_network': {'title': 'Ip_Network', 'type': 'string', 'format': 'ipv4network'}},
        'required': ['ip_network'],
    }


def test_ipv6network_type():
    class Model(BaseModel):
        ip_network: IPv6Network

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_network': {'title': 'Ip_Network', 'type': 'string', 'format': 'ipv6network'}},
        'required': ['ip_network'],
    }


def test_ipvanynetwork_type():
    class Model(BaseModel):
        ip_network: IPvAnyNetwork

    model_schema = Model.schema()
    assert model_schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {'ip_network': {'title': 'Ip_Network', 'type': 'string', 'format': 'ipvanynetwork'}},
        'required': ['ip_network'],
    }


@pytest.mark.parametrize('annotation', [Callable, Callable[[int], int]])
def test_callable_type(annotation):
    class Model(BaseModel):
        callback: annotation
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

    class Ingredient(BaseModel):
        name: str

    class Pizza(BaseModel):
        name: str
        ingredients: List[Ingredient]

    flat_models = get_flat_models_from_models([Bar, Pizza])
    assert flat_models == set([Foo, Bar, Ingredient, Pizza])


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
            'Baz': {'title': 'Baz', 'type': 'object', 'properties': {'c': {'$ref': '#/definitions/Bar'}}},
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


def test_schema_with_ref_prefix():
    class Foo(BaseModel):
        a: str

    class Bar(BaseModel):
        b: Foo

    class Baz(BaseModel):
        c: Bar

    model_schema = schema([Bar, Baz], ref_prefix='#/components/schemas/')  # OpenAPI style
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


@pytest.mark.parametrize(
    'kwargs,type_,expected_extra',
    [
        ({'max_length': 5}, str, {'type': 'string', 'maxLength': 5}),
        ({'max_length': 5}, constr(max_length=6), {'type': 'string', 'maxLength': 6}),
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
        a: type_ = Schema('foo', title='A title', description='A description', **kwargs)

    expected_schema = {
        'title': 'Foo',
        'type': 'object',
        'properties': {'a': {'title': 'A title', 'description': 'A description', 'default': 'foo'}},
    }

    expected_schema['properties']['a'].update(expected_extra)
    assert Foo.schema() == expected_schema


@pytest.mark.parametrize(
    'kwargs,type_,expected',
    [
        ({'max_length': 5}, int, {'type': 'integer'}),
        ({'min_length': 2}, float, {'type': 'number'}),
        ({'max_length': 5}, Decimal, {'type': 'number'}),
        ({'regex': '^foo$'}, int, {'type': 'integer'}),
        ({'gt': 2}, str, {'type': 'string'}),
        ({'lt': 5}, bytes, {'type': 'string', 'format': 'binary'}),
        ({'ge': 2}, str, {'type': 'string'}),
        ({'le': 5}, bool, {'type': 'boolean'}),
    ],
)
def test_not_constraints_schema(kwargs, type_, expected):
    class Foo(BaseModel):
        a: type_ = Schema('foo', title='A title', description='A description', **kwargs)

    base_schema = {
        'title': 'Foo',
        'type': 'object',
        'properties': {'a': {'title': 'A title', 'description': 'A description', 'default': 'foo'}},
    }

    base_schema['properties']['a'].update(expected)
    assert Foo.schema() == base_schema


@pytest.mark.parametrize(
    'kwargs,type_,value',
    [
        ({'max_length': 5}, str, 'foo'),
        ({'max_length': 5}, constr(max_length=6), 'foo'),
        ({'min_length': 2}, str, 'foo'),
        ({'max_length': 5}, bytes, b'foo'),
        ({'regex': '^foo$'}, str, 'foo'),
        ({'max_length': 5}, bool, True),
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
        a: type_ = Schema('foo', title='A title', description='A description', **kwargs)

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
        a: type_ = Schema('foo', title='A title', description='A description', **kwargs)

    with pytest.raises(ValidationError):
        Foo(a=value)


def test_schema_kwargs():
    class Foo(BaseModel):
        a: str = Schema('foo', examples=['bar'])

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
            'a': {'type': 'object', 'title': 'A', 'default': {}, 'patternProperties': {regex_str: {'type': 'string'}}}
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
