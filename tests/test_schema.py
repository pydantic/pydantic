import os
import sys
import tempfile
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import Any, Callable, Dict, List, NewType, Optional, Set, Tuple, Union
from uuid import UUID

import pytest

from pydantic import BaseModel, Extra, Field, ValidationError, conlist, validator
from pydantic.color import Color
from pydantic.dataclasses import dataclass
from pydantic.networks import AnyUrl, EmailStr, IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork, NameEmail, stricturl
from pydantic.schema import (
    get_flat_models_from_model,
    get_flat_models_from_models,
    get_model_name_map,
    model_schema,
    schema,
)
from pydantic.types import (
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
    FilePath,
    Json,
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
    StrictBool,
    StrictStr,
    conbytes,
    condecimal,
    confloat,
    conint,
    constr,
)
from pydantic.typing import Literal

try:
    import email_validator
except ImportError:
    email_validator = None

try:
    import typing_extensions
except ImportError:
    typing_extensions = None


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
    assert True not in ApplePie.__schema_cache__
    assert False not in ApplePie.__schema_cache__
    assert ApplePie.schema() == s
    assert True in ApplePie.__schema_cache__
    assert False not in ApplePie.__schema_cache__
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

    assert Model.schema() == {'title': 'Model', 'type': 'object', 'properties': {'a': {'title': 'A'}}}


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
        a: str = Field('some string', const=True)

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'string', 'const': 'some string'}},
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
        'properties': {'a': {'title': 'A', 'type': 'array'}},
        'required': ['a'],
    }
    base_schema['properties']['a']['items'] = expected_schema

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

    base_schema = {'title': 'Model', 'type': 'object', 'properties': {'a': {}}, 'required': ['a']}
    base_schema['properties']['a'] = expected_schema

    assert model_schema == base_schema


@pytest.mark.parametrize(
    'field_type,expected_schema',
    [
        (AnyUrl, {'title': 'A', 'type': 'string', 'format': 'uri', 'minLength': 1, 'maxLength': 2 ** 16}),
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
        ({'regex': '^foo$'}, int),
        ({'gt': 2}, str),
        ({'lt': 5}, bytes),
        ({'ge': 2}, str),
        ({'le': 5}, bool),
        ({'gt': 0}, Callable),
        ({'gt': 0}, Callable[[int], int]),
        ({'gt': 0}, conlist(int, min_items=4)),
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


@pytest.mark.skipif(not typing_extensions, reason='typing_extensions not installed')
def test_literal_schema():
    class Model(BaseModel):
        a: Literal[1]
        b: Literal['a']
        c: Literal['a', 1]

    assert Model.schema() == {
        'properties': {
            'a': {'title': 'A', 'type': 'integer', 'const': 1},
            'b': {'title': 'B', 'type': 'string', 'const': 'a'},
            'c': {'anyOf': [{'type': 'string', 'const': 'a'}, {'type': 'integer', 'const': 1}], 'title': 'C'},
        },
        'required': ['a', 'b', 'c'],
        'title': 'Model',
        'type': 'object',
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
            def schema_extra(schema):
                schema.pop('properties')
                schema['type'] = 'override'

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


def test_conlist():
    class Model(BaseModel):
        foo: List[int] = Field(..., min_items=2, max_items=4)

    assert Model(foo=[1, 2]).dict() == {'foo': [1, 2]}

    with pytest.raises(ValidationError, match='ensure this value has at least 2 items'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='ensure this value has at most 4 items'):
        Model(foo=list(range(5)))

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'foo': {'title': 'Foo', 'type': 'array', 'items': {'type': 'integer'}, 'minItems': 2, 'maxItems': 4}
        },
        'required': ['foo'],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    assert exc_info.value.errors() == [
        {'loc': ('foo', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('foo', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


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
        'properties': {'example': {'title': 'Example', 'enum': ['GT', 'LT', 'GE', 'LE', 'ML', 'MO', 'RE']}},
        'required': ['example'],
    }


def test_path_modify_schema():
    class MyPath(Path):
        @classmethod
        def __modify_schema__(cls, schema):
            schema.update(schema, foobar=123)

    class Model(BaseModel):
        path1: Path
        path2: MyPath

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'path1': {'title': 'Path1', 'type': 'string', 'format': 'path'},
            'path2': {'title': 'Path2', 'type': 'string', 'format': 'path', 'foobar': 123},
        },
        'required': ['path1', 'path2'],
    }
