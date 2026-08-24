import ipaddress
import json
import math
import os
import re
import sys
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import (
    Annotated,
    Any,
    Literal,
    NewType,
    TypeVar,
    Union,
)

import annotated_types
import pytest
from pydantic_core import (
    CoreSchema,
    PydanticCustomError,
    PydanticOmit,
    SchemaError,
    core_schema,
)
from typing_extensions import NotRequired, TypedDict, get_args  # noqa: UP035 (for `get_args`)

from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    AfterValidator,
    AwareDatetime,
    Base64Bytes,
    Base64Str,
    Base64UrlBytes,
    Base64UrlStr,
    BaseModel,
    BeforeValidator,
    ByteSize,
    ConfigDict,
    DirectoryPath,
    EmailStr,
    FailFast,
    Field,
    FilePath,
    FiniteFloat,
    FutureDate,
    FutureDatetime,
    GetCoreSchemaHandler,
    GetPydanticSchema,
    ImportString,
    InstanceOf,
    Json,
    JsonValue,
    NaiveDatetime,
    NameEmail,
    NegativeFloat,
    NegativeInt,
    NewPath,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    OnErrorOmit,
    PastDate,
    PastDatetime,
    PlainSerializer,
    PlainValidator,
    PositiveFloat,
    PositiveInt,
    PydanticInvalidForJsonSchema,
    Secret,
    SecretBytes,
    SecretStr,
    SerializeAsAny,
    SkipValidation,
    Strict,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    StringConstraints,
    TypeAdapter,
    ValidateAs,
    ValidationError,
    conbytes,
    condate,
    condecimal,
    confloat,
    confrozenset,
    conint,
    conlist,
    conset,
    constr,
    field_serializer,
    field_validator,
    validate_call,
)

try:
    import email_validator
except ImportError:
    email_validator = None


# TODO add back tests for Iterator


def test_strict_raw_type():
    class Model(BaseModel):
        v: Annotated[str, Strict]

    assert Model(v='foo').v == 'foo'
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[type=string_type,'):
        Model(v=b'fo')


@pytest.mark.parametrize(
    'annotation',
    [
        pytest.param(ImportString[Callable[[Any], Any]], id='ImportString[...]'),
        pytest.param(Annotated[Callable[[Any], Any], ImportString], id='Annotated[..., ImportString]'),
    ],
)
def test_string_import_callable(annotation):
    class PyObjectModel(BaseModel):
        callable: annotation

    m = PyObjectModel(callable='math.cos')
    assert m.callable == math.cos

    m = PyObjectModel(callable=math.cos)
    assert m.callable == math.cos

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable='foobar')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'import_error',
            'loc': ('callable',),
            'msg': "Invalid python path: No module named 'foobar'",
            'input': 'foobar',
            'ctx': {'error': "No module named 'foobar'"},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable='os.missing')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'import_error',
            'loc': ('callable',),
            'msg': "Invalid python path: No module named 'os.missing'; 'os' is not a package",
            'input': 'os.missing',
            'ctx': {'error': "No module named 'os.missing'; 'os' is not a package"},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable='os.path')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'callable_type', 'loc': ('callable',), 'msg': 'Input should be callable', 'input': os.path}
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable=[1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'callable_type', 'loc': ('callable',), 'msg': 'Input should be callable', 'input': [1, 2, 3]}
    ]


@pytest.mark.parametrize(
    ('value', 'expected', 'mode'),
    [
        ('math:cos', 'math.cos', 'json'),
        ('math:cos', math.cos, 'python'),
        ('math.cos', 'math.cos', 'json'),
        ('math.cos', math.cos, 'python'),
        pytest.param(
            'os.path', 'posixpath', 'json', marks=pytest.mark.skipif(sys.platform == 'win32', reason='different output')
        ),
        pytest.param(
            'os.path', 'ntpath', 'json', marks=pytest.mark.skipif(sys.platform != 'win32', reason='different output')
        ),
        ('os.path', os.path, 'python'),
        ([1, 2, 3], [1, 2, 3], 'json'),
        ([1, 2, 3], [1, 2, 3], 'python'),
        ('math', 'math', 'json'),
        ('math', math, 'python'),
        ('builtins.list', 'builtins.list', 'json'),
        ('builtins.list', list, 'python'),
        (list, 'builtins.list', 'json'),
        (list, list, 'python'),
        (f'{__name__}.pytest', 'pytest', 'json'),
        (f'{__name__}.pytest', pytest, 'python'),
    ],
)
def test_string_import_any(value: Any, expected: Any, mode: Literal['json', 'python']):
    class PyObjectModel(BaseModel):
        thing: ImportString

    assert PyObjectModel(thing=value).model_dump(mode=mode) == {'thing': expected}


@pytest.mark.parametrize(
    ('value', 'validate_default', 'expected'),
    [
        (math.cos, True, math.cos),
        ('math:cos', True, math.cos),
        (math.cos, False, math.cos),
        ('math:cos', False, 'math:cos'),
    ],
)
def test_string_import_default_value(value: Any, validate_default: bool, expected: Any):
    class PyObjectModel(BaseModel):
        thing: ImportString = Field(default=value, validate_default=validate_default)

    assert PyObjectModel().thing == expected


@pytest.mark.parametrize('value', ['oss', 'os.os', f'{__name__}.x'])
def test_string_import_any_expected_failure(value: Any):
    """Ensure importString correctly fails to instantiate when it's supposed to"""

    class PyObjectModel(BaseModel):
        thing: ImportString

    with pytest.raises(ValidationError, match='type=import_error'):
        PyObjectModel(thing=value)


@pytest.mark.parametrize(
    'annotation',
    [
        pytest.param(
            ImportString[Annotated[float, annotated_types.Ge(3), annotated_types.Le(4)]], id='ImportString[...]'
        ),
        pytest.param(
            Annotated[float, annotated_types.Ge(3), annotated_types.Le(4), ImportString],
            id='Annotated[..., ImportString]',
        ),
    ],
)
def test_string_import_constraints(annotation):
    class PyObjectModel(BaseModel):
        thing: annotation

    assert PyObjectModel(thing='math:pi').model_dump() == {'thing': pytest.approx(3.141592654)}
    with pytest.raises(ValidationError, match='type=greater_than_equal'):
        PyObjectModel(thing='math:e')


def test_string_import_examples():
    import collections

    adapter = TypeAdapter(ImportString)
    assert adapter.validate_python('collections') is collections
    assert adapter.validate_python('collections.abc') is collections.abc
    assert adapter.validate_python('collections.abc.Mapping') is collections.abc.Mapping
    assert adapter.validate_python('collections.abc:Mapping') is collections.abc.Mapping


@pytest.mark.parametrize(
    'import_string,errors',
    [
        (
            'collections.abc.def',
            [
                {
                    'ctx': {'error': "No module named 'collections.abc.def'; 'collections.abc' is not a package"},
                    'input': 'collections.abc.def',
                    'loc': (),
                    'msg': "Invalid python path: No module named 'collections.abc.def'; 'collections.abc' is not a package",
                    'type': 'import_error',
                }
            ],
        ),
        (
            'collections.abc:def',
            [
                {
                    'ctx': {'error': "cannot import name 'def' from 'collections.abc'"},
                    'input': 'collections.abc:def',
                    'loc': (),
                    'msg': "Invalid python path: cannot import name 'def' from 'collections.abc'",
                    'type': 'import_error',
                }
            ],
        ),
        (
            'collections:abc:Mapping',
            [
                {
                    'ctx': {'error': "Import strings should have at most one ':'; received 'collections:abc:Mapping'"},
                    'input': 'collections:abc:Mapping',
                    'loc': (),
                    'msg': "Invalid python path: Import strings should have at most one ':';"
                    " received 'collections:abc:Mapping'",
                    'type': 'import_error',
                }
            ],
        ),
        (
            '123_collections:Mapping',
            [
                {
                    'ctx': {'error': "No module named '123_collections'"},
                    'input': '123_collections:Mapping',
                    'loc': (),
                    'msg': "Invalid python path: No module named '123_collections'",
                    'type': 'import_error',
                }
            ],
        ),
        (
            ':Mapping',
            [
                {
                    'ctx': {'error': "Import strings should have a nonempty module name; received ':Mapping'"},
                    'input': ':Mapping',
                    'loc': (),
                    'msg': 'Invalid python path: Import strings should have a nonempty module '
                    "name; received ':Mapping'",
                    'type': 'import_error',
                }
            ],
        ),
    ],
)
def test_string_import_errors(import_string, errors):
    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(ImportString).validate_python(import_string)
    assert exc_info.value.errors() == errors


@pytest.mark.xfail(
    reason='This fails with pytest bc of the weirdness associated with importing modules in a test, but works in normal usage'
)
def test_import_string_sys_stdout() -> None:
    class ImportThings(BaseModel):
        obj: ImportString

    import_things = ImportThings(obj='sys.stdout')
    assert import_things.model_dump_json() == '{"obj":"sys.stdout"}'


def test_import_string_thing_with_name() -> None:
    """https://github.com/pydantic/pydantic/issues/12218"""

    class ImportThings(BaseModel):
        obj: ImportString

    @dataclass
    class ThingWithName:
        name: str

    import_things = ImportThings(obj=ThingWithName('foo'))
    assert import_things.model_dump_json() == '{"obj":{"name":"foo"}}'


@pytest.mark.parametrize(
    'kwargs,type_,a',
    [
        ({'pattern': '^foo$'}, int, 1),
        *[
            ({constraint_name: 0}, list[int], [1, 2, 3, 4, 5])
            for constraint_name in ['gt', 'lt', 'ge', 'le', 'multiple_of']
        ]
        + [
            ({constraint_name: 0}, set[int], {1, 2, 3, 4, 5})
            for constraint_name in ['gt', 'lt', 'ge', 'le', 'multiple_of']
        ]
        + [
            ({constraint_name: 0}, frozenset[int], frozenset({1, 2, 3, 4, 5}))
            for constraint_name in ['gt', 'lt', 'ge', 'le', 'multiple_of']
        ]
        + [({constraint_name: 0}, Decimal, Decimal('1.0')) for constraint_name in ['max_length', 'min_length']]
        + [({constraint_name: 0}, float, 1.0) for constraint_name in ['max_digits', 'decimal_places']],
    ],
)
def test_invalid_schema_constraints(kwargs, type_, a):
    class Foo(BaseModel):
        a: type_ = Field('foo', title='A title', description='A description', **kwargs)

    constraint_name = list(kwargs.keys())[0]
    with pytest.raises(
        TypeError, match=re.escape(f"Unable to apply constraint '{constraint_name}' to supplied value {a}")
    ):
        Foo(a=a)


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_string_success():
    class MoreStringsModel(BaseModel):
        str_strip_enabled: constr(strip_whitespace=True)
        str_strip_disabled: constr(strip_whitespace=False)
        str_regex: constr(pattern=r'^xxx\d{3}$') = ...
        str_min_length: constr(min_length=5) = ...
        str_email: EmailStr = ...
        name_email: NameEmail = ...
        str_gt: Annotated[str, annotated_types.Gt('a')]

    m = MoreStringsModel(
        str_strip_enabled='   xxx123   ',
        str_strip_disabled='   xxx123   ',
        str_regex='xxx123',
        str_min_length='12345',
        str_email='foobar@example.com  ',
        name_email='foo bar  <foobaR@example.com>',
        str_gt='b',
    )
    assert m.str_strip_enabled == 'xxx123'
    assert m.str_strip_disabled == '   xxx123   '
    assert m.str_regex == 'xxx123'
    assert m.str_email == 'foobar@example.com'
    assert repr(m.name_email) == "NameEmail(name='foo bar', email='foobaR@example.com')"
    assert str(m.name_email) == 'foo bar <foobaR@example.com>'
    assert m.name_email.name == 'foo bar'
    assert m.name_email.email == 'foobaR@example.com'
    assert m.str_gt == 'b'


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_string_fails():
    class MoreStringsModel(BaseModel):
        str_regex: constr(pattern=r'^xxx\d{3}$') = ...
        str_min_length: constr(min_length=5) = ...
        str_email: EmailStr = ...
        name_email: NameEmail = ...

    with pytest.raises(ValidationError) as exc_info:
        MoreStringsModel(
            str_regex='xxx123xxx',
            str_min_length='1234',
            str_email='foobar<@example.com',
            name_email='foobar @example.com',
        )
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_pattern_mismatch',
            'loc': ('str_regex',),
            'msg': "String should match pattern '^xxx\\d{3}$'",
            'input': 'xxx123xxx',
            'ctx': {'pattern': '^xxx\\d{3}$'},
        },
        {
            'type': 'string_too_short',
            'loc': ('str_min_length',),
            'msg': 'String should have at least 5 characters',
            'input': '1234',
            'ctx': {'min_length': 5},
        },
        {
            'type': 'value_error',
            'loc': ('str_email',),
            'msg': 'value is not a valid email address: An open angle bracket at the start of the email address has to be followed by a close angle bracket at the end.',
            'input': 'foobar<@example.com',
            'ctx': {
                'reason': 'An open angle bracket at the start of the email address has to be followed by a close angle bracket at the end.'
            },
        },
        {
            'type': 'value_error',
            'loc': ('name_email',),
            'msg': 'value is not a valid email address: The email address contains invalid characters before the @-sign: SPACE.',
            'input': 'foobar @example.com',
            'ctx': {'reason': 'The email address contains invalid characters before the @-sign: SPACE.'},
        },
    ]


@pytest.mark.skipif(email_validator, reason='email_validator is installed')
def test_email_validator_not_installed_email_str():
    with pytest.raises(ImportError):

        class Model(BaseModel):
            str_email: EmailStr = ...


@pytest.mark.skipif(email_validator, reason='email_validator is installed')
def test_email_validator_not_installed_name_email():
    with pytest.raises(ImportError):

        class Model(BaseModel):
            str_email: NameEmail = ...


def test_new_type_success():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', list[int])

    class Model(BaseModel):
        a: a_type
        b: b_type
        c: c_type

    m = Model(a=42, b=24, c=[1, 2, 3])
    assert m.model_dump() == {'a': 42, 'b': 24, 'c': [1, 2, 3]}


def test_new_type_fails():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', list[int])

    class Model(BaseModel):
        a: a_type
        b: b_type
        c: c_type

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foo', b='bar', c=['foo'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'foo',
        },
        {
            'type': 'int_parsing',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'bar',
        },
        {
            'type': 'int_parsing',
            'loc': ('c', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'foo',
        },
    ]


def test_valid_simple_json():
    class JsonModel(BaseModel):
        json_obj: Json

    obj = '{"a": 1, "b": [2, 3]}'
    assert JsonModel(json_obj=obj).model_dump() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_valid_simple_json_any():
    class JsonModel(BaseModel):
        json_obj: Json[Any]

    obj = '{"a": 1, "b": [2, 3]}'
    assert JsonModel(json_obj=obj).model_dump() == {'json_obj': {'a': 1, 'b': [2, 3]}}


@pytest.mark.parametrize('type_expr', [Json, Json[Any]])
def test_invalid_simple_json(type_expr):
    class JsonModel(BaseModel):
        json_obj: type_expr

    obj = '{a: 1, b: [2, 3]}'
    with pytest.raises(ValidationError) as exc_info:
        JsonModel(json_obj=obj)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'json_invalid',
            'loc': ('json_obj',),
            'msg': 'Invalid JSON: key must be a string at line 1 column 2',
            'input': '{a: 1, b: [2, 3]}',
            'ctx': {'error': 'key must be a string at line 1 column 2'},
        }
    ]


def test_valid_simple_json_bytes():
    class JsonModel(BaseModel):
        json_obj: Json

    obj = b'{"a": 1, "b": [2, 3]}'
    assert JsonModel(json_obj=obj).model_dump() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_valid_detailed_json():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[list[int]]

    obj = '[1, 2, 3]'
    assert JsonDetailedModel(json_obj=obj).model_dump() == {'json_obj': [1, 2, 3]}

    obj = b'[1, 2, 3]'
    assert JsonDetailedModel(json_obj=obj).model_dump() == {'json_obj': [1, 2, 3]}

    obj = '(1, 2, 3)'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'json_invalid',
            'loc': ('json_obj',),
            'msg': 'Invalid JSON: expected value at line 1 column 1',
            'input': '(1, 2, 3)',
            'ctx': {'error': 'expected value at line 1 column 1'},
        }
    ]


def test_valid_model_json():
    class Model(BaseModel):
        a: int
        b: list[int]

    class JsonDetailedModel(BaseModel):
        json_obj: Json[Model]

    obj = '{"a": 1, "b": [2, 3]}'
    m = JsonDetailedModel(json_obj=obj)
    assert isinstance(m.json_obj, Model)
    assert m.json_obj.a == 1
    assert m.model_dump() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_invalid_model_json():
    class Model(BaseModel):
        a: int
        b: list[int]

    class JsonDetailedModel(BaseModel):
        json_obj: Json[Model]

    obj = '{"a": 1, "c": [2, 3]}'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('json_obj', 'b'), 'msg': 'Field required', 'input': {'a': 1, 'c': [2, 3]}}
    ]


def test_invalid_detailed_json_type_error():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[list[int]]

    obj = '["a", "b", "c"]'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('json_obj', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': ('json_obj', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
        {
            'type': 'int_parsing',
            'loc': ('json_obj', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'c',
        },
    ]


def test_json_not_str():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[list[int]]

    obj = 12
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'json_type',
            'loc': ('json_obj',),
            'msg': 'JSON input should be string, bytes or bytearray',
            'input': 12,
        }
    ]


def test_json_before_validator():
    call_count = 0

    class JsonModel(BaseModel):
        json_obj: Json[str]

        @field_validator('json_obj', mode='before')
        @classmethod
        def check(cls, v):
            assert v == '"foobar"'
            nonlocal call_count
            call_count += 1
            return v

    assert JsonModel(json_obj='"foobar"').model_dump() == {'json_obj': 'foobar'}
    assert call_count == 1


def test_json_optional_simple():
    class JsonOptionalModel(BaseModel):
        json_obj: Json | None

    assert JsonOptionalModel(json_obj=None).model_dump() == {'json_obj': None}
    assert JsonOptionalModel(json_obj='["x", "y", "z"]').model_dump() == {'json_obj': ['x', 'y', 'z']}


def test_json_optional_complex():
    class JsonOptionalModel(BaseModel):
        json_obj: Json[list[int]] | None

    JsonOptionalModel(json_obj=None)

    good = JsonOptionalModel(json_obj='[1, 2, 3]')
    assert good.json_obj == [1, 2, 3]

    with pytest.raises(ValidationError) as exc_info:
        JsonOptionalModel(json_obj='["i should fail"]')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('json_obj', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'i should fail',
        }
    ]


def test_json_required():
    class JsonRequired(BaseModel):
        json_obj: Json

    assert JsonRequired(json_obj='["x", "y", "z"]').model_dump() == {'json_obj': ['x', 'y', 'z']}
    with pytest.raises(ValidationError, match=r'JSON input should be string, bytes or bytearray \[type=json_type,'):
        JsonRequired(json_obj=None)
    with pytest.raises(ValidationError, match=r'Field required \[type=missing,'):
        JsonRequired()


@pytest.mark.parametrize('validate_json', [True, False])
def test_secretstr(validate_json):
    class Foobar(BaseModel):
        password: SecretStr
        empty_password: SecretStr

    if validate_json:
        f = Foobar.model_validate_json('{"password": "1234", "empty_password": ""}')
        with pytest.raises(ValidationError) as exc_info:
            Foobar.model_validate_json('{"password": 1234, "empty_password": null}')
    else:
        f = Foobar(password='1234', empty_password='')
        with pytest.raises(ValidationError) as exc_info:
            Foobar(password=1234, empty_password=None)

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': ('password',), 'msg': 'Input should be a valid string', 'input': 1234},
        {'type': 'string_type', 'loc': ('empty_password',), 'msg': 'Input should be a valid string', 'input': None},
    ]

    # Assert correct types.
    assert f.password.__class__.__name__ == 'SecretStr'
    assert f.empty_password.__class__.__name__ == 'SecretStr'

    # Assert str and repr are correct.
    assert str(f.password) == '**********'
    assert str(f.empty_password) == ''
    assert repr(f.password) == "SecretStr('**********')"
    assert repr(f.empty_password) == "SecretStr('')"
    assert len(f.password) == 4
    assert len(f.empty_password) == 0

    # Assert retrieval of secret value is correct
    assert f.password.get_secret_value() == '1234'
    assert f.empty_password.get_secret_value() == ''


def test_secretstr_subclass():
    class DecryptableStr(SecretStr):
        """
        Simulate a SecretStr with decryption capabilities.
        """

        def decrypt_value(self) -> str:
            return f'MOCK DECRYPTED {self.get_secret_value()}'

    class Foobar(BaseModel):
        password: DecryptableStr
        empty_password: SecretStr

    # Initialize the model.
    f = Foobar(password='1234', empty_password='')

    # Assert correct types.
    assert f.password.__class__.__name__ == 'DecryptableStr'
    assert f.empty_password.__class__.__name__ == 'SecretStr'

    # Assert str and repr are correct.
    assert str(f.password) == '**********'
    assert str(f.empty_password) == ''
    assert repr(f.password) == "DecryptableStr('**********')"
    assert repr(f.empty_password) == "SecretStr('')"
    assert len(f.password) == 4
    assert len(f.empty_password) == 0

    # Assert retrieval of secret value is correct
    assert f.password.get_secret_value() == '1234'
    assert f.empty_password.get_secret_value() == ''


def test_secretstr_equality():
    assert SecretStr('abc') == SecretStr('abc')
    assert SecretStr('123') != SecretStr('321')
    assert SecretStr('123') != '123'
    assert SecretStr('123') is not SecretStr('123')
    assert SecretStr('café') == SecretStr('café')
    assert SecretStr('café') != SecretStr('cafe')
    assert SecretStr('\ud800') == SecretStr('\ud800')  # lone surrogate, unencodable with strict utf-8


def test_secretstr_idempotent():
    class Foobar(BaseModel):
        password: SecretStr

    # Should not raise an exception
    m = Foobar(password=SecretStr('1234'))
    assert m.password.get_secret_value() == '1234'


class SecretDate(Secret[date]):
    def _display(self) -> str:
        return '****/**/**'


class SampleEnum(str, Enum):
    foo = 'foo'
    bar = 'bar'


SecretEnum = Secret[SampleEnum]


@pytest.mark.parametrize(
    'value, result',
    [
        # Valid inputs
        (1_493_942_400, date(2017, 5, 5)),
        (1_493_942_400_000, date(2017, 5, 5)),
        (0, date(1970, 1, 1)),
        ('2012-04-23', date(2012, 4, 23)),
        (b'2012-04-23', date(2012, 4, 23)),
        (date(2012, 4, 9), date(2012, 4, 9)),
        (datetime(2012, 4, 9, 0, 0), date(2012, 4, 9)),
        (1_549_238_400, date(2019, 2, 4)),  # nowish in s
        (1_549_238_400_000, date(2019, 2, 4)),  # nowish in ms
        (19_999_958_400, date(2603, 10, 11)),  # just before watershed
    ],
)
def test_secretdate(value, result):
    class Foobar(BaseModel):
        value: SecretDate

    f = Foobar(value=value)

    # Assert correct type.
    assert f.value.__class__.__name__ == 'SecretDate'

    # Assert str and repr are correct.
    assert str(f.value) == '****/**/**'
    assert repr(f.value) == "SecretDate('****/**/**')"

    # Assert retrieval of secret value is correct
    assert f.value.get_secret_value() == result


def test_secretdate_json_serializable():
    class _SecretDate(Secret[date]):
        def _display(self) -> str:
            return '****/**/**'

    SecretDate = Annotated[
        _SecretDate,
        PlainSerializer(lambda v: v.get_secret_value().strftime('%Y-%m-%d'), when_used='json'),
    ]

    class Foobar(BaseModel):
        value: SecretDate

    f = Foobar(value='2017-01-01')

    assert '2017-01-01' in f.model_dump_json()


def test_secretenum_json_serializable():
    class SampleEnum(str, Enum):
        foo = 'foo'
        bar = 'bar'

    SecretEnum = Annotated[
        Secret[SampleEnum],
        PlainSerializer(lambda v: v.get_secret_value(), when_used='json'),
    ]

    class Foobar(BaseModel):
        value: SecretEnum

    f = Foobar(value='foo')

    assert f.model_dump_json() == '{"value":"foo"}'


@pytest.mark.parametrize(
    'SecretField, value, error_msg',
    [
        (SecretDate, 'not-a-date', r'Input should be a valid date'),
        (SecretStr, 0, r'Input should be a valid string \[type=string_type,'),
        (SecretBytes, 0, r'Input should be a valid bytes \[type=bytes_type,'),
        (SecretEnum, 0, r'Input should be an instance of SampleEnum'),
    ],
)
def test_strict_secretfield_by_config(SecretField, value, error_msg):
    class Foobar(BaseModel):
        model_config = ConfigDict(strict=True)
        value: SecretField

    with pytest.raises(ValidationError, match=error_msg):
        Foobar(value=value)


@pytest.mark.parametrize(
    'field, value, error_msg',
    [
        (date, 'not-a-date', r'Input should be a valid date'),
        (str, 0, r'Input should be a valid string \[type=string_type,'),
        (bytes, 0, r'Input should be a valid bytes \[type=bytes_type,'),
        (SampleEnum, 0, r'Input should be an instance of SampleEnum'),
    ],
)
def test_strict_secretfield_annotated(field, value, error_msg):
    SecretField = Annotated[field, Strict()]

    class Foobar(BaseModel):
        value: Secret[SecretField]

    with pytest.raises(ValidationError, match=error_msg):
        Foobar(value=value)


@pytest.mark.parametrize(
    'value',
    [
        datetime(2012, 4, 9, 12, 15),
        'x20120423',
        '2012-04-56',
        20000044800,  # just after watershed
        1_549_238_400_000_000,  # nowish in μs
        1_549_238_400_000_000_000,  # nowish in ns
        'infinity',
        float('inf'),
        int('1' + '0' * 100),
        float('-infinity'),
        float('nan'),
    ],
)
def test_secretdate_parsing(value):
    class FooBar(BaseModel):
        d: SecretDate

    with pytest.raises(ValidationError):
        FooBar(d=value)


def test_secretdate_equality():
    assert SecretDate('2017-01-01') == SecretDate('2017-01-01')
    assert SecretDate('2017-01-01') != SecretDate('2018-01-01')
    assert SecretDate(date(2017, 1, 1)) != date(2017, 1, 1)
    assert SecretDate('2017-01-01') is not SecretDate('2017-01-01')


def test_secretdate_idempotent():
    class Foobar(BaseModel):
        value: SecretDate

    # Should not raise an exception
    m = Foobar(value=SecretDate(date(2017, 1, 1)))
    assert m.value.get_secret_value() == date(2017, 1, 1)


def test_secret_union_serializable() -> None:
    class Base(BaseModel):
        x: Secret[int] | Secret[str]

    model = Base(x=1)
    assert model.model_dump() == {'x': Secret[int](1)}
    assert model.model_dump_json() == '{"x":"**********"}'


@pytest.mark.parametrize(
    'pydantic_type',
    [
        pytest.param(Strict, id='Strict'),
        pytest.param(StrictBool, id='StrictBool'),
        pytest.param(conint, id='conint'),
        pytest.param(PositiveInt, id='PositiveInt'),
        pytest.param(NegativeInt, id='NegativeInt'),
        pytest.param(NonPositiveInt, id='NonPositiveInt'),
        pytest.param(NonNegativeInt, id='NonNegativeInt'),
        pytest.param(StrictInt, id='StrictInt'),
        pytest.param(confloat, id='confloat'),
        pytest.param(PositiveFloat, id='PositiveFloat'),
        pytest.param(NegativeFloat, id='NegativeFloat'),
        pytest.param(NonPositiveFloat, id='NonPositiveFloat'),
        pytest.param(NonNegativeFloat, id='NonNegativeFloat'),
        pytest.param(StrictFloat, id='StrictFloat'),
        pytest.param(FiniteFloat, id='FiniteFloat'),
        pytest.param(conbytes, id='conbytes'),
        pytest.param(Secret, id='Secret'),
        pytest.param(SecretBytes, id='SecretBytes'),
        pytest.param(constr, id='constr'),
        pytest.param(StrictStr, id='StrictStr'),
        pytest.param(SecretStr, id='SecretStr'),
        pytest.param(ImportString, id='ImportString'),
        pytest.param(conset, id='conset'),
        pytest.param(confrozenset, id='confrozenset'),
        pytest.param(conlist, id='conlist'),
        pytest.param(condecimal, id='condecimal'),
        pytest.param(UUID1, id='UUID1'),
        pytest.param(UUID3, id='UUID3'),
        pytest.param(UUID4, id='UUID4'),
        pytest.param(UUID5, id='UUID5'),
        pytest.param(FilePath, id='FilePath'),
        pytest.param(DirectoryPath, id='DirectoryPath'),
        pytest.param(NewPath, id='NewPath'),
        pytest.param(Json, id='Json'),
        pytest.param(ByteSize, id='ByteSize'),
        pytest.param(condate, id='condate'),
        pytest.param(PastDate, id='PastDate'),
        pytest.param(FutureDate, id='FutureDate'),
        pytest.param(PastDatetime, id='PastDatetime'),
        pytest.param(FutureDatetime, id='FutureDatetime'),
        pytest.param(AwareDatetime, id='AwareDatetime'),
        pytest.param(NaiveDatetime, id='NaiveDatetime'),
    ],
)
def test_is_hashable(pydantic_type):
    assert type(hash(pydantic_type)) is int


def test_model_contain_hashable_type():
    class MyModel(BaseModel):
        v: str | StrictStr

    assert MyModel(v='test').v == 'test'


def test_secretstr_error():
    class Foobar(BaseModel):
        password: SecretStr

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=[6, 23, 'abc'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': ('password',),
            'msg': 'Input should be a valid string',
            'input': [6, 23, 'abc'],
        }
    ]


def test_secret_str_hashable():
    assert type(hash(SecretStr('abs'))) is int


def test_secret_bytes_hashable():
    assert type(hash(SecretBytes(b'abs'))) is int


def test_secret_str_min_max_length():
    class Foobar(BaseModel):
        password: SecretStr = Field(min_length=6, max_length=10)

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password='')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('password',),
            'msg': 'Value should have at least 6 items after validation, not 0',
            'input': '',
            'ctx': {'field_type': 'Value', 'min_length': 6, 'actual_length': 0},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password='1' * 20)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('password',),
            'msg': 'Value should have at most 10 items after validation, not 20',
            'input': '11111111111111111111',
            'ctx': {'field_type': 'Value', 'max_length': 10, 'actual_length': 20},
        }
    ]

    value = '1' * 8
    assert Foobar(password=value).password.get_secret_value() == value


def test_secretbytes_json():
    class Foobar(BaseModel):
        password: SecretBytes

    assert Foobar(password='foo').model_dump_json() == '{"password":"**********"}'


def test_secretbytes():
    class Foobar(BaseModel):
        password: SecretBytes
        empty_password: SecretBytes

    # Initialize the model.
    # Use bytes that can't be decoded with UTF8 (https://github.com/pydantic/pydantic/issues/7971)
    password = b'\x89PNG\r\n\x1a\n'
    f = Foobar(password=password, empty_password=b'')

    # Assert correct types.
    assert f.password.__class__.__name__ == 'SecretBytes'
    assert f.empty_password.__class__.__name__ == 'SecretBytes'

    # Assert str and repr are correct.
    assert str(f.password) == "b'**********'"
    assert str(f.empty_password) == "b''"
    assert repr(f.password) == "SecretBytes(b'**********')"
    assert repr(f.empty_password) == "SecretBytes(b'')"

    # Assert retrieval of secret value is correct
    assert f.password.get_secret_value() == password
    assert f.empty_password.get_secret_value() == b''

    # Assert that SecretBytes is equal to SecretBytes if the secret is the same.
    assert f == f.model_copy()
    copied_with_changes = f.model_copy()
    copied_with_changes.password = SecretBytes(b'4321')
    assert f != copied_with_changes


def test_secretbytes_equality():
    assert SecretBytes(b'abc') == SecretBytes(b'abc')
    assert SecretBytes(b'123') != SecretBytes(b'321')
    assert SecretBytes(b'123') != b'123'
    assert SecretBytes(b'123') is not SecretBytes(b'123')


def test_secretbytes_idempotent():
    class Foobar(BaseModel):
        password: SecretBytes

    # Should not raise an exception.
    _ = Foobar(password=SecretBytes(b'1234'))


def test_secretbytes_error():
    class Foobar(BaseModel):
        password: SecretBytes

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=[6, 23, 'abc'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'bytes_type',
            'loc': ('password',),
            'msg': 'Input should be a valid bytes',
            'input': [6, 23, 'abc'],
        }
    ]


def test_secret_bytes_min_max_length():
    class Foobar(BaseModel):
        password: SecretBytes = Field(min_length=6, max_length=10)

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=b'')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('password',),
            'msg': 'Value should have at least 6 items after validation, not 0',
            'input': b'',
            'ctx': {'field_type': 'Value', 'min_length': 6, 'actual_length': 0},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=b'1' * 20)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('password',),
            'msg': 'Value should have at most 10 items after validation, not 20',
            'input': b'11111111111111111111',
            'ctx': {'field_type': 'Value', 'max_length': 10, 'actual_length': 20},
        }
    ]

    value = b'1' * 8
    assert Foobar(password=value).password.get_secret_value() == value


def test_generic_without_params():
    class Model(BaseModel):
        generic_list: list
        generic_dict: dict
        generic_tuple: tuple

    m = Model(generic_list=[0, 'a'], generic_dict={0: 'a', 'a': 0}, generic_tuple=(1, 'q'))
    assert m.model_dump() == {'generic_list': [0, 'a'], 'generic_dict': {0: 'a', 'a': 0}, 'generic_tuple': (1, 'q')}


def test_generic_without_params_error():
    class Model(BaseModel):
        generic_list: list
        generic_dict: dict
        generic_tuple: tuple

    with pytest.raises(ValidationError) as exc_info:
        Model(generic_list=0, generic_dict=0, generic_tuple=0)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': ('generic_list',),
            'msg': 'Input should be a valid list',
            'input': 0,
        },
        {
            'type': 'dict_type',
            'loc': ('generic_dict',),
            'msg': 'Input should be a valid dictionary',
            'input': 0,
        },
        {'type': 'tuple_type', 'loc': ('generic_tuple',), 'msg': 'Input should be a valid tuple', 'input': 0},
    ]


@pytest.mark.parametrize(
    'input_value,output,human_bin,human_dec,human_sep',
    (
        pytest.param(1, 1, '1B', '1B', '1 B', id='1_int-1_int-1B-1B-1 B'),
        pytest.param('1', 1, '1B', '1B', '1 B', id='1_str-1_int-1B-1B-1 B'),
        ('1.0', 1, '1B', '1B', '1 B'),
        ('1b', 1, '1B', '1B', '1 B'),
        ('1.5 KB', int(1.5e3), '1.5KiB', '1.5KB', '1.5 KiB'),
        ('1.5 K', int(1.5e3), '1.5KiB', '1.5KB', '1.5 KiB'),
        ('1.5 MB', int(1.5e6), '1.4MiB', '1.5MB', '1.4 MiB'),
        ('1.5 M', int(1.5e6), '1.4MiB', '1.5MB', '1.4 MiB'),
        ('5.1kib', 5222, '5.1KiB', '5.2KB', '5.1 KiB'),
        ('6.2EiB', 7148113328562451456, '6.2EiB', '7.1EB', '6.2 EiB'),
        ('8bit', 1, '1B', '1B', '1 B'),
        ('1kbit', 125, '125B', '125B', '125 B'),
    ),
)
def test_bytesize_conversions(input_value, output, human_bin, human_dec, human_sep):
    class Model(BaseModel):
        size: ByteSize

    m = Model(size=input_value)

    assert m.size == output

    assert m.size.human_readable() == human_bin
    assert m.size.human_readable(decimal=True) == human_dec
    assert m.size.human_readable(separator=' ') == human_sep


def test_bytesize_to():
    class Model(BaseModel):
        size: ByteSize

    m = Model(size='1GiB')

    assert m.size.to('MiB') == pytest.approx(1024)
    assert m.size.to('MB') == pytest.approx(1073.741824)
    assert m.size.to('TiB') == pytest.approx(0.0009765625)
    assert m.size.to('bit') == pytest.approx(8589934592)
    assert m.size.to('kbit') == pytest.approx(8589934.592)


def test_bytesize_raises():
    class Model(BaseModel):
        size: ByteSize

    with pytest.raises(ValidationError, match='parse value') as exc_info:
        Model(size='d1MB')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'd1MB',
            'loc': ('size',),
            'msg': 'could not parse value and unit from byte string',
            'type': 'byte_size',
        }
    ]

    with pytest.raises(ValidationError, match='byte unit') as exc_info:
        Model(size='1LiB')
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'unit': 'LiB'},
            'input': '1LiB',
            'loc': ('size',),
            'msg': 'could not interpret byte unit: LiB',
            'type': 'byte_size_unit',
        }
    ]

    # 1Gi is not a valid unit unlike 1G
    with pytest.raises(ValidationError, match='byte unit'):
        Model(size='1Gi')

    m = Model(size='1MB')
    with pytest.raises(PydanticCustomError, match='byte unit'):
        m.size.to('bad_unit')

    with pytest.raises(PydanticCustomError, match='byte unit'):
        m.size.to('1ZiB')


def test_custom_generic_containers():
    T = TypeVar('T')

    class GenericList(list[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(GenericList, handler(list[get_args(source_type)[0]]))

    class Model(BaseModel):
        field: GenericList[int]

    model = Model(field=['1', '2'])
    assert model.field == [1, 2]
    assert isinstance(model.field, GenericList)

    with pytest.raises(ValidationError) as exc_info:
        Model(field=['a'])
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('field', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


@pytest.mark.parametrize(
    ('field_type', 'input_data', 'expected_value', 'serialized_data'),
    [
        pytest.param(Base64Bytes, b'Zm9vIGJhcg==', b'foo bar', b'Zm9vIGJhcg==', id='Base64Bytes-bytes-input'),
        pytest.param(Base64Bytes, 'Zm9vIGJhcg==', b'foo bar', b'Zm9vIGJhcg==', id='Base64Bytes-str-input'),
        pytest.param(
            Base64Bytes, bytearray(b'Zm9vIGJhcg=='), b'foo bar', b'Zm9vIGJhcg==', id='Base64Bytes-bytearray-input'
        ),
        pytest.param(Base64Str, b'Zm9vIGJhcg==', 'foo bar', 'Zm9vIGJhcg==', id='Base64Str-bytes-input'),
        pytest.param(Base64Str, 'Zm9vIGJhcg==', 'foo bar', 'Zm9vIGJhcg==', id='Base64Str-str-input'),
        pytest.param(Base64Str, bytearray(b'Zm9vIGJhcg=='), 'foo bar', 'Zm9vIGJhcg==', id='Base64Str-bytearray-input'),
        pytest.param(
            Base64Bytes,
            b'BCq+6+1/Paun/Q==',
            b'\x04*\xbe\xeb\xed\x7f=\xab\xa7\xfd',
            b'BCq+6+1/Paun/Q==',
            id='Base64Bytes-bytes-alphabet-vanilla',
        ),
    ],
)
def test_base64(field_type, input_data, expected_value, serialized_data):
    class Model(BaseModel):
        base64_value: field_type
        base64_value_or_none: field_type | None = None

    m = Model(base64_value=input_data)
    assert m.base64_value == expected_value

    m = Model.model_construct(base64_value=expected_value)
    assert m.base64_value == expected_value

    assert m.model_dump() == {
        'base64_value': serialized_data,
        'base64_value_or_none': None,
    }

    assert Model.model_json_schema() == {
        'properties': {
            'base64_value': {
                'format': 'base64',
                'title': 'Base64 Value',
                'type': 'string',
            },
            'base64_value_or_none': {
                'anyOf': [{'type': 'string', 'format': 'base64'}, {'type': 'null'}],
                'default': None,
                'title': 'Base64 Value Or None',
            },
        },
        'required': ['base64_value'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize(
    ('field_type', 'input_data'),
    [
        pytest.param(Base64Bytes, b'Zm9vIGJhcg', id='Base64Bytes-invalid-base64-bytes'),
        pytest.param(Base64Bytes, 'Zm9vIGJhcg', id='Base64Bytes-invalid-base64-str'),
        pytest.param(Base64Str, b'Zm9vIGJhcg', id='Base64Str-invalid-base64-bytes'),
        pytest.param(Base64Str, 'Zm9vIGJhcg', id='Base64Str-invalid-base64-str'),
    ],
)
def test_base64_invalid(field_type, input_data):
    class Model(BaseModel):
        base64_value: field_type

    with pytest.raises(ValidationError) as e:
        Model(base64_value=input_data)

    assert e.value.errors(include_url=False) == [
        {
            'ctx': {'error': 'Incorrect padding'},
            'input': input_data,
            'loc': ('base64_value',),
            'msg': "Base64 decoding error: 'Incorrect padding'",
            'type': 'base64_decode',
        },
    ]


@pytest.mark.parametrize(
    ('field_type', 'input_data', 'expected_value', 'serialized_data'),
    [
        pytest.param(Base64UrlBytes, b'Zm9vIGJhcg==\n', b'foo bar', b'Zm9vIGJhcg==', id='Base64UrlBytes-reversible'),
        pytest.param(Base64UrlStr, 'Zm9vIGJhcg==\n', 'foo bar', 'Zm9vIGJhcg==', id='Base64UrlStr-reversible'),
        pytest.param(Base64UrlBytes, b'Zm9vIGJhcg==', b'foo bar', b'Zm9vIGJhcg==', id='Base64UrlBytes-bytes-input'),
        pytest.param(Base64UrlBytes, 'Zm9vIGJhcg==', b'foo bar', b'Zm9vIGJhcg==', id='Base64UrlBytes-str-input'),
        pytest.param(
            Base64UrlBytes, bytearray(b'Zm9vIGJhcg=='), b'foo bar', b'Zm9vIGJhcg==', id='Base64UrlBytes-bytearray-input'
        ),
        pytest.param(Base64UrlStr, b'Zm9vIGJhcg==', 'foo bar', 'Zm9vIGJhcg==', id='Base64UrlStr-bytes-input'),
        pytest.param(Base64UrlStr, 'Zm9vIGJhcg==', 'foo bar', 'Zm9vIGJhcg==', id='Base64UrlStr-str-input'),
        pytest.param(
            Base64UrlStr, bytearray(b'Zm9vIGJhcg=='), 'foo bar', 'Zm9vIGJhcg==', id='Base64UrlStr-bytearray-input'
        ),
        pytest.param(
            Base64UrlBytes,
            b'BCq-6-1_Paun_Q==',
            b'\x04*\xbe\xeb\xed\x7f=\xab\xa7\xfd',
            b'BCq-6-1_Paun_Q==',
            id='Base64UrlBytes-bytes-alphabet-url',
        ),
        pytest.param(
            Base64UrlBytes,
            b'BCq+6+1/Paun/Q==',
            b'\x04*\xbe\xeb\xed\x7f=\xab\xa7\xfd',
            b'BCq-6-1_Paun_Q==',
            id='Base64UrlBytes-bytes-alphabet-vanilla',
        ),
    ],
)
def test_base64url(field_type, input_data, expected_value, serialized_data):
    class Model(BaseModel):
        base64url_value: field_type
        base64url_value_or_none: field_type | None = None

    m = Model(base64url_value=input_data)
    assert m.base64url_value == expected_value

    m = Model.model_construct(base64url_value=expected_value)
    assert m.base64url_value == expected_value

    assert m.model_dump() == {
        'base64url_value': serialized_data,
        'base64url_value_or_none': None,
    }

    assert Model.model_json_schema() == {
        'properties': {
            'base64url_value': {
                'format': 'base64url',
                'title': 'Base64Url Value',
                'type': 'string',
            },
            'base64url_value_or_none': {
                'anyOf': [{'type': 'string', 'format': 'base64url'}, {'type': 'null'}],
                'default': None,
                'title': 'Base64Url Value Or None',
            },
        },
        'required': ['base64url_value'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize(
    ('field_type', 'input_data'),
    [
        pytest.param(Base64UrlBytes, b'Zm9vIGJhcg', id='Base64UrlBytes-invalid-base64-bytes'),
        pytest.param(Base64UrlBytes, 'Zm9vIGJhcg', id='Base64UrlBytes-invalid-base64-str'),
        pytest.param(Base64UrlStr, b'Zm9vIGJhcg', id='Base64UrlStr-invalid-base64-bytes'),
        pytest.param(Base64UrlStr, 'Zm9vIGJhcg', id='Base64UrlStr-invalid-base64-str'),
    ],
)
def test_base64url_invalid(field_type, input_data):
    class Model(BaseModel):
        base64url_value: field_type

    with pytest.raises(ValidationError) as e:
        Model(base64url_value=input_data)

    assert e.value.errors(include_url=False) == [
        {
            'ctx': {'error': 'Incorrect padding'},
            'input': input_data,
            'loc': ('base64url_value',),
            'msg': "Base64 decoding error: 'Incorrect padding'",
            'type': 'base64_decode',
        },
    ]


def test_handle_3rd_party_custom_type_reusing_known_metadata() -> None:
    class PdDecimal(Decimal):
        def ___repr__(self) -> str:
            return f'PdDecimal({super().__repr__()})'

    class PdDecimalMarker:
        def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(PdDecimal, handler.generate_schema(Decimal))

    class Model(BaseModel):
        x: Annotated[PdDecimal, PdDecimalMarker(), annotated_types.Gt(0)]

    assert isinstance(Model(x=1).x, PdDecimal)
    with pytest.raises(ValidationError) as exc_info:
        Model(x=-1)

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('x',),
            'msg': 'Input should be greater than 0',
            'input': -1,
            'ctx': {'gt': 0},
        }
    ]


@pytest.mark.parametrize('optional', [True, False])
def test_skip_validation(optional):
    type_hint = SkipValidation[int]
    if optional:
        type_hint = type_hint | None

    @validate_call
    def my_function(y: type_hint):
        return repr(y)

    assert my_function('2') == "'2'"


def test_skip_validation_model_reference():
    class ModelA(BaseModel):
        x: int

    class ModelB(BaseModel):
        y: SkipValidation[ModelA]

    assert ModelB(y=123).y == 123


def test_skip_validation_serialization():
    class A(BaseModel):
        x: SkipValidation[int]

        @field_serializer('x')
        def double_x(self, v):
            return v * 2

    assert A(x=1).model_dump() == {'x': 2}
    assert A(x='abc').model_dump() == {'x': 'abcabc'}  # no validation
    assert A(x='abc').model_dump_json() == '{"x":"abcabc"}'


def test_skip_validation_json_schema():
    class A(BaseModel):
        x: SkipValidation[int]

    assert A.model_json_schema() == {
        'properties': {'x': {'title': 'X', 'type': 'integer'}},
        'required': ['x'],
        'title': 'A',
        'type': 'object',
    }


def test_validate_as() -> None:
    class Arbitrary:
        def __init__(self, a: int) -> None:
            self.a = a

        def __eq__(self, other) -> bool:
            return self.a == other.a

    class ArbitraryModel(BaseModel):
        a: int

    ta = TypeAdapter(Annotated[Arbitrary, ValidateAs(ArbitraryModel, instantiation_hook=lambda v: Arbitrary(a=v.a))])

    assert ta.validate_python({'a': 1}) == Arbitrary(1)


def test_validate_as_known_serialization() -> None:
    """https://github.com/pydantic/pydantic/issues/13460"""

    def first_even(nums: list[int]) -> int:
        for i in nums:
            if i % 2 == 0:
                return i
        raise ValueError('Even not found.')

    class Model(BaseModel):
        x: Annotated[int, ValidateAs(list[int], first_even)]

    m = Model(x=[1, 2])

    assert m.model_dump_json() == '{"x":2}'


def test_validate_as_unknown_serialization() -> None:

    class Arbitrary:
        def __init__(self, a: int) -> None:
            self.a = a

        def __eq__(self, other) -> bool:
            return self.a == other.a

    ta = TypeAdapter(Annotated[Arbitrary, ValidateAs(int, instantiation_hook=Arbitrary)])

    assert ta.dump_python(Arbitrary(1)) == Arbitrary(1)


@pytest.mark.skipif(sys.version_info < (3, 12), reason="`Annotated` doesn't allow instances in <3.12")
def test_skip_validation_arbitrary_type_object() -> None:
    """https://github.com/pydantic/pydantic/issues/11997.

    Using an arbitrary object (and not a type) normally raises a warning,
    which should be suppressed when using `SkipValidation`.
    """

    with warnings.catch_warnings():
        warnings.simplefilter('error')

        class Model(BaseModel, arbitrary_types_allowed=True):
            field: Annotated[object(), SkipValidation]


def test_transform_schema():
    ValidateStrAsInt = Annotated[str, GetPydanticSchema(lambda _s, h: core_schema.int_schema())]

    class Model(BaseModel):
        x: ValidateStrAsInt | None

    assert Model(x=None).x is None
    assert Model(x='1').x == 1


def test_transform_schema_for_first_party_class():
    # Here, first party means you can define the `__get_pydantic_core_schema__` method on the class directly.
    class LowercaseStr(str):
        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source_type: Any,
            handler: GetCoreSchemaHandler,
        ) -> CoreSchema:
            schema = handler(str)
            return core_schema.no_info_after_validator_function(lambda v: v.lower(), schema)

    class Model(BaseModel):
        lower: LowercaseStr = Field(min_length=1)

    assert Model(lower='ABC').lower == 'abc'

    with pytest.raises(ValidationError) as exc_info:
        Model(lower='')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('lower',),
            'msg': 'Value should have at least 1 item after validation, not 0',
            'input': '',
            'ctx': {'field_type': 'Value', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_constraint_dataclass() -> None:
    @dataclass(order=True)
    # need to make it inherit from int so that
    # because the PydanticKnownError requires it to be a number
    # but it's not really relevant to this test
    class MyDataclass(int):
        x: int

    ta = TypeAdapter(Annotated[MyDataclass, annotated_types.Gt(MyDataclass(0))])

    assert ta.validate_python(MyDataclass(1)) == MyDataclass(1)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(MyDataclass(0))

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': (),
            'msg': 'Input should be greater than 0',
            'input': MyDataclass(0),
            'ctx': {'gt': MyDataclass(0)},
        }
    ]


def test_transform_schema_for_third_party_class():
    # Here, third party means you can't define methods on the class directly, so have to use annotations.

    class IntWrapper:
        # This is pretending to be a third-party class. This example is specifically inspired by pandas.Timestamp,
        # which can receive an item of type `datetime` as an input to its `__init__`.
        # The important thing here is we are not defining any custom methods on this type directly.
        def __init__(self, t: int) -> None:
            self.t = t

        def __eq__(self, value: object) -> bool:
            if isinstance(value, IntWrapper):
                return self.t == value.t
            elif isinstance(value, int):
                return self.t == value
            return False

        def __gt__(self, value: object) -> bool:
            if isinstance(value, IntWrapper):
                return self.t > value.t
            elif isinstance(value, int):
                return self.t > value
            return NotImplemented

    class _IntWrapperAnnotation:
        # This is an auxiliary class that, when used as the first annotation for DatetimeWrapper,
        # ensures pydantic can produce a valid schema.
        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source_type: Any,
            handler: GetCoreSchemaHandler,
        ) -> CoreSchema:
            schema = handler.generate_schema(int)
            return core_schema.no_info_after_validator_function(IntWrapper, schema)

    # Giving a name to Annotated[IntWrapper, _IntWrapperAnnotation] makes it easier to use in code
    # where I want a field of type `IntWrapper` that works as desired with pydantic.
    PydanticDatetimeWrapper = Annotated[IntWrapper, _IntWrapperAnnotation]

    class Model(BaseModel):
        # The reason all of the above is necessary is specifically so that we get good behavior
        x: Annotated[PydanticDatetimeWrapper, annotated_types.Gt(123)]

    m = Model(x=1234)
    assert isinstance(m.x, IntWrapper)
    assert repr(m.x.t) == '1234'

    with pytest.raises(ValidationError) as exc_info:
        Model(x=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('x',),
            'msg': 'Input should be greater than 123',
            'input': 1,
            'ctx': {'gt': 123},
        }
    ]


def test_instance_of_annotation():
    class Model(BaseModel):
        # Note: the generic parameter gets ignored by runtime validation
        x: InstanceOf[Sequence[int]]

    class MyList(list):
        pass

    assert Model(x='abc').x == 'abc'
    assert type(Model(x=MyList([1, 2, 3])).x) is MyList

    with pytest.raises(ValidationError) as exc_info:
        Model(x=1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'Sequence'},
            'input': 1,
            'loc': ('x',),
            'msg': 'Input should be an instance of Sequence',
            'type': 'is_instance_of',
        }
    ]

    assert Model.model_validate_json('{"x": [1,2,3]}').x == [1, 2, 3]
    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate_json('{"x": "abc"}')
    assert exc_info.value.errors(include_url=False) == [
        {'input': 'abc', 'loc': ('x',), 'msg': 'Input should be a valid array', 'type': 'list_type'}
    ]


def test_instanceof_invalid_core_schema():
    class MyClass:
        pass

    @dataclass
    class ClassWithInvalidAnnotations:
        a: 'Unknown' = 1  # noqa: F821
        b: NotRequired[int] = 1

    class MyModel(BaseModel):
        a: InstanceOf[MyClass]
        b: InstanceOf[MyClass] | None
        c: InstanceOf[ClassWithInvalidAnnotations]

    MyModel(a=MyClass(), b=None, c=ClassWithInvalidAnnotations())
    MyModel(a=MyClass(), b=MyClass(), c=ClassWithInvalidAnnotations())

    with pytest.raises(ValidationError) as exc_info:
        MyModel(a=1, b=1, c=1)

    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'test_instanceof_invalid_core_schema.<locals>.MyClass'},
            'input': 1,
            'loc': ('a',),
            'msg': 'Input should be an instance of test_instanceof_invalid_core_schema.<locals>.MyClass',
            'type': 'is_instance_of',
        },
        {
            'ctx': {'class': 'test_instanceof_invalid_core_schema.<locals>.MyClass'},
            'input': 1,
            'loc': ('b',),
            'msg': 'Input should be an instance of test_instanceof_invalid_core_schema.<locals>.MyClass',
            'type': 'is_instance_of',
        },
        {
            'ctx': {'class': 'test_instanceof_invalid_core_schema.<locals>.ClassWithInvalidAnnotations'},
            'input': 1,
            'loc': ('c',),
            'msg': 'Input should be an instance of test_instanceof_invalid_core_schema.<locals>.ClassWithInvalidAnnotations',
            'type': 'is_instance_of',
        },
    ]
    with pytest.raises(
        PydanticInvalidForJsonSchema, match='Cannot generate a JsonSchema for core_schema.IsInstanceSchema'
    ):
        MyModel.model_json_schema()


def test_instanceof_serialization():
    class Inner(BaseModel):
        pass

    class SubInner(Inner):
        x: int

    class OuterStandard(BaseModel):
        inner: InstanceOf[Inner]

    assert OuterStandard(inner=SubInner(x=1)).model_dump() == {'inner': {}}

    class OuterAsAny(BaseModel):
        inner1: SerializeAsAny[InstanceOf[Inner]]
        inner2: InstanceOf[SerializeAsAny[Inner]]

    assert OuterAsAny(inner1=SubInner(x=2), inner2=SubInner(x=3)).model_dump() == {
        'inner1': {'x': 2},
        'inner2': {'x': 3},
    }


def test_constraints_arbitrary_type() -> None:
    class CustomType:
        def __init__(self, v: Any) -> None:
            self.v = v

        def __eq__(self, o: object) -> bool:
            return self.v == o

        def __le__(self, o: object) -> bool:
            return self.v <= o

        def __lt__(self, o: object) -> bool:
            return self.v < o

        def __ge__(self, o: object) -> bool:
            return self.v >= o

        def __gt__(self, o: object) -> bool:
            return self.v > o

        def __mod__(self, o: Any) -> Any:
            return self.v % o

        def __len__(self) -> int:
            return len(self.v)

        def __repr__(self) -> str:
            return f'CustomType({self.v})'

    class Model(BaseModel):
        gt: Annotated[CustomType, annotated_types.Gt(0)]
        ge: Annotated[CustomType, annotated_types.Ge(0)]
        lt: Annotated[CustomType, annotated_types.Lt(0)]
        le: Annotated[CustomType, annotated_types.Le(0)]
        multiple_of: Annotated[CustomType, annotated_types.MultipleOf(2)]
        min_length: Annotated[CustomType, annotated_types.MinLen(1)]
        max_length: Annotated[CustomType, annotated_types.MaxLen(1)]
        predicate: Annotated[CustomType, annotated_types.Predicate(lambda x: x > 0)]
        not_multiple_of_3: Annotated[CustomType, annotated_types.Not(lambda x: x % 3 == 0)]

        model_config = ConfigDict(arbitrary_types_allowed=True)

    Model(
        gt=CustomType(1),
        ge=CustomType(0),
        lt=CustomType(-1),
        le=CustomType(0),
        min_length=CustomType([1, 2]),
        max_length=CustomType([1]),
        multiple_of=CustomType(4),
        predicate=CustomType(1),
        not_multiple_of_3=CustomType(4),
    )

    with pytest.raises(ValidationError) as exc_info:
        Model(
            gt=CustomType(-1),
            ge=CustomType(-1),
            lt=CustomType(1),
            le=CustomType(1),
            min_length=CustomType([]),
            max_length=CustomType([1, 2, 3]),
            multiple_of=CustomType(3),
            predicate=CustomType(-1),
            not_multiple_of_3=CustomType(6),
        )
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('gt',),
            'msg': 'Input should be greater than 0',
            'input': CustomType(-1),
            'ctx': {'gt': 0},
        },
        {
            'type': 'greater_than_equal',
            'loc': ('ge',),
            'msg': 'Input should be greater than or equal to 0',
            'input': CustomType(-1),
            'ctx': {'ge': 0},
        },
        {
            'type': 'less_than',
            'loc': ('lt',),
            'msg': 'Input should be less than 0',
            'input': CustomType(1),
            'ctx': {'lt': 0},
        },
        {
            'type': 'less_than_equal',
            'loc': ('le',),
            'msg': 'Input should be less than or equal to 0',
            'input': CustomType(1),
            'ctx': {'le': 0},
        },
        {
            'type': 'multiple_of',
            'loc': ('multiple_of',),
            'msg': 'Input should be a multiple of 2',
            'input': CustomType(3),
            'ctx': {'multiple_of': 2},
        },
        {
            'type': 'too_short',
            'loc': ('min_length',),
            'msg': 'Value should have at least 1 item after validation, not 0',
            'input': CustomType([]),
            'ctx': {'field_type': 'Value', 'min_length': 1, 'actual_length': 0},
        },
        {
            'type': 'too_long',
            'loc': ('max_length',),
            'msg': 'Value should have at most 1 item after validation, not 3',
            'input': CustomType([1, 2, 3]),
            'ctx': {'field_type': 'Value', 'max_length': 1, 'actual_length': 3},
        },
        {
            'type': 'predicate_failed',
            'loc': ('predicate',),
            'msg': "Predicate 'test_constraints_arbitrary_type.<locals>.Model.<lambda>' failed",
            'input': CustomType(-1),
        },
        {
            'type': 'not_operation_failed',
            'loc': ('not_multiple_of_3',),
            'msg': "Not of 'test_constraints_arbitrary_type.<locals>.Model.<lambda>' failed",
            'input': CustomType(6),
        },
    ]


def test_annotated_default_value() -> None:
    t = TypeAdapter(Annotated[list[int], Field(default=['1', '2'])])

    r = t.get_default_value()
    assert r is not None
    assert r.value == ['1', '2']

    # insert_assert(t.json_schema())
    assert t.json_schema() == {'type': 'array', 'items': {'type': 'integer'}, 'default': ['1', '2']}


def test_annotated_default_value_validate_default() -> None:
    t = TypeAdapter(Annotated[list[int], Field(default=['1', '2'])], config=ConfigDict(validate_default=True))

    r = t.get_default_value()
    assert r is not None
    assert r.value == [1, 2]

    # insert_assert(t.json_schema())
    assert t.json_schema() == {'type': 'array', 'items': {'type': 'integer'}, 'default': ['1', '2']}


def test_annotated_default_value_functional_validator() -> None:
    T = TypeVar('T')
    WithAfterValidator = Annotated[T, AfterValidator(lambda x: [v * 2 for v in x])]
    WithDefaultValue = Annotated[T, Field(default=['1', '2'])]

    # the order of the args should not matter, we always put the default value on the outside
    for tp in (WithDefaultValue[WithAfterValidator[list[int]]], WithAfterValidator[WithDefaultValue[list[int]]]):
        t = TypeAdapter(tp, config=ConfigDict(validate_default=True))

        r = t.get_default_value()
        assert r is not None
        assert r.value == [2, 4]

        # insert_assert(t.json_schema())
        assert t.json_schema() == {'type': 'array', 'items': {'type': 'integer'}, 'default': ['1', '2']}


def test_importstring_reports_internal_import_error(tmp_path, monkeypatch):
    # Create a module that exists, but fails to import due to missing dependency
    (tmp_path / 'my_module.py').write_text('import definitely_missing_dep_xyz\n\nclass MyClass:\n    pass\n')
    monkeypatch.syspath_prepend(tmp_path)

    adapter = TypeAdapter(ImportString)

    with pytest.raises(ValidationError, match="No module named 'definitely_missing_dep_xyz'"):
        adapter.validate_python('my_module.MyClass')


def test_import_string_explicit_colon_does_not_try_dot_fallback():
    # Regression test: if the input already contains ':attr', we should NOT try
    # to reinterpret dots as module/attribute splits (which could accidentally
    # create an invalid import string containing two colons).
    adapter = TypeAdapter(ImportString)

    # A buggy implementation might try to split 'collections.defaultdict' further
    # and create 'collections:defaultdict:get', which would be invalid
    with pytest.raises(ValidationError):
        adapter.validate_python('collections.defaultdict:get')


@pytest.mark.parametrize(
    'pydantic_type,expected',
    (
        (Json, 'Json'),
        (PastDate, 'PastDate'),
        (FutureDate, 'FutureDate'),
        (AwareDatetime, 'AwareDatetime'),
        (NaiveDatetime, 'NaiveDatetime'),
        (PastDatetime, 'PastDatetime'),
        (FutureDatetime, 'FutureDatetime'),
        (ImportString, 'ImportString'),
    ),
)
def test_types_repr(pydantic_type, expected):
    assert repr(pydantic_type()) == expected


def test_get_pydantic_core_schema_marker_unrelated_type() -> None:
    """Test using handler.generate_schema() to generate a schema that ignores
    the current context of annotations and such
    """

    @dataclass
    class Marker:
        num: int

        def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler.resolve_ref_schema(handler.generate_schema(source_type))
            return core_schema.no_info_after_validator_function(lambda x: x * self.num, schema)

    ta = TypeAdapter(Annotated[int, Marker(2), Marker(3)])

    assert ta.validate_python('1') == 3


def test_json_value():
    adapter = TypeAdapter(JsonValue)
    valid_json_data = {'a': {'b': {'c': 1, 'd': [2, None]}}}
    # would pass validation as a dict[str, Any]
    invalid_json_data = {'a': {'b': ...}}

    assert adapter.validate_python(valid_json_data) == valid_json_data
    assert adapter.validate_json(json.dumps(valid_json_data)) == valid_json_data

    with pytest.raises(ValidationError) as exc_info:
        adapter.validate_python(invalid_json_data)
    assert exc_info.value.errors() == [
        {
            'input': Ellipsis,
            'loc': ('dict', 'a', 'dict', 'b'),
            'msg': 'input was not a valid JSON value',
            'type': 'invalid-json-value',
        }
    ]


def test_json_value_with_subclassed_types():
    class IntType(int):
        pass

    class FloatType(float):
        pass

    class StrType(str):
        pass

    class ListType(list):
        pass

    class DictType(dict):
        pass

    adapter = TypeAdapter(JsonValue)
    valid_json_data = {'int': IntType(), 'float': FloatType(), 'str': StrType(), 'list': ListType(), 'dict': DictType()}
    assert adapter.validate_python(valid_json_data) == valid_json_data


def test_json_value_roundtrip() -> None:
    # see https://github.com/pydantic/pydantic/issues/8175
    class MyModel(BaseModel):
        val: str | JsonValue

    round_trip_value = json.loads(MyModel(val=True).model_dump_json())['val']
    assert round_trip_value is True, round_trip_value


def test_on_error_omit() -> None:
    OmittableInt = OnErrorOmit[int]

    class MyTypedDict(TypedDict):
        a: NotRequired[OmittableInt]
        b: NotRequired[OmittableInt]

    class Model(BaseModel):
        a_list: list[OmittableInt]
        a_dict: dict[OmittableInt, OmittableInt]
        a_typed_dict: MyTypedDict

    actual = Model(
        a_list=[1, 2, 'a', 3],
        a_dict={1: 1, 2: 2, 'a': 'a', 'b': 0, 3: 'c', 4: 4},
        a_typed_dict=MyTypedDict(a=1, b='xyz'),  # type: ignore
    )

    expected = Model(a_list=[1, 2, 3], a_dict={1: 1, 2: 2, 4: 4}, a_typed_dict=MyTypedDict(a=1))

    assert actual == expected


def test_on_error_omit_top_level() -> None:
    ta = TypeAdapter(OnErrorOmit[int])

    assert ta.validate_python(1) == 1
    assert ta.validate_python('1') == 1

    # we might want to just raise the OmitError or convert it to a ValidationError
    # if it hits the top level, but this documents the current behavior at least
    with pytest.raises(SchemaError, match='Uncaught Omit error'):
        ta.validate_python('a')


def test_omit() -> None:
    def omit_func(v):
        if v == 'omit':
            raise PydanticOmit
        elif v == 'error':
            raise ValueError('error')
        else:
            return v

    ta = TypeAdapter(Annotated[str, PlainValidator(omit_func)])

    assert ta.validate_python('foo') == 'foo'
    assert ta.validate_json('"foo"') == 'foo'

    with pytest.raises(ValidationError):
        ta.validate_python('error')

    with pytest.raises(SchemaError, match='Uncaught Omit error, please check your usage of `default` validators.'):
        ta.validate_python('omit')


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_constraints_on_str_like() -> None:
    """See https://github.com/pydantic/pydantic/issues/8577 for motivation."""

    class Foo(BaseModel):
        baz: Annotated[EmailStr, StringConstraints(to_lower=True, strip_whitespace=True)]

    assert Foo(baz=' uSeR@ExAmPlE.com  ').baz == 'user@example.com'


@pytest.mark.parametrize(
    'tp',
    [
        pytest.param(list[int], id='list'),
        pytest.param(tuple[int, ...], id='tuple'),
        pytest.param(set[int], id='set'),
        pytest.param(frozenset[int], id='frozenset'),
    ],
)
@pytest.mark.parametrize(
    ['fail_fast', 'decl'],
    [
        pytest.param(True, FailFast(), id='fail-fast-default'),
        pytest.param(True, FailFast(True), id='fail-fast-true'),
        pytest.param(False, FailFast(False), id='fail-fast-false'),
        pytest.param(False, Field(), id='field-default'),
        pytest.param(True, Field(fail_fast=True), id='field-true'),
        pytest.param(False, Field(fail_fast=False), id='field-false'),
    ],
)
def test_fail_fast(tp, fail_fast, decl) -> None:
    class Foo(BaseModel):
        a: Annotated[tp, decl]

    with pytest.raises(ValidationError) as exc_info:
        Foo(a=[1, 'a', 'c'])

    errors = [
        {
            'input': 'a',
            'loc': ('a', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        },
    ]

    if not fail_fast:
        errors.append(
            {
                'input': 'c',
                'loc': ('a', 2),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'type': 'int_parsing',
            },
        )

    assert exc_info.value.errors(include_url=False) == errors


def test_ser_ip_with_union() -> None:
    bool_first = TypeAdapter(Union[bool, ipaddress.IPv4Address])  # noqa: UP007
    assert bool_first.dump_python(True, mode='json') is True
    assert bool_first.dump_json(True) == b'true'

    ip_first = TypeAdapter(Union[ipaddress.IPv4Address, bool])  # noqa: UP007
    assert ip_first.dump_python(True, mode='json') is True
    assert ip_first.dump_json(True) == b'true'


def test_ser_ip_with_unexpected_value() -> None:
    ta = TypeAdapter(ipaddress.IPv4Address)

    with pytest.warns(UserWarning, match='serialized value may not be as expected.'):
        assert ta.dump_python(123)


def test_ser_ip_python_and_json() -> None:
    ta = TypeAdapter(ipaddress.IPv4Address)

    ip = ta.validate_python('127.0.0.1')
    assert ta.dump_python(ip) == ip
    assert ta.dump_python(ip, mode='json') == '127.0.0.1'
    assert ta.dump_json(ip) == b'"127.0.0.1"'


def test_annotated_metadata_any_order() -> None:
    def validator(v):
        if isinstance(v, (int, float)):
            return timedelta(days=v)
        return v

    class BeforeValidatorAfterLe(BaseModel):
        v: Annotated[timedelta, annotated_types.Le(timedelta(days=365)), BeforeValidator(validator)]

    class BeforeValidatorBeforeLe(BaseModel):
        v: Annotated[timedelta, BeforeValidator(validator), annotated_types.Le(timedelta(days=365))]

    try:
        BeforeValidatorAfterLe(v=366)
    except ValueError as ex:
        assert '365 days' in str(ex)

    # in this case, the Le constraint comes after the BeforeValidator, so we use functional validators
    # from pydantic._internal._validators.py (in this case, less_than_or_equal_validator)
    # which doesn't have access to fancy pydantic-core formatting for timedelta, so we get
    # the raw timedelta repr in the error `datetime.timedelta(days=365`` vs the above `365 days`
    try:
        BeforeValidatorBeforeLe(v=366)
    except ValueError as ex:
        assert 'datetime.timedelta(days=365)' in str(ex)


@pytest.mark.parametrize(
    'base64_type',
    [Base64Bytes, Base64Str, Base64UrlBytes, Base64UrlStr],
    ids=['Base64Bytes', 'Base64Str', 'Base64UrlBytes', 'Base64UrlStr'],
)
def test_base64_with_invalid_min_length(base64_type) -> None:
    """Check that an error is raised when the length of the base64 type's value is less or more than the min_length and max_length."""

    class Model(BaseModel):
        base64_value: base64_type = Field(min_length=3, max_length=5)  # type: ignore

    with pytest.raises(ValidationError):
        Model(**{'base64_value': b''})

    with pytest.raises(ValidationError):
        Model(**{'base64_value': b'123456'})


def test_serialize_as_any_secret_types() -> None:
    ta_secret_str = TypeAdapter(SecretStr)
    secret_str = ta_secret_str.validate_python('secret')

    ta_any = TypeAdapter(Any)

    assert ta_any.dump_python(secret_str) == secret_str
    assert ta_any.dump_python(secret_str, mode='json') == '**********'
    assert ta_any.dump_json(secret_str) == b'"**********"'

    ta_secret_bytes = TypeAdapter(SecretBytes)
    secret_bytes = ta_secret_bytes.validate_python(b'secret')

    assert ta_any.dump_python(secret_bytes) == secret_bytes
    assert ta_any.dump_python(secret_bytes, mode='json') == '**********'
    assert ta_any.dump_json(secret_bytes) == b'"**********"'

    ta_secret_date = TypeAdapter(SecretDate)
    secret_date = ta_secret_date.validate_python('2024-01-01')

    assert ta_any.dump_python(secret_date) == secret_date
    assert ta_any.dump_python(secret_date, mode='json') == '****/**/**'
    assert ta_any.dump_json(secret_date) == b'"****/**/**"'


def test_custom_serializer_override_secret_str() -> None:
    class User(BaseModel):
        name: str
        password: Annotated[SecretStr, PlainSerializer(lambda x: f'secret: {str(x)}')]

    u = User(name='sam', password='hi')
    assert u.model_dump()['password'] == 'secret: **********'


def test_secret_str_none() -> None:
    """https://github.com/pydantic/pydantic/issues/13692"""

    class Model(BaseModel):
        f: SecretStr = None

    assert Model.model_dump() == {'f': None}
    assert Model.model_dump_json() == '{"f":null}'
