import collections
import itertools
import json
import math
import os
import re
import sys
import typing
import uuid
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from numbers import Number
from pathlib import Path
from typing import (
    Any,
    Callable,
    Counter,
    DefaultDict,
    Deque,
    Dict,
    FrozenSet,
    Iterable,
    List,
    NewType,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
)
from uuid import UUID

import annotated_types
import dirty_equals
import pytest
from dirty_equals import HasRepr, IsFloatNan, IsOneOf, IsStr
from pydantic_core import CoreSchema, PydanticCustomError, SchemaError, core_schema
from typing_extensions import Annotated, Literal, NotRequired, TypedDict, get_args

from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    AfterValidator,
    AllowInfNan,
    AwareDatetime,
    Base64Bytes,
    Base64Str,
    Base64UrlBytes,
    Base64UrlStr,
    BaseModel,
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
    PositiveFloat,
    PositiveInt,
    PydanticInvalidForJsonSchema,
    PydanticSchemaGenerationError,
    Secret,
    SecretBytes,
    SecretStr,
    SerializeAsAny,
    SkipValidation,
    Strict,
    StrictBool,
    StrictBytes,
    StrictFloat,
    StrictInt,
    StrictStr,
    StringConstraints,
    Tag,
    TypeAdapter,
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
from pydantic.dataclasses import dataclass as pydantic_dataclass

try:
    import email_validator
except ImportError:
    email_validator = None


# TODO add back tests for Iterator


@pytest.fixture(scope='session', name='ConBytesModel')
def con_bytes_model_fixture():
    class ConBytesModel(BaseModel):
        v: conbytes(max_length=10) = b'foobar'

    return ConBytesModel


def test_constrained_bytes_good(ConBytesModel):
    m = ConBytesModel(v=b'short')
    assert m.v == b'short'


def test_constrained_bytes_default(ConBytesModel):
    m = ConBytesModel()
    assert m.v == b'foobar'


def test_strict_raw_type():
    class Model(BaseModel):
        v: Annotated[str, Strict]

    assert Model(v='foo').v == 'foo'
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[type=string_type,'):
        Model(v=b'fo')


@pytest.mark.parametrize(
    ('data', 'valid'),
    [(b'this is too long', False), ('⪶⓲⽷01'.encode(), False), (b'not long90', True), ('⪶⓲⽷0'.encode(), True)],
)
def test_constrained_bytes_too_long(ConBytesModel, data: bytes, valid: bool):
    if valid:
        assert ConBytesModel(v=data).model_dump() == {'v': data}
    else:
        with pytest.raises(ValidationError) as exc_info:
            ConBytesModel(v=data)
        # insert_assert(exc_info.value.errors(include_url=False))
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'max_length': 10},
                'input': data,
                'loc': ('v',),
                'msg': 'Data should have at most 10 bytes',
                'type': 'bytes_too_long',
            }
        ]


def test_constrained_bytes_strict_true():
    class Model(BaseModel):
        v: conbytes(strict=True)

    assert Model(v=b'foobar').v == b'foobar'
    with pytest.raises(ValidationError):
        Model(v=bytearray('foobar', 'utf-8'))

    with pytest.raises(ValidationError):
        Model(v='foostring')

    with pytest.raises(ValidationError):
        Model(v=42)

    with pytest.raises(ValidationError):
        Model(v=0.42)


def test_constrained_bytes_strict_false():
    class Model(BaseModel):
        v: conbytes(strict=False)

    assert Model(v=b'foobar').v == b'foobar'
    assert Model(v=bytearray('foobar', 'utf-8')).v == b'foobar'
    assert Model(v='foostring').v == b'foostring'

    with pytest.raises(ValidationError):
        Model(v=42)

    with pytest.raises(ValidationError):
        Model(v=0.42)


def test_constrained_bytes_strict_default():
    class Model(BaseModel):
        v: conbytes()

    assert Model(v=b'foobar').v == b'foobar'
    assert Model(v=bytearray('foobar', 'utf-8')).v == b'foobar'
    assert Model(v='foostring').v == b'foostring'

    with pytest.raises(ValidationError):
        Model(v=42)

    with pytest.raises(ValidationError):
        Model(v=0.42)


def test_constrained_list_good():
    class ConListModelMax(BaseModel):
        v: conlist(int) = []

    m = ConListModelMax(v=[1, 2, 3])
    assert m.v == [1, 2, 3]


def test_constrained_list_default():
    class ConListModelMax(BaseModel):
        v: conlist(int) = []

    m = ConListModelMax()
    assert m.v == []


def test_constrained_list_too_long():
    class ConListModelMax(BaseModel):
        v: conlist(int, max_length=10) = []

    with pytest.raises(ValidationError) as exc_info:
        ConListModelMax(v=list(str(i) for i in range(11)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('v',),
            'msg': 'List should have at most 10 items after validation, not 11',
            'input': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
            'ctx': {'field_type': 'List', 'max_length': 10, 'actual_length': 11},
        }
    ]


def test_constrained_list_too_short():
    class ConListModelMin(BaseModel):
        v: conlist(int, min_length=1)

    with pytest.raises(ValidationError) as exc_info:
        ConListModelMin(v=[])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('v',),
            'msg': 'List should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_constrained_list_optional():
    class Model(BaseModel):
        req: Optional[conlist(str, min_length=1)]
        opt: Optional[conlist(str, min_length=1)] = None

    assert Model(req=None).model_dump() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).model_dump() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=[], opt=[])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('req',),
            'msg': 'List should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        },
        {
            'type': 'too_short',
            'loc': ('opt',),
            'msg': 'List should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req=['a'], opt=['a']).model_dump() == {'req': ['a'], 'opt': ['a']}


def test_constrained_list_constraints():
    class ConListModelBoth(BaseModel):
        v: conlist(int, min_length=7, max_length=11)

    m = ConListModelBoth(v=list(range(7)))
    assert m.v == list(range(7))

    m = ConListModelBoth(v=list(range(11)))
    assert m.v == list(range(11))

    with pytest.raises(ValidationError) as exc_info:
        ConListModelBoth(v=list(range(6)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('v',),
            'msg': 'List should have at least 7 items after validation, not 6',
            'input': [0, 1, 2, 3, 4, 5],
            'ctx': {'field_type': 'List', 'min_length': 7, 'actual_length': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConListModelBoth(v=list(range(12)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('v',),
            'msg': 'List should have at most 11 items after validation, not 12',
            'input': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'ctx': {'field_type': 'List', 'max_length': 11, 'actual_length': 12},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConListModelBoth(v=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': ('v',), 'msg': 'Input should be a valid list', 'input': 1}
    ]


def test_constrained_list_item_type_fails():
    class ConListModel(BaseModel):
        v: conlist(int) = []

    with pytest.raises(ValidationError) as exc_info:
        ConListModel(v=['a', 'b', 'c'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('v', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': ('v', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
        {
            'type': 'int_parsing',
            'loc': ('v', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'c',
        },
    ]


def test_conlist():
    class Model(BaseModel):
        foo: List[int] = Field(..., min_length=2, max_length=4)
        bar: conlist(str, min_length=1, max_length=4) = None

    assert Model(foo=[1, 2], bar=['spoon']).model_dump() == {'foo': [1, 2], 'bar': ['spoon']}

    msg = r'List should have at least 2 items after validation, not 1 \[type=too_short,'
    with pytest.raises(ValidationError, match=msg):
        Model(foo=[1])

    msg = r'List should have at most 4 items after validation, not 5 \[type=too_long,'
    with pytest.raises(ValidationError, match=msg):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('foo', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
        {
            'type': 'int_parsing',
            'loc': ('foo', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': ('foo',), 'msg': 'Input should be a valid list', 'input': 1}
    ]


def test_conlist_wrong_type_default():
    """It should not validate default value by default"""

    class Model(BaseModel):
        v: conlist(int) = 'a'

    m = Model()
    assert m.v == 'a'


def test_constrained_set_good():
    class Model(BaseModel):
        v: conset(int) = []

    m = Model(v=[1, 2, 3])
    assert m.v == {1, 2, 3}


def test_constrained_set_default():
    class Model(BaseModel):
        v: conset(int) = set()

    m = Model()
    assert m.v == set()


def test_constrained_set_default_invalid():
    class Model(BaseModel):
        v: conset(int) = 'not valid, not validated'

    m = Model()
    assert m.v == 'not valid, not validated'


def test_constrained_set_too_long():
    class ConSetModelMax(BaseModel):
        v: conset(int, max_length=10) = []

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelMax(v={str(i) for i in range(11)})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('v',),
            'msg': 'Set should have at most 10 items after validation, not more',
            'input': {'4', '3', '10', '9', '5', '6', '1', '8', '0', '7', '2'},
            'ctx': {'field_type': 'Set', 'max_length': 10, 'actual_length': None},
        }
    ]


def test_constrained_set_too_short():
    class ConSetModelMin(BaseModel):
        v: conset(int, min_length=1)

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelMin(v=[])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('v',),
            'msg': 'Set should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_constrained_set_optional():
    class Model(BaseModel):
        req: Optional[conset(str, min_length=1)]
        opt: Optional[conset(str, min_length=1)] = None

    assert Model(req=None).model_dump() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).model_dump() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=set(), opt=set())
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('req',),
            'msg': 'Set should have at least 1 item after validation, not 0',
            'input': set(),
            'ctx': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        },
        {
            'type': 'too_short',
            'loc': ('opt',),
            'msg': 'Set should have at least 1 item after validation, not 0',
            'input': set(),
            'ctx': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req={'a'}, opt={'a'}).model_dump() == {'req': {'a'}, 'opt': {'a'}}


def test_constrained_set_constraints():
    class ConSetModelBoth(BaseModel):
        v: conset(int, min_length=7, max_length=11)

    m = ConSetModelBoth(v=set(range(7)))
    assert m.v == set(range(7))

    m = ConSetModelBoth(v=set(range(11)))
    assert m.v == set(range(11))

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=set(range(6)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('v',),
            'msg': 'Set should have at least 7 items after validation, not 6',
            'input': {0, 1, 2, 3, 4, 5},
            'ctx': {'field_type': 'Set', 'min_length': 7, 'actual_length': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=set(range(12)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('v',),
            'msg': 'Set should have at most 11 items after validation, not more',
            'input': {0, 8, 1, 9, 2, 10, 3, 7, 11, 4, 6, 5},
            'ctx': {'field_type': 'Set', 'max_length': 11, 'actual_length': None},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'set_type', 'loc': ('v',), 'msg': 'Input should be a valid set', 'input': 1}
    ]


def test_constrained_set_item_type_fails():
    class ConSetModel(BaseModel):
        v: conset(int) = []

    with pytest.raises(ValidationError) as exc_info:
        ConSetModel(v=['a', 'b', 'c'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('v', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': ('v', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
        {
            'type': 'int_parsing',
            'loc': ('v', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'c',
        },
    ]


def test_conset():
    class Model(BaseModel):
        foo: Set[int] = Field(..., min_length=2, max_length=4)
        bar: conset(str, min_length=1, max_length=4) = None

    assert Model(foo=[1, 2], bar=['spoon']).model_dump() == {'foo': {1, 2}, 'bar': {'spoon'}}

    assert Model(foo=[1, 1, 1, 2, 2], bar=['spoon']).model_dump() == {'foo': {1, 2}, 'bar': {'spoon'}}

    with pytest.raises(ValidationError, match='Set should have at least 2 items after validation, not 1'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='Set should have at most 4 items after validation, not more'):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('foo', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
        {
            'type': 'int_parsing',
            'loc': ('foo', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'set_type', 'loc': ('foo',), 'msg': 'Input should be a valid set', 'input': 1}
    ]


def test_conset_not_required():
    class Model(BaseModel):
        foo: Optional[Set[int]] = None

    assert Model(foo=None).foo is None
    assert Model().foo is None


def test_confrozenset():
    class Model(BaseModel):
        foo: FrozenSet[int] = Field(..., min_length=2, max_length=4)
        bar: confrozenset(str, min_length=1, max_length=4) = None

    m = Model(foo=[1, 2], bar=['spoon'])
    assert m.model_dump() == {'foo': {1, 2}, 'bar': {'spoon'}}
    assert isinstance(m.foo, frozenset)
    assert isinstance(m.bar, frozenset)

    assert Model(foo=[1, 1, 1, 2, 2], bar=['spoon']).model_dump() == {'foo': {1, 2}, 'bar': {'spoon'}}

    with pytest.raises(ValidationError, match='Frozenset should have at least 2 items after validation, not 1'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='Frozenset should have at most 4 items after validation, not more'):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('foo', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
        {
            'type': 'int_parsing',
            'loc': ('foo', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_set_type', 'loc': ('foo',), 'msg': 'Input should be a valid frozenset', 'input': 1}
    ]


def test_confrozenset_not_required():
    class Model(BaseModel):
        foo: Optional[FrozenSet[int]] = None

    assert Model(foo=None).foo is None
    assert Model().foo is None


def test_constrained_frozenset_optional():
    class Model(BaseModel):
        req: Optional[confrozenset(str, min_length=1)]
        opt: Optional[confrozenset(str, min_length=1)] = None

    assert Model(req=None).model_dump() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).model_dump() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=frozenset(), opt=frozenset())
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('req',),
            'msg': 'Frozenset should have at least 1 item after validation, not 0',
            'input': frozenset(),
            'ctx': {'field_type': 'Frozenset', 'min_length': 1, 'actual_length': 0},
        },
        {
            'type': 'too_short',
            'loc': ('opt',),
            'msg': 'Frozenset should have at least 1 item after validation, not 0',
            'input': frozenset(),
            'ctx': {'field_type': 'Frozenset', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req={'a'}, opt={'a'}).model_dump() == {'req': {'a'}, 'opt': {'a'}}


@pytest.fixture(scope='session', name='ConStringModel')
def constring_model_fixture():
    class ConStringModel(BaseModel):
        v: constr(max_length=10) = 'foobar'

    return ConStringModel


def test_constrained_str_good(ConStringModel):
    m = ConStringModel(v='short')
    assert m.v == 'short'


def test_constrained_str_default(ConStringModel):
    m = ConStringModel()
    assert m.v == 'foobar'


@pytest.mark.parametrize(
    ('data', 'valid'),
    [('this is too long', False), ('⛄' * 11, False), ('not long90', True), ('⛄' * 10, True)],
)
def test_constrained_str_too_long(ConStringModel, data, valid):
    if valid:
        assert ConStringModel(v=data).model_dump() == {'v': data}
    else:
        with pytest.raises(ValidationError) as exc_info:
            ConStringModel(v=data)
        # insert_assert(exc_info.value.errors(include_url=False))
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'max_length': 10},
                'input': data,
                'loc': ('v',),
                'msg': 'String should have at most 10 characters',
                'type': 'string_too_long',
            }
        ]


@pytest.mark.parametrize(
    'to_upper, value, result',
    [
        (True, 'abcd', 'ABCD'),
        (False, 'aBcD', 'aBcD'),
    ],
)
def test_constrained_str_upper(to_upper, value, result):
    class Model(BaseModel):
        v: constr(to_upper=to_upper)

    m = Model(v=value)
    assert m.v == result


@pytest.mark.parametrize(
    'to_lower, value, result',
    [
        (True, 'ABCD', 'abcd'),
        (False, 'ABCD', 'ABCD'),
    ],
)
def test_constrained_str_lower(to_lower, value, result):
    class Model(BaseModel):
        v: constr(to_lower=to_lower)

    m = Model(v=value)
    assert m.v == result


def test_constrained_str_max_length_0():
    class Model(BaseModel):
        v: constr(max_length=0)

    m = Model(v='')
    assert m.v == ''
    with pytest.raises(ValidationError) as exc_info:
        Model(v='qwe')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': ('v',),
            'msg': 'String should have at most 0 characters',
            'input': 'qwe',
            'ctx': {'max_length': 0},
        }
    ]


@pytest.mark.parametrize(
    'annotation',
    [
        ImportString[Callable[[Any], Any]],
        Annotated[Callable[[Any], Any], ImportString],
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
            'msg': "Invalid python path: No module named 'os.missing'",
            'input': 'os.missing',
            'ctx': {'error': "No module named 'os.missing'"},
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
        ImportString[Annotated[float, annotated_types.Ge(3), annotated_types.Le(4)]],
        Annotated[float, annotated_types.Ge(3), annotated_types.Le(4), ImportString],
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
                    'ctx': {'error': "No module named 'collections.abc.def'"},
                    'input': 'collections.abc.def',
                    'loc': (),
                    'msg': "Invalid python path: No module named 'collections.abc.def'",
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


def test_decimal():
    class Model(BaseModel):
        v: Decimal

    m = Model(v='1.234')
    assert m.v == Decimal('1.234')
    assert isinstance(m.v, Decimal)
    assert m.model_dump() == {'v': Decimal('1.234')}


def test_decimal_allow_inf():
    class MyModel(BaseModel):
        value: Annotated[Decimal, AllowInfNan(True)]

    m = MyModel(value='inf')
    assert m.value == Decimal('inf')

    m = MyModel(value=Decimal('inf'))
    assert m.value == Decimal('inf')


def test_decimal_dont_allow_inf():
    class MyModel(BaseModel):
        value: Decimal

    with pytest.raises(ValidationError, match=r'Input should be a finite number \[type=finite_number'):
        MyModel(value='inf')
    with pytest.raises(ValidationError, match=r'Input should be a finite number \[type=finite_number'):
        MyModel(value=Decimal('inf'))


def test_decimal_strict():
    class Model(BaseModel):
        v: Decimal

        model_config = ConfigDict(strict=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=1.23)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': ('v',),
            'msg': 'Input should be an instance of Decimal',
            'input': 1.23,
            'ctx': {'class': 'Decimal'},
        }
    ]

    v = Decimal(1.23)
    assert Model(v=v).v == v
    assert Model(v=v).model_dump() == {'v': v}

    assert Model.model_validate_json('{"v": "1.23"}').v == Decimal('1.23')


def test_decimal_precision() -> None:
    ta = TypeAdapter(Decimal)

    num = f'{1234567890 * 100}.{1234567890 * 100}'

    expected = Decimal(num)
    assert ta.validate_python(num) == expected
    assert ta.validate_json(f'"{num}"') == expected


def test_strict_date():
    class Model(BaseModel):
        v: Annotated[date, Field(strict=True)]

    assert Model(v=date(2017, 5, 5)).v == date(2017, 5, 5)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=datetime(2017, 5, 5))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'date_type',
            'loc': ('v',),
            'msg': 'Input should be a valid date',
            'input': datetime(2017, 5, 5),
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='2017-05-05')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'date_type',
            'loc': ('v',),
            'msg': 'Input should be a valid date',
            'input': '2017-05-05',
        }
    ]


def test_strict_datetime():
    class Model(BaseModel):
        v: Annotated[datetime, Field(strict=True)]

    assert Model(v=datetime(2017, 5, 5, 10, 10, 10)).v == datetime(2017, 5, 5, 10, 10, 10)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=date(2017, 5, 5))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_type',
            'loc': ('v',),
            'msg': 'Input should be a valid datetime',
            'input': date(2017, 5, 5),
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='2017-05-05T10:10:10')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_type',
            'loc': ('v',),
            'msg': 'Input should be a valid datetime',
            'input': '2017-05-05T10:10:10',
        }
    ]


def test_strict_time():
    class Model(BaseModel):
        v: Annotated[time, Field(strict=True)]

    assert Model(v=time(10, 10, 10)).v == time(10, 10, 10)

    with pytest.raises(ValidationError) as exc_info:
        Model(v='10:10:10')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'time_type',
            'loc': ('v',),
            'msg': 'Input should be a valid time',
            'input': '10:10:10',
        }
    ]


def test_strict_timedelta():
    class Model(BaseModel):
        v: Annotated[timedelta, Field(strict=True)]

    assert Model(v=timedelta(days=1)).v == timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        Model(v='1 days')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'time_delta_type',
            'loc': ('v',),
            'msg': 'Input should be a valid timedelta',
            'input': '1 days',
        }
    ]


@pytest.fixture(scope='session', name='CheckModel')
def check_model_fixture():
    class CheckModel(BaseModel):
        bool_check: bool = True
        str_check: constr(strip_whitespace=True, max_length=10) = 's'
        bytes_check: bytes = b's'
        int_check: int = 1
        float_check: float = 1.0
        uuid_check: UUID = UUID('7bd00d58-6485-4ca6-b889-3da6d8df3ee4')
        decimal_check: condecimal(allow_inf_nan=False) = Decimal('42.24')
        date_check: date = date(2017, 5, 5)
        datetime_check: datetime = datetime(2017, 5, 5, 10, 10, 10)
        time_check: time = time(10, 10, 10)
        timedelta_check: timedelta = timedelta(days=1)
        list_check: List[str] = ['1', '2']
        tuple_check: Tuple[str, ...] = ('1', '2')
        set_check: Set[str] = {'1', '2'}
        frozenset_check: FrozenSet[str] = frozenset(['1', '2'])

    return CheckModel


class BoolCastable:
    def __bool__(self) -> bool:
        return True


@pytest.mark.parametrize(
    'field,value,result',
    [
        ('bool_check', True, True),
        ('bool_check', 1, True),
        ('bool_check', 1.0, True),
        ('bool_check', Decimal(1), True),
        ('bool_check', 'y', True),
        ('bool_check', 'Y', True),
        ('bool_check', 'yes', True),
        ('bool_check', 'Yes', True),
        ('bool_check', 'YES', True),
        ('bool_check', 'true', True),
        ('bool_check', 'True', True),
        ('bool_check', 'TRUE', True),
        ('bool_check', 'on', True),
        ('bool_check', 'On', True),
        ('bool_check', 'ON', True),
        ('bool_check', '1', True),
        ('bool_check', 't', True),
        ('bool_check', 'T', True),
        ('bool_check', b'TRUE', True),
        ('bool_check', False, False),
        ('bool_check', 0, False),
        ('bool_check', 0.0, False),
        ('bool_check', Decimal(0), False),
        ('bool_check', 'n', False),
        ('bool_check', 'N', False),
        ('bool_check', 'no', False),
        ('bool_check', 'No', False),
        ('bool_check', 'NO', False),
        ('bool_check', 'false', False),
        ('bool_check', 'False', False),
        ('bool_check', 'FALSE', False),
        ('bool_check', 'off', False),
        ('bool_check', 'Off', False),
        ('bool_check', 'OFF', False),
        ('bool_check', '0', False),
        ('bool_check', 'f', False),
        ('bool_check', 'F', False),
        ('bool_check', b'FALSE', False),
        ('bool_check', None, ValidationError),
        ('bool_check', '', ValidationError),
        ('bool_check', [], ValidationError),
        ('bool_check', {}, ValidationError),
        ('bool_check', [1, 2, 3, 4], ValidationError),
        ('bool_check', {1: 2, 3: 4}, ValidationError),
        ('bool_check', b'2', ValidationError),
        ('bool_check', '2', ValidationError),
        ('bool_check', 2, ValidationError),
        ('bool_check', 2.0, ValidationError),
        ('bool_check', Decimal(2), ValidationError),
        ('bool_check', b'\x81', ValidationError),
        ('bool_check', BoolCastable(), ValidationError),
        ('str_check', 's', 's'),
        ('str_check', '  s  ', 's'),
        ('str_check', ' leading', 'leading'),
        ('str_check', 'trailing ', 'trailing'),
        ('str_check', b's', 's'),
        ('str_check', b'  s  ', 's'),
        ('str_check', bytearray(b's' * 5), 'sssss'),
        ('str_check', 1, ValidationError),
        ('str_check', 'x' * 11, ValidationError),
        ('str_check', b'x' * 11, ValidationError),
        ('str_check', b'\x81', ValidationError),
        ('str_check', bytearray(b'\x81' * 5), ValidationError),
        ('bytes_check', 's', b's'),
        ('bytes_check', '  s  ', b'  s  '),
        ('bytes_check', b's', b's'),
        ('bytes_check', 1, ValidationError),
        ('bytes_check', bytearray('xx', encoding='utf8'), b'xx'),
        ('bytes_check', True, ValidationError),
        ('bytes_check', False, ValidationError),
        ('bytes_check', {}, ValidationError),
        ('bytes_check', 'x' * 11, b'x' * 11),
        ('bytes_check', b'x' * 11, b'x' * 11),
        ('int_check', 1, 1),
        ('int_check', 1.0, 1),
        ('int_check', 1.9, ValidationError),
        ('int_check', Decimal(1), 1),
        ('int_check', Decimal(1.9), ValidationError),
        ('int_check', '1', 1),
        ('int_check', '1.9', ValidationError),
        ('int_check', b'1', 1),
        ('int_check', 12, 12),
        ('int_check', '12', 12),
        ('int_check', b'12', 12),
        ('float_check', 1, 1.0),
        ('float_check', 1.0, 1.0),
        ('float_check', Decimal(1.0), 1.0),
        ('float_check', '1.0', 1.0),
        ('float_check', '1', 1.0),
        ('float_check', b'1.0', 1.0),
        ('float_check', b'1', 1.0),
        ('float_check', True, 1.0),
        ('float_check', False, 0.0),
        ('float_check', 't', ValidationError),
        ('float_check', b't', ValidationError),
        ('uuid_check', 'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        ('uuid_check', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        ('uuid_check', b'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        ('uuid_check', b'\x12\x34\x56\x78' * 4, UUID('12345678-1234-5678-1234-567812345678')),
        ('uuid_check', 'ebcdab58-6eb8-46fb-a190-', ValidationError),
        ('uuid_check', 123, ValidationError),
        ('decimal_check', 42.24, Decimal('42.24')),
        ('decimal_check', '42.24', Decimal('42.24')),
        ('decimal_check', b'42.24', ValidationError),
        ('decimal_check', '  42.24  ', Decimal('42.24')),
        ('decimal_check', Decimal('42.24'), Decimal('42.24')),
        ('decimal_check', 'not a valid decimal', ValidationError),
        ('decimal_check', 'NaN', ValidationError),
        ('date_check', date(2017, 5, 5), date(2017, 5, 5)),
        ('date_check', datetime(2017, 5, 5), date(2017, 5, 5)),
        ('date_check', '2017-05-05', date(2017, 5, 5)),
        ('date_check', b'2017-05-05', date(2017, 5, 5)),
        ('date_check', 1493942400000, date(2017, 5, 5)),
        ('date_check', 1493942400, date(2017, 5, 5)),
        ('date_check', 1493942400000.0, date(2017, 5, 5)),
        ('date_check', Decimal(1493942400000), date(2017, 5, 5)),
        ('date_check', datetime(2017, 5, 5, 10), ValidationError),
        ('date_check', '2017-5-5', ValidationError),
        ('date_check', b'2017-5-5', ValidationError),
        ('date_check', 1493942401000, ValidationError),
        ('date_check', 1493942401000.0, ValidationError),
        ('date_check', Decimal(1493942401000), ValidationError),
        ('datetime_check', datetime(2017, 5, 5, 10, 10, 10), datetime(2017, 5, 5, 10, 10, 10)),
        ('datetime_check', date(2017, 5, 5), datetime(2017, 5, 5, 0, 0, 0)),
        ('datetime_check', '2017-05-05T10:10:10.0002', datetime(2017, 5, 5, 10, 10, 10, microsecond=200)),
        ('datetime_check', '2017-05-05 10:10:10', datetime(2017, 5, 5, 10, 10, 10)),
        ('datetime_check', '2017-05-05 10:10:10+00:00', datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        ('datetime_check', b'2017-05-05T10:10:10.0002', datetime(2017, 5, 5, 10, 10, 10, microsecond=200)),
        ('datetime_check', 1493979010000, datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        ('datetime_check', 1493979010, datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        ('datetime_check', 1493979010000.0, datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        ('datetime_check', Decimal(1493979010), datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        ('datetime_check', '2017-5-5T10:10:10', ValidationError),
        ('datetime_check', b'2017-5-5T10:10:10', ValidationError),
        ('time_check', time(10, 10, 10), time(10, 10, 10)),
        ('time_check', '10:10:10.0002', time(10, 10, 10, microsecond=200)),
        ('time_check', b'10:10:10.0002', time(10, 10, 10, microsecond=200)),
        ('time_check', 3720, time(1, 2, tzinfo=timezone.utc)),
        ('time_check', 3720.0002, time(1, 2, microsecond=200, tzinfo=timezone.utc)),
        ('time_check', Decimal(3720.0002), time(1, 2, microsecond=200, tzinfo=timezone.utc)),
        ('time_check', '1:1:1', ValidationError),
        ('time_check', b'1:1:1', ValidationError),
        ('time_check', -1, ValidationError),
        ('time_check', 86400, ValidationError),
        ('time_check', 86400.0, ValidationError),
        ('time_check', Decimal(86400), ValidationError),
        ('timedelta_check', timedelta(days=1), timedelta(days=1)),
        ('timedelta_check', '1 days 10:10', timedelta(days=1, seconds=36600)),
        ('timedelta_check', '1 d 10:10', timedelta(days=1, seconds=36600)),
        ('timedelta_check', b'1 days 10:10', timedelta(days=1, seconds=36600)),
        ('timedelta_check', 123_000, timedelta(days=1, seconds=36600)),
        ('timedelta_check', 123_000.0002, timedelta(days=1, seconds=36600, microseconds=200)),
        ('timedelta_check', Decimal(123_000.0002), timedelta(days=1, seconds=36600, microseconds=200)),
        ('timedelta_check', '1 10:10', ValidationError),
        ('timedelta_check', b'1 10:10', ValidationError),
        ('list_check', ['1', '2'], ['1', '2']),
        ('list_check', ('1', '2'), ['1', '2']),
        ('list_check', {'1': 1, '2': 2}.keys(), ['1', '2']),
        ('list_check', {'1': '1', '2': '2'}.values(), ['1', '2']),
        ('list_check', {'1', '2'}, dirty_equals.IsOneOf(['1', '2'], ['2', '1'])),
        ('list_check', frozenset(['1', '2']), dirty_equals.IsOneOf(['1', '2'], ['2', '1'])),
        ('list_check', {'1': 1, '2': 2}, ValidationError),
        ('tuple_check', ('1', '2'), ('1', '2')),
        ('tuple_check', ['1', '2'], ('1', '2')),
        ('tuple_check', {'1': 1, '2': 2}.keys(), ('1', '2')),
        ('tuple_check', {'1': '1', '2': '2'}.values(), ('1', '2')),
        ('tuple_check', {'1', '2'}, dirty_equals.IsOneOf(('1', '2'), ('2', '1'))),
        ('tuple_check', frozenset(['1', '2']), dirty_equals.IsOneOf(('1', '2'), ('2', '1'))),
        ('tuple_check', {'1': 1, '2': 2}, ValidationError),
        ('set_check', {'1', '2'}, {'1', '2'}),
        ('set_check', ['1', '2', '1', '2'], {'1', '2'}),
        ('set_check', ('1', '2', '1', '2'), {'1', '2'}),
        ('set_check', frozenset(['1', '2']), {'1', '2'}),
        ('set_check', {'1': 1, '2': 2}.keys(), {'1', '2'}),
        ('set_check', {'1': '1', '2': '2'}.values(), {'1', '2'}),
        ('set_check', {'1': 1, '2': 2}, ValidationError),
        ('frozenset_check', frozenset(['1', '2']), frozenset(['1', '2'])),
        ('frozenset_check', ['1', '2', '1', '2'], frozenset(['1', '2'])),
        ('frozenset_check', ('1', '2', '1', '2'), frozenset(['1', '2'])),
        ('frozenset_check', {'1', '2'}, frozenset(['1', '2'])),
        ('frozenset_check', {'1': 1, '2': 2}.keys(), frozenset(['1', '2'])),
        ('frozenset_check', {'1': '1', '2': '2'}.values(), frozenset(['1', '2'])),
        ('frozenset_check', {'1': 1, '2': 2}, ValidationError),
    ],
)
def test_default_validators(field, value, result, CheckModel):
    kwargs = {field: value}
    if result == ValidationError:
        with pytest.raises(ValidationError):
            CheckModel(**kwargs)
    else:
        assert CheckModel(**kwargs).model_dump()[field] == result


@pytest.fixture(scope='session', name='StrModel')
def str_model_fixture():
    class StrModel(BaseModel):
        str_check: Annotated[str, annotated_types.Len(5, 10)]

    return StrModel


def test_string_too_long(StrModel):
    with pytest.raises(ValidationError) as exc_info:
        StrModel(str_check='x' * 150)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': ('str_check',),
            'msg': 'String should have at most 10 characters',
            'input': 'x' * 150,
            'ctx': {'max_length': 10},
        }
    ]


def test_string_too_short(StrModel):
    with pytest.raises(ValidationError) as exc_info:
        StrModel(str_check='x')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_short',
            'loc': ('str_check',),
            'msg': 'String should have at least 5 characters',
            'input': 'x',
            'ctx': {'min_length': 5},
        }
    ]


@pytest.fixture(scope='session', name='DatetimeModel')
def datetime_model_fixture():
    class DatetimeModel(BaseModel):
        dt: datetime
        date_: date
        time_: time
        duration: timedelta

    return DatetimeModel


def test_datetime_successful(DatetimeModel):
    m = DatetimeModel(dt='2017-10-05T19:47:07', date_=1493942400, time_='10:20:30.400', duration='00:15:30.0001')
    assert m.dt == datetime(2017, 10, 5, 19, 47, 7)
    assert m.date_ == date(2017, 5, 5)
    assert m.time_ == time(10, 20, 30, 400_000)
    assert m.duration == timedelta(minutes=15, seconds=30, microseconds=100)


def test_datetime_errors(DatetimeModel):
    with pytest.raises(ValueError) as exc_info:
        DatetimeModel(dt='2017-13-05T19:47:07', date_='XX1494012000', time_='25:20:30.400', duration='15:30.0001broken')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_from_date_parsing',
            'loc': ('dt',),
            'msg': 'Input should be a valid datetime or date, month value is outside expected range of 1-12',
            'input': '2017-13-05T19:47:07',
            'ctx': {'error': 'month value is outside expected range of 1-12'},
        },
        {
            'type': 'date_from_datetime_parsing',
            'loc': ('date_',),
            'msg': 'Input should be a valid date or datetime, invalid character in year',
            'input': 'XX1494012000',
            'ctx': {'error': 'invalid character in year'},
        },
        {
            'type': 'time_parsing',
            'loc': ('time_',),
            'msg': 'Input should be in a valid time format, hour value is outside expected range of 0-23',
            'input': '25:20:30.400',
            'ctx': {'error': 'hour value is outside expected range of 0-23'},
        },
        {
            'type': 'time_delta_parsing',
            'loc': ('duration',),
            'msg': 'Input should be a valid timedelta, unexpected extra characters at the end of the input',
            'input': '15:30.0001broken',
            'ctx': {'error': 'unexpected extra characters at the end of the input'},
        },
    ]


@pytest.fixture(scope='session')
def cooking_model():
    class FruitEnum(str, Enum):
        pear = 'pear'
        banana = 'banana'

    class ToolEnum(IntEnum):
        spanner = 1
        wrench = 2

    class CookingModel(BaseModel):
        fruit: FruitEnum = FruitEnum.pear
        tool: ToolEnum = ToolEnum.spanner

    return FruitEnum, ToolEnum, CookingModel


def test_enum_successful(cooking_model):
    FruitEnum, ToolEnum, CookingModel = cooking_model
    m = CookingModel(tool=2)
    assert m.fruit == FruitEnum.pear
    assert m.tool == ToolEnum.wrench
    assert repr(m.tool) == '<ToolEnum.wrench: 2>'


def test_enum_fails(cooking_model):
    FruitEnum, ToolEnum, CookingModel = cooking_model
    with pytest.raises(ValueError) as exc_info:
        CookingModel(tool=3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'expected': '1 or 2'},
            'input': 3,
            'loc': ('tool',),
            'msg': 'Input should be 1 or 2',
            'type': 'enum',
        }
    ]


def test_enum_fails_error_msg():
    class Number(IntEnum):
        one = 1
        two = 2
        three = 3

    class Model(BaseModel):
        num: Number

    with pytest.raises(ValueError) as exc_info:
        Model(num=4)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'enum',
            'loc': ('num',),
            'msg': 'Input should be 1, 2 or 3',
            'input': 4,
            'ctx': {'expected': '1, 2 or 3'},
        }
    ]


def test_int_enum_successful_for_str_int(cooking_model):
    FruitEnum, ToolEnum, CookingModel = cooking_model
    m = CookingModel(tool='2')
    assert m.tool == ToolEnum.wrench
    assert repr(m.tool) == '<ToolEnum.wrench: 2>'


def test_plain_enum_validate():
    class MyEnum(Enum):
        a = 1

    class Model(BaseModel):
        x: MyEnum

    m = Model(x=MyEnum.a)
    assert m.x is MyEnum.a

    assert TypeAdapter(MyEnum).validate_python(1) is MyEnum.a
    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(MyEnum).validate_python(1, strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'test_plain_enum_validate.<locals>.MyEnum'},
            'input': 1,
            'loc': (),
            'msg': IsStr(regex='Input should be an instance of test_plain_enum_validate.<locals>.MyEnum'),
            'type': 'is_instance_of',
        }
    ]

    assert TypeAdapter(MyEnum).validate_json('1') is MyEnum.a
    TypeAdapter(MyEnum).validate_json('1', strict=True)
    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(MyEnum).validate_json('"1"', strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'ctx': {'expected': '1'}, 'input': '1', 'loc': (), 'msg': 'Input should be 1', 'type': 'enum'}
    ]


def test_plain_enum_validate_json():
    class MyEnum(Enum):
        a = 1

    class Model(BaseModel):
        x: MyEnum

    m = Model.model_validate_json('{"x":1}')
    assert m.x is MyEnum.a


def test_enum_type():
    class Model(BaseModel):
        my_enum: Enum

    class MyEnum(Enum):
        a = 1

    m = Model(my_enum=MyEnum.a)
    assert m.my_enum == MyEnum.a
    assert m.model_dump() == {'my_enum': MyEnum.a}
    assert m.model_dump_json() == '{"my_enum":1}'

    with pytest.raises(ValidationError) as exc_info:
        Model(my_enum=1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'Enum'},
            'input': 1,
            'loc': ('my_enum',),
            'msg': 'Input should be an instance of Enum',
            'type': 'is_instance_of',
        }
    ]


def test_enum_missing_default():
    class MyEnum(Enum):
        a = 1

    ta = TypeAdapter(MyEnum)
    missing_value = re.search(r'missing: (\w+)', repr(ta.validator)).group(1)
    assert missing_value == 'None'

    assert ta.validate_python(1) is MyEnum.a
    with pytest.raises(ValidationError):
        ta.validate_python(2)


def test_enum_missing_custom():
    class MyEnum(Enum):
        a = 1

        @classmethod
        def _missing_(cls, value):
            return MyEnum.a

    ta = TypeAdapter(MyEnum)
    missing_value = re.search(r'missing: (\w+)', repr(ta.validator)).group(1)
    assert missing_value == 'Some'

    assert ta.validate_python(1) is MyEnum.a
    assert ta.validate_python(2) is MyEnum.a


def test_int_enum_type():
    class Model(BaseModel):
        my_enum: IntEnum

    class MyEnum(Enum):
        a = 1

    class MyIntEnum(IntEnum):
        b = 2

    m = Model(my_enum=MyIntEnum.b)
    assert m.my_enum == MyIntEnum.b
    assert m.model_dump() == {'my_enum': MyIntEnum.b}
    assert m.model_dump_json() == '{"my_enum":2}'

    with pytest.raises(ValidationError) as exc_info:
        Model(my_enum=MyEnum.a)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'IntEnum'},
            'input': MyEnum.a,
            'loc': ('my_enum',),
            'msg': 'Input should be an instance of IntEnum',
            'type': 'is_instance_of',
        }
    ]


@pytest.mark.parametrize('enum_base,strict', [(Enum, False), (IntEnum, False), (IntEnum, True)])
def test_enum_from_json(enum_base, strict):
    class MyEnum(enum_base):
        a = 1
        b = 3

    class Model(BaseModel):
        my_enum: MyEnum

    m = Model.model_validate_json('{"my_enum":1}', strict=strict)
    assert m.my_enum is MyEnum.a

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate_json('{"my_enum":2}', strict=strict)

    MyEnum.__name__ if sys.version_info[:2] <= (3, 8) else MyEnum.__qualname__

    if strict:
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'expected': '1 or 3'},
                'input': 2,
                'loc': ('my_enum',),
                'msg': 'Input should be 1 or 3',
                'type': 'enum',
            }
        ]
    else:
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'expected': '1 or 3'},
                'input': 2,
                'loc': ('my_enum',),
                'msg': 'Input should be 1 or 3',
                'type': 'enum',
            }
        ]


def test_strict_enum() -> None:
    class Demo(Enum):
        A = 0
        B = 1

    class User(BaseModel):
        model_config = ConfigDict(strict=True)

        demo_strict: Demo
        demo_not_strict: Demo = Field(strict=False)

    user = User(demo_strict=Demo.A, demo_not_strict=1)

    assert isinstance(user.demo_strict, Demo)
    assert isinstance(user.demo_not_strict, Demo)
    assert user.demo_strict.value == 0
    assert user.demo_not_strict.value == 1

    with pytest.raises(ValidationError, match='Input should be an instance of test_strict_enum.<locals>.Demo'):
        User(demo_strict=0, demo_not_strict=1)


def test_enum_with_no_cases() -> None:
    class MyEnum(Enum):
        pass

    class MyModel(BaseModel):
        e: MyEnum

    json_schema = MyModel.model_json_schema()
    assert json_schema['properties']['e']['enum'] == []


@pytest.mark.parametrize(
    'kwargs,type_',
    [
        pytest.param(
            {'pattern': '^foo$'},
            int,
            marks=pytest.mark.xfail(
                reason='int cannot be used with pattern but we do not currently validate that at schema build time'
            ),
        ),
        ({'gt': 0}, conlist(int, min_length=4)),
        ({'gt': 0}, conset(int, min_length=4)),
        ({'gt': 0}, confrozenset(int, min_length=4)),
    ],
)
def test_invalid_schema_constraints(kwargs, type_):
    match = (
        r'(:?Invalid Schema:\n.*\n  Extra inputs are not permitted)|(:?The following constraints cannot be applied to)'
    )
    with pytest.raises((SchemaError, TypeError), match=match):

        class Foo(BaseModel):
            a: type_ = Field('foo', title='A title', description='A description', **kwargs)


def test_invalid_decimal_constraint():
    with pytest.raises(
        TypeError, match="The following constraints cannot be applied to <class 'decimal.Decimal'>: 'max_length'"
    ):

        class Foo(BaseModel):
            a: Decimal = Field('foo', title='A title', description='A description', max_length=5)


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


def test_dict():
    class Model(BaseModel):
        v: dict

    assert Model(v={1: 10, 2: 20}).v == {1: 10, 2: 20}
    with pytest.raises(ValidationError) as exc_info:
        Model(v=[(1, 2), (3, 4)])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dict_type',
            'loc': ('v',),
            'msg': 'Input should be a valid dictionary',
            'input': [(1, 2), (3, 4)],
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'dict_type', 'loc': ('v',), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]


@pytest.mark.parametrize(
    'value,result',
    (
        ([1, 2, '3'], [1, 2, '3']),
        ((1, 2, '3'), [1, 2, '3']),
        ((i**2 for i in range(5)), [0, 1, 4, 9, 16]),
        (deque([1, 2, 3]), [1, 2, 3]),
        ({1, '2'}, IsOneOf([1, '2'], ['2', 1])),
    ),
)
def test_list_success(value, result):
    class Model(BaseModel):
        v: list

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (123, '123'))
def test_list_fails(value):
    class Model(BaseModel):
        v: list

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': ('v',),
            'msg': 'Input should be a valid list',
            'input': value,
        }
    ]


def test_ordered_dict():
    class Model(BaseModel):
        v: OrderedDict

    assert Model(v=OrderedDict([(1, 10), (2, 20)])).v == OrderedDict([(1, 10), (2, 20)])
    assert Model(v={1: 10, 2: 20}).v == OrderedDict([(1, 10), (2, 20)])

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'dict_type', 'loc': ('v',), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]


@pytest.mark.parametrize(
    'value,result',
    (
        ([1, 2, '3'], (1, 2, '3')),
        ((1, 2, '3'), (1, 2, '3')),
        ((i**2 for i in range(5)), (0, 1, 4, 9, 16)),
        (deque([1, 2, 3]), (1, 2, 3)),
        ({1, '2'}, IsOneOf((1, '2'), ('2', 1))),
    ),
)
def test_tuple_success(value, result):
    class Model(BaseModel):
        v: tuple

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (123, '123'))
def test_tuple_fails(value):
    class Model(BaseModel):
        v: tuple

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'tuple_type', 'loc': ('v',), 'msg': 'Input should be a valid tuple', 'input': value}
    ]


@pytest.mark.parametrize(
    'value,cls,result',
    (
        ([1, 2, '3'], int, (1, 2, 3)),
        ((1, 2, '3'), int, (1, 2, 3)),
        ((i**2 for i in range(5)), int, (0, 1, 4, 9, 16)),
        (('a', 'b', 'c'), str, ('a', 'b', 'c')),
    ),
)
def test_tuple_variable_len_success(value, cls, result):
    class Model(BaseModel):
        v: Tuple[cls, ...]

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'value, cls, exc',
    [
        (
            ('a', 'b', [1, 2], 'c'),
            str,
            [
                {
                    'type': 'string_type',
                    'loc': ('v', 2),
                    'msg': 'Input should be a valid string',
                    'input': [1, 2],
                }
            ],
        ),
        (
            ('a', 'b', [1, 2], 'c', [3, 4]),
            str,
            [
                {
                    'type': 'string_type',
                    'loc': ('v', 2),
                    'msg': 'Input should be a valid string',
                    'input': [1, 2],
                },
                {
                    'type': 'string_type',
                    'loc': ('v', 4),
                    'msg': 'Input should be a valid string',
                    'input': [3, 4],
                },
            ],
        ),
    ],
)
def test_tuple_variable_len_fails(value, cls, exc):
    class Model(BaseModel):
        v: Tuple[cls, ...]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors(include_url=False) == exc


@pytest.mark.parametrize(
    'value,result',
    (
        ({1, 2, 2, '3'}, {1, 2, '3'}),
        ((1, 2, 2, '3'), {1, 2, '3'}),
        ([1, 2, 2, '3'], {1, 2, '3'}),
        ({i**2 for i in range(5)}, {0, 1, 4, 9, 16}),
    ),
)
def test_set_success(value, result):
    class Model(BaseModel):
        v: set

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (123, '123'))
def test_set_fails(value):
    class Model(BaseModel):
        v: set

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'set_type', 'loc': ('v',), 'msg': 'Input should be a valid set', 'input': value}
    ]


def test_list_type_fails():
    class Model(BaseModel):
        v: List[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': ('v',), 'msg': 'Input should be a valid list', 'input': '123'}
    ]


def test_set_type_fails():
    class Model(BaseModel):
        v: Set[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'set_type', 'loc': ('v',), 'msg': 'Input should be a valid set', 'input': '123'}
    ]


@pytest.mark.parametrize(
    'cls, value,result',
    (
        (int, [1, 2, 3], [1, 2, 3]),
        (int, (1, 2, 3), (1, 2, 3)),
        (int, range(5), [0, 1, 2, 3, 4]),
        (int, deque((1, 2, 3)), deque((1, 2, 3))),
        (Set[int], [{1, 2}, {3, 4}, {5, 6}], [{1, 2}, {3, 4}, {5, 6}]),
        (Tuple[int, str], ((1, 'a'), (2, 'b'), (3, 'c')), ((1, 'a'), (2, 'b'), (3, 'c'))),
    ),
)
def test_sequence_success(cls, value, result):
    class Model(BaseModel):
        v: Sequence[cls]

    assert Model(v=value).v == result


def int_iterable():
    i = 0
    while True:
        i += 1
        yield str(i)


def str_iterable():
    while True:
        yield from 'foobarbaz'


def test_infinite_iterable_int():
    class Model(BaseModel):
        it: Iterable[int]

    m = Model(it=int_iterable())

    assert repr(m.it) == 'ValidatorIterator(index=0, schema=Some(Int(IntValidator { strict: false })))'

    output = []
    for i in m.it:
        output.append(i)
        if i == 10:
            break

    assert output == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    m = Model(it=[1, 2, 3])
    assert list(m.it) == [1, 2, 3]

    m = Model(it=str_iterable())
    with pytest.raises(ValidationError) as exc_info:
        next(m.it)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'f',
        }
    ]


@pytest.mark.parametrize('type_annotation', (Iterable[Any], Iterable))
def test_iterable_any(type_annotation):
    class Model(BaseModel):
        it: type_annotation

    m = Model(it=int_iterable())

    output = []
    for i in m.it:
        output.append(i)
        if int(i) == 10:
            break

    assert output == ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

    m = Model(it=[1, '2', b'three'])
    assert list(m.it) == [1, '2', b'three']

    with pytest.raises(ValidationError) as exc_info:
        Model(it=3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'iterable_type', 'loc': ('it',), 'msg': 'Input should be iterable', 'input': 3}
    ]


def test_invalid_iterable():
    class Model(BaseModel):
        it: Iterable[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(it=3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'iterable_type', 'loc': ('it',), 'msg': 'Input should be iterable', 'input': 3}
    ]


@pytest.mark.parametrize(
    'config,input_str',
    (
        ({}, 'type=iterable_type, input_value=5, input_type=int'),
        ({'hide_input_in_errors': False}, 'type=iterable_type, input_value=5, input_type=int'),
        ({'hide_input_in_errors': True}, 'type=iterable_type'),
    ),
)
def test_iterable_error_hide_input(config, input_str):
    class Model(BaseModel):
        it: Iterable[int]

        model_config = ConfigDict(**config)

    with pytest.raises(ValidationError, match=re.escape(f'Input should be iterable [{input_str}]')):
        Model(it=5)


def test_infinite_iterable_validate_first():
    class Model(BaseModel):
        it: Iterable[int]
        b: int

        @field_validator('it')
        @classmethod
        def infinite_first_int(cls, it):
            return itertools.chain([next(it)], it)

    m = Model(it=int_iterable(), b=3)

    assert m.b == 3
    assert m.it

    for i in m.it:
        assert i
        if i == 10:
            break

    with pytest.raises(ValidationError) as exc_info:
        Model(it=str_iterable(), b=3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('it', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'f',
        }
    ]


def test_sequence_generator_fails():
    class Model(BaseModel):
        v: Sequence[int]

    gen = (i for i in [1, 2, 3])
    with pytest.raises(ValidationError) as exc_info:
        Model(v=gen)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': ('v',),
            'msg': 'Input should be an instance of Sequence',
            'input': gen,
            'ctx': {'class': 'Sequence'},
        }
    ]


@pytest.mark.parametrize(
    'cls,value,errors',
    (
        (
            int,
            [1, 'a', 3],
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 1),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'a',
                },
            ],
        ),
        (
            int,
            (1, 2, 'a'),
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 2),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'a',
                },
            ],
        ),
        (
            float,
            ('a', 2.2, 3.3),
            [
                {
                    'type': 'float_parsing',
                    'loc': ('v', 0),
                    'msg': 'Input should be a valid number, unable to parse string as a number',
                    'input': 'a',
                },
            ],
        ),
        (
            float,
            (1.1, 2.2, 'a'),
            [
                {
                    'type': 'float_parsing',
                    'loc': ('v', 2),
                    'msg': 'Input should be a valid number, unable to parse string as a number',
                    'input': 'a',
                },
            ],
        ),
        (
            float,
            {1.0, 2.0, 3.0},
            [
                {
                    'type': 'is_instance_of',
                    'loc': ('v',),
                    'msg': 'Input should be an instance of Sequence',
                    'input': {
                        1.0,
                        2.0,
                        3.0,
                    },
                    'ctx': {
                        'class': 'Sequence',
                    },
                },
            ],
        ),
        (
            Set[int],
            [{1, 2}, {2, 3}, {'d'}],
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 2, 0),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'd',
                }
            ],
        ),
        (
            Tuple[int, str],
            ((1, 'a'), ('a', 'a'), (3, 'c')),
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 1, 0),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'a',
                }
            ],
        ),
        (
            List[int],
            [{'a': 1, 'b': 2}, [1, 2], [2, 3]],
            [
                {
                    'type': 'list_type',
                    'loc': ('v', 0),
                    'msg': 'Input should be a valid list',
                    'input': {'a': 1, 'b': 2},
                }
            ],
        ),
    ),
    ids=repr,
)
def test_sequence_fails(cls, value, errors):
    class Model(BaseModel):
        v: Sequence[cls]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors(include_url=False) == errors


def test_sequence_strict():
    assert TypeAdapter(Sequence[int]).validate_python((), strict=True) == ()


def test_list_strict() -> None:
    class LaxModel(BaseModel):
        v: List[int]

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        v: List[int]

        model_config = ConfigDict(strict=True)

    assert LaxModel(v=(1, 2)).v == [1, 2]
    assert LaxModel(v=('1', 2)).v == [1, 2]
    # Tuple should be rejected
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=(1, 2))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': ('v',), 'msg': 'Input should be a valid list', 'input': (1, 2)}
    ]
    # Strict in each list item
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=['1', 2])
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('v', 0), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


def test_set_strict() -> None:
    class LaxModel(BaseModel):
        v: Set[int]

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        v: Set[int]

        model_config = ConfigDict(strict=True)

    assert LaxModel(v=(1, 2)).v == {1, 2}
    assert LaxModel(v=('1', 2)).v == {1, 2}
    # Tuple should be rejected
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=(1, 2))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'set_type',
            'loc': ('v',),
            'msg': 'Input should be a valid set',
            'input': (1, 2),
        }
    ]
    # Strict in each set item
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v={'1', 2})
    err_info = exc_info.value.errors(include_url=False)
    # Sets are not ordered
    del err_info[0]['loc']
    assert err_info == [{'type': 'int_type', 'msg': 'Input should be a valid integer', 'input': '1'}]


def test_frozenset_strict() -> None:
    class LaxModel(BaseModel):
        v: FrozenSet[int]

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        v: FrozenSet[int]

        model_config = ConfigDict(strict=True)

    assert LaxModel(v=(1, 2)).v == frozenset((1, 2))
    assert LaxModel(v=('1', 2)).v == frozenset((1, 2))
    # Tuple should be rejected
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=(1, 2))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'frozen_set_type',
            'loc': ('v',),
            'msg': 'Input should be a valid frozenset',
            'input': (1, 2),
        }
    ]
    # Strict in each set item
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=frozenset(('1', 2)))
    err_info = exc_info.value.errors(include_url=False)
    # Sets are not ordered
    del err_info[0]['loc']
    assert err_info == [{'type': 'int_type', 'msg': 'Input should be a valid integer', 'input': '1'}]


def test_tuple_strict() -> None:
    class LaxModel(BaseModel):
        v: Tuple[int, int]

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        v: Tuple[int, int]

        model_config = ConfigDict(strict=True)

    assert LaxModel(v=[1, 2]).v == (1, 2)
    assert LaxModel(v=['1', 2]).v == (1, 2)
    # List should be rejected
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=[1, 2])
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'tuple_type', 'loc': ('v',), 'msg': 'Input should be a valid tuple', 'input': [1, 2]}
    ]
    # Strict in each list item
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=('1', 2))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('v', 0), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


def test_int_validation():
    class Model(BaseModel):
        a: PositiveInt = None
        b: NegativeInt = None
        c: NonNegativeInt = None
        d: NonPositiveInt = None
        e: conint(gt=4, lt=10) = None
        f: conint(ge=0, le=10) = None
        g: conint(multiple_of=5) = None

    m = Model(a=5, b=-5, c=0, d=0, e=5, f=0, g=25)
    assert m.model_dump() == {'a': 5, 'b': -5, 'c': 0, 'd': 0, 'e': 5, 'f': 0, 'g': 25}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-5, b=5, c=-5, d=5, e=-5, f=11, g=42)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('a',),
            'msg': 'Input should be greater than 0',
            'input': -5,
            'ctx': {'gt': 0},
        },
        {
            'type': 'less_than',
            'loc': ('b',),
            'msg': 'Input should be less than 0',
            'input': 5,
            'ctx': {'lt': 0},
        },
        {
            'type': 'greater_than_equal',
            'loc': ('c',),
            'msg': 'Input should be greater than or equal to 0',
            'input': -5,
            'ctx': {'ge': 0},
        },
        {
            'type': 'less_than_equal',
            'loc': ('d',),
            'msg': 'Input should be less than or equal to 0',
            'input': 5,
            'ctx': {'le': 0},
        },
        {
            'type': 'greater_than',
            'loc': ('e',),
            'msg': 'Input should be greater than 4',
            'input': -5,
            'ctx': {'gt': 4},
        },
        {
            'type': 'less_than_equal',
            'loc': ('f',),
            'msg': 'Input should be less than or equal to 10',
            'input': 11,
            'ctx': {'le': 10},
        },
        {
            'type': 'multiple_of',
            'loc': ('g',),
            'msg': 'Input should be a multiple of 5',
            'input': 42,
            'ctx': {'multiple_of': 5},
        },
    ]


def test_float_validation():
    class Model(BaseModel):
        a: PositiveFloat = None
        b: NegativeFloat = None
        c: NonNegativeFloat = None
        d: NonPositiveFloat = None
        e: confloat(gt=4, lt=12.2) = None
        f: confloat(ge=0, le=9.9) = None
        g: confloat(multiple_of=0.5) = None
        h: confloat(allow_inf_nan=False) = None

    m = Model(a=5.1, b=-5.2, c=0, d=0, e=5.3, f=9.9, g=2.5, h=42)
    assert m.model_dump() == {'a': 5.1, 'b': -5.2, 'c': 0, 'd': 0, 'e': 5.3, 'f': 9.9, 'g': 2.5, 'h': 42}

    assert Model(a=float('inf')).a == float('inf')
    assert Model(b=float('-inf')).b == float('-inf')

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-5.1, b=5.2, c=-5.1, d=5.1, e=-5.3, f=9.91, g=4.2, h=float('nan'))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('a',),
            'msg': 'Input should be greater than 0',
            'input': -5.1,
            'ctx': {
                'gt': 0.0,
            },
        },
        {
            'type': 'less_than',
            'loc': ('b',),
            'msg': 'Input should be less than 0',
            'input': 5.2,
            'ctx': {
                'lt': 0.0,
            },
        },
        {
            'type': 'greater_than_equal',
            'loc': ('c',),
            'msg': 'Input should be greater than or equal to 0',
            'input': -5.1,
            'ctx': {
                'ge': 0.0,
            },
        },
        {
            'type': 'less_than_equal',
            'loc': ('d',),
            'msg': 'Input should be less than or equal to 0',
            'input': 5.1,
            'ctx': {
                'le': 0.0,
            },
        },
        {
            'type': 'greater_than',
            'loc': ('e',),
            'msg': 'Input should be greater than 4',
            'input': -5.3,
            'ctx': {
                'gt': 4.0,
            },
        },
        {
            'type': 'less_than_equal',
            'loc': ('f',),
            'msg': 'Input should be less than or equal to 9.9',
            'input': 9.91,
            'ctx': {
                'le': 9.9,
            },
        },
        {
            'type': 'multiple_of',
            'loc': ('g',),
            'msg': 'Input should be a multiple of 0.5',
            'input': 4.2,
            'ctx': {
                'multiple_of': 0.5,
            },
        },
        {
            'type': 'finite_number',
            'loc': ('h',),
            'msg': 'Input should be a finite number',
            'input': HasRepr('nan'),
        },
    ]


def test_infinite_float_validation():
    class Model(BaseModel):
        a: float = None

    assert Model(a=float('inf')).a == float('inf')
    assert Model(a=float('-inf')).a == float('-inf')
    assert math.isnan(Model(a=float('nan')).a)


@pytest.mark.parametrize(
    ('ser_json_inf_nan', 'input', 'output', 'python_roundtrip'),
    (
        ('null', float('inf'), 'null', None),
        ('null', float('-inf'), 'null', None),
        ('null', float('nan'), 'null', None),
        ('constants', float('inf'), 'Infinity', float('inf')),
        ('constants', float('-inf'), '-Infinity', float('-inf')),
        ('constants', float('nan'), 'NaN', IsFloatNan),
    ),
)
def test_infinite_float_json_serialization(ser_json_inf_nan, input, output, python_roundtrip):
    class Model(BaseModel):
        model_config = ConfigDict(ser_json_inf_nan=ser_json_inf_nan)
        a: float

    json_string = Model(a=input).model_dump_json()
    assert json_string == f'{{"a":{output}}}'
    assert json.loads(json_string) == {'a': python_roundtrip}


@pytest.mark.parametrize('value', [float('inf'), float('-inf'), float('nan')])
def test_finite_float_validation_error(value):
    class Model(BaseModel):
        a: FiniteFloat

    assert Model(a=42).a == 42
    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'finite_number',
            'loc': ('a',),
            'msg': 'Input should be a finite number',
            'input': HasRepr(repr(value)),
        }
    ]


def test_finite_float_config():
    class Model(BaseModel):
        a: float

        model_config = ConfigDict(allow_inf_nan=False)

    assert Model(a=42).a == 42
    with pytest.raises(ValidationError) as exc_info:
        Model(a=float('nan'))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'finite_number',
            'loc': ('a',),
            'msg': 'Input should be a finite number',
            'input': HasRepr('nan'),
        }
    ]


def test_strict_bytes():
    class Model(BaseModel):
        v: StrictBytes

    assert Model(v=b'foobar').v == b'foobar'
    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        Model(v=bytearray('foobar', 'utf-8'))

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        Model(v='foostring')

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        Model(v=42)

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        Model(v=0.42)


def test_strict_bytes_max_length():
    class Model(BaseModel):
        u: StrictBytes = Field(..., max_length=5)

    assert Model(u=b'foo').u == b'foo'

    with pytest.raises(ValidationError, match=r'Input should be a valid bytes \[type=bytes_type'):
        Model(u=123)
    with pytest.raises(ValidationError, match=r'Data should have at most 5 bytes \[type=bytes_too_long,'):
        Model(u=b'1234567')


def test_strict_str():
    class FruitEnum(str, Enum):
        """A subclass of a string"""

        pear = 'pear'
        banana = 'banana'

    class Model(BaseModel):
        v: StrictStr

    assert Model(v='foobar').v == 'foobar'

    assert Model.model_validate({'v': FruitEnum.banana}) == Model.model_construct(v=FruitEnum.banana)

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        Model(v=123)

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        Model(v=b'foobar')


def test_strict_str_max_length():
    class Model(BaseModel):
        u: StrictStr = Field(..., max_length=5)

    assert Model(u='foo').u == 'foo'

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        Model(u=123)

    with pytest.raises(ValidationError, match=r'String should have at most 5 characters \[type=string_too_long,'):
        Model(u='1234567')


def test_strict_bool():
    class Model(BaseModel):
        v: StrictBool

    assert Model(v=True).v is True
    assert Model(v=False).v is False

    with pytest.raises(ValidationError):
        Model(v=1)

    with pytest.raises(ValidationError):
        Model(v='1')

    with pytest.raises(ValidationError):
        Model(v=b'1')


def test_strict_int():
    class Model(BaseModel):
        v: StrictInt

    assert Model(v=123456).v == 123456

    with pytest.raises(ValidationError, match=r'Input should be a valid integer \[type=int_type,'):
        Model(v='123456')

    with pytest.raises(ValidationError, match=r'Input should be a valid integer \[type=int_type,'):
        Model(v=3.14159)

    with pytest.raises(ValidationError, match=r'Input should be a valid integer \[type=int_type,'):
        Model(v=True)


@pytest.mark.parametrize(
    ('input', 'expected_json'),
    (
        (9_223_372_036_854_775_807, b'9223372036854775807'),
        (-9_223_372_036_854_775_807, b'-9223372036854775807'),
        (1433352099889938534014333520998899385340, b'1433352099889938534014333520998899385340'),
        (-1433352099889938534014333520998899385340, b'-1433352099889938534014333520998899385340'),
    ),
)
def test_big_int_json(input, expected_json):
    v = TypeAdapter(int)
    dumped = v.dump_json(input)
    assert dumped == expected_json
    assert v.validate_json(dumped) == input


def test_strict_float():
    class Model(BaseModel):
        v: StrictFloat

    assert Model(v=3.14159).v == 3.14159
    assert Model(v=123456).v == 123456

    with pytest.raises(ValidationError, match=r'Input should be a valid number \[type=float_type,'):
        Model(v='3.14159')

    with pytest.raises(ValidationError, match=r'Input should be a valid number \[type=float_type,'):
        Model(v=True)


def test_bool_unhashable_fails():
    class Model(BaseModel):
        v: bool

    with pytest.raises(ValidationError) as exc_info:
        Model(v={})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'bool_type', 'loc': ('v',), 'msg': 'Input should be a valid boolean', 'input': {}}
    ]


def test_uuid_error():
    v = TypeAdapter(UUID)

    valid = UUID('49fdfa1d856d4003a83e4b9236532ec6')

    # sanity check
    assert v.validate_python(valid) == valid
    assert v.validate_python(valid.hex) == valid

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('ebcdab58-6eb8-46fb-a190-d07a3')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'loc': (),
            'msg': 'Input should be a valid UUID, invalid group length in group 4: expected 12, found 5',
            'input': 'ebcdab58-6eb8-46fb-a190-d07a3',
            'ctx': {'error': 'invalid group length in group 4: expected 12, found 5'},
            'type': 'uuid_parsing',
        }
    ]

    not_a_valid_input_type = object()
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(not_a_valid_input_type)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': not_a_valid_input_type,
            'loc': (),
            'msg': 'UUID input should be a string, bytes or UUID object',
            'type': 'uuid_type',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(valid.hex, strict=True)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': (),
            'msg': 'Input should be an instance of UUID',
            'input': '49fdfa1d856d4003a83e4b9236532ec6',
            'ctx': {'class': 'UUID'},
        }
    ]

    assert v.validate_json(json.dumps(valid.hex), strict=True) == valid


def test_uuid_json():
    class Model(BaseModel):
        v: UUID
        v1: UUID1
        v3: UUID3
        v4: UUID4

    m = Model(v=uuid.uuid4(), v1=uuid.uuid1(), v3=uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org'), v4=uuid.uuid4())
    assert m.model_dump_json() == f'{{"v":"{m.v}","v1":"{m.v1}","v3":"{m.v3}","v4":"{m.v4}"}}'


def test_uuid_validation():
    class UUIDModel(BaseModel):
        a: UUID1
        b: UUID3
        c: UUID4
        d: UUID5
        e: UUID

    a = uuid.uuid1()
    b = uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
    c = uuid.uuid4()
    d = uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')
    e = UUID('{00000000-7fff-4000-7fff-000000000000}')

    m = UUIDModel(a=a, b=b, c=c, d=d, e=e)
    assert m.model_dump() == {'a': a, 'b': b, 'c': c, 'd': d, 'e': e}

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=d, b=c, c=b, d=a, e=e)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'uuid_version',
            'loc': ('a',),
            'msg': 'UUID version 1 expected',
            'input': d,
            'ctx': {'expected_version': 1},
        },
        {
            'type': 'uuid_version',
            'loc': ('b',),
            'msg': 'UUID version 3 expected',
            'input': c,
            'ctx': {'expected_version': 3},
        },
        {
            'type': 'uuid_version',
            'loc': ('c',),
            'msg': 'UUID version 4 expected',
            'input': b,
            'ctx': {'expected_version': 4},
        },
        {
            'type': 'uuid_version',
            'loc': ('d',),
            'msg': 'UUID version 5 expected',
            'input': a,
            'ctx': {'expected_version': 5},
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=e, b=e, c=e, d=e, e=e)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'uuid_version',
            'loc': ('a',),
            'msg': 'UUID version 1 expected',
            'input': e,
            'ctx': {'expected_version': 1},
        },
        {
            'type': 'uuid_version',
            'loc': ('b',),
            'msg': 'UUID version 3 expected',
            'input': e,
            'ctx': {'expected_version': 3},
        },
        {
            'type': 'uuid_version',
            'loc': ('c',),
            'msg': 'UUID version 4 expected',
            'input': e,
            'ctx': {'expected_version': 4},
        },
        {
            'type': 'uuid_version',
            'loc': ('d',),
            'msg': 'UUID version 5 expected',
            'input': e,
            'ctx': {'expected_version': 5},
        },
    ]


def test_uuid_strict() -> None:
    class StrictByConfig(BaseModel):
        a: UUID1
        b: UUID3
        c: UUID4
        d: UUID5
        e: uuid.UUID

        model_config = ConfigDict(strict=True)

    class StrictByField(BaseModel):
        a: UUID1 = Field(..., strict=True)
        b: UUID3 = Field(..., strict=True)
        c: UUID4 = Field(..., strict=True)
        d: UUID5 = Field(..., strict=True)
        e: uuid.UUID = Field(..., strict=True)

    a = uuid.UUID('7fb48116-ca6b-11ed-a439-3274d3adddac')  # uuid1
    b = uuid.UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e')  # uuid3
    c = uuid.UUID('260d1600-3680-4f4f-a968-f6fa622ffd8d')  # uuid4
    d = uuid.UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d')  # uuid5
    e = uuid.UUID('7fb48116-ca6b-11ed-a439-3274d3adddac')  # any uuid

    strict_errors = [
        {
            'type': 'is_instance_of',
            'loc': ('a',),
            'msg': 'Input should be an instance of UUID',
            'input': '7fb48116-ca6b-11ed-a439-3274d3adddac',
            'ctx': {'class': 'UUID'},
        },
        {
            'type': 'is_instance_of',
            'loc': ('b',),
            'msg': 'Input should be an instance of UUID',
            'input': '6fa459ea-ee8a-3ca4-894e-db77e160355e',
            'ctx': {'class': 'UUID'},
        },
        {
            'type': 'is_instance_of',
            'loc': ('c',),
            'msg': 'Input should be an instance of UUID',
            'input': '260d1600-3680-4f4f-a968-f6fa622ffd8d',
            'ctx': {'class': 'UUID'},
        },
        {
            'type': 'is_instance_of',
            'loc': ('d',),
            'msg': 'Input should be an instance of UUID',
            'input': '886313e1-3b8a-5372-9b90-0c9aee199e5d',
            'ctx': {'class': 'UUID'},
        },
        {
            'type': 'is_instance_of',
            'loc': ('e',),
            'msg': 'Input should be an instance of UUID',
            'input': '7fb48116-ca6b-11ed-a439-3274d3adddac',
            'ctx': {'class': 'UUID'},
        },
    ]

    for model in [StrictByConfig, StrictByField]:
        with pytest.raises(ValidationError) as exc_info:
            model(a=str(a), b=str(b), c=str(c), d=str(d), e=str(e))
        assert exc_info.value.errors(include_url=False) == strict_errors

        m = model(a=a, b=b, c=c, d=d, e=e)
        assert isinstance(m.a, type(a)) and m.a == a
        assert isinstance(m.b, type(b)) and m.b == b
        assert isinstance(m.c, type(c)) and m.c == c
        assert isinstance(m.d, type(d)) and m.d == d
        assert isinstance(m.e, type(e)) and m.e == e


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [
        (True, '  123  ', '123'),
        (True, '  123\t\n', '123'),
        (False, '  123  ', '  123  '),
    ],
)
def test_str_strip_whitespace(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        model_config = ConfigDict(str_strip_whitespace=enabled)

    m = Model(str_check=str_check)
    assert m.str_check == result_str_check


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [(True, 'ABCDefG', 'ABCDEFG'), (False, 'ABCDefG', 'ABCDefG')],
)
def test_str_to_upper(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        model_config = ConfigDict(str_to_upper=enabled)

    m = Model(str_check=str_check)

    assert m.str_check == result_str_check


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [(True, 'ABCDefG', 'abcdefg'), (False, 'ABCDefG', 'ABCDefG')],
)
def test_str_to_lower(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        model_config = ConfigDict(str_to_lower=enabled)

    m = Model(str_check=str_check)

    assert m.str_check == result_str_check


pos_int_values = 'Inf', '+Inf', 'Infinity', '+Infinity'
neg_int_values = '-Inf', '-Infinity'
nan_values = 'NaN', '-NaN', '+NaN', 'sNaN', '-sNaN', '+sNaN'
non_finite_values = nan_values + pos_int_values + neg_int_values
# dirty_equals.AnyThing() doesn't work with Decimal on PyPy, hence this hack
ANY_THING = object()


@pytest.mark.parametrize(
    'type_args,value,result',
    [
        (dict(gt=Decimal('42.24')), Decimal('43'), Decimal('43')),
        (
            dict(gt=Decimal('42.24')),
            Decimal('42'),
            [
                {
                    'type': 'greater_than',
                    'loc': ('foo',),
                    'msg': 'Input should be greater than 42.24',
                    'input': Decimal('42'),
                    'ctx': {'gt': Decimal('42.24')},
                }
            ],
        ),
        (dict(lt=Decimal('42.24')), Decimal('42'), Decimal('42')),
        (
            dict(lt=Decimal('42.24')),
            Decimal('43'),
            [
                {
                    'type': 'less_than',
                    'loc': ('foo',),
                    'msg': 'Input should be less than 42.24',
                    'input': Decimal('43'),
                    'ctx': {
                        'lt': Decimal('42.24'),
                    },
                },
            ],
        ),
        (dict(ge=Decimal('42.24')), Decimal('43'), Decimal('43')),
        (dict(ge=Decimal('42.24')), Decimal('42.24'), Decimal('42.24')),
        (
            dict(ge=Decimal('42.24')),
            Decimal('42'),
            [
                {
                    'type': 'greater_than_equal',
                    'loc': ('foo',),
                    'msg': 'Input should be greater than or equal to 42.24',
                    'input': Decimal('42'),
                    'ctx': {
                        'ge': Decimal('42.24'),
                    },
                }
            ],
        ),
        (dict(le=Decimal('42.24')), Decimal('42'), Decimal('42')),
        (dict(le=Decimal('42.24')), Decimal('42.24'), Decimal('42.24')),
        (
            dict(le=Decimal('42.24')),
            Decimal('43'),
            [
                {
                    'type': 'less_than_equal',
                    'loc': ('foo',),
                    'msg': 'Input should be less than or equal to 42.24',
                    'input': Decimal('43'),
                    'ctx': {
                        'le': Decimal('42.24'),
                    },
                }
            ],
        ),
        (dict(max_digits=2, decimal_places=2), Decimal('0.99'), Decimal('0.99')),
        pytest.param(
            dict(max_digits=2, decimal_places=1),
            Decimal('0.99'),
            [
                {
                    'type': 'decimal_max_places',
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 1 decimal place',
                    'input': Decimal('0.99'),
                    'ctx': {
                        'decimal_places': 1,
                    },
                }
            ],
        ),
        (
            dict(max_digits=3, decimal_places=1),
            Decimal('999'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 2 digits before the decimal point',
                    'type': 'decimal_whole_digits',
                    'input': Decimal('999'),
                    'ctx': {'whole_digits': 2},
                }
            ],
        ),
        (dict(max_digits=4, decimal_places=1), Decimal('999'), Decimal('999')),
        (dict(max_digits=20, decimal_places=2), Decimal('742403889818000000'), Decimal('742403889818000000')),
        (dict(max_digits=20, decimal_places=2), Decimal('7.42403889818E+17'), Decimal('7.42403889818E+17')),
        (dict(max_digits=6, decimal_places=2), Decimal('000000000001111.700000'), Decimal('000000000001111.700000')),
        (
            dict(max_digits=6, decimal_places=2),
            Decimal('0000000000011111.700000'),
            [
                {
                    'type': 'decimal_whole_digits',
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 4 digits before the decimal point',
                    'input': Decimal('11111.700000'),
                    'ctx': {'whole_digits': 4},
                }
            ],
        ),
        (
            dict(max_digits=20, decimal_places=2),
            Decimal('7424742403889818000000'),
            [
                {
                    'type': 'decimal_max_digits',
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 20 digits in total',
                    'input': Decimal('7424742403889818000000'),
                    'ctx': {
                        'max_digits': 20,
                    },
                },
            ],
        ),
        (dict(max_digits=5, decimal_places=2), Decimal('7304E-1'), Decimal('7304E-1')),
        (
            dict(max_digits=5, decimal_places=2),
            Decimal('7304E-3'),
            [
                {
                    'type': 'decimal_max_places',
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 2 decimal places',
                    'input': Decimal('7.304'),
                    'ctx': {'decimal_places': 2},
                }
            ],
        ),
        (dict(max_digits=5, decimal_places=5), Decimal('70E-5'), Decimal('70E-5')),
        (
            dict(max_digits=4, decimal_places=4),
            Decimal('70E-6'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 4 digits in total',
                    'type': 'decimal_max_digits',
                    'input': Decimal('0.00007'),
                    'ctx': {'max_digits': 4},
                }
            ],
        ),
        *[
            (
                dict(decimal_places=2, max_digits=10, allow_inf_nan=False),
                value,
                [
                    {
                        'loc': ('foo',),
                        'msg': 'Input should be a finite number',
                        'type': 'finite_number',
                        'input': value,
                    }
                ],
            )
            for value in non_finite_values
        ],
        *[
            (
                dict(decimal_places=2, max_digits=10, allow_inf_nan=False),
                Decimal(value),
                [
                    {
                        'loc': ('foo',),
                        'msg': 'Input should be a finite number',
                        'type': 'finite_number',
                        'input': ANY_THING,
                    }
                ],
            )
            for value in non_finite_values
        ],
        (
            dict(multiple_of=Decimal('5')),
            Decimal('42'),
            [
                {
                    'type': 'multiple_of',
                    'loc': ('foo',),
                    'msg': 'Input should be a multiple of 5',
                    'input': Decimal('42'),
                    'ctx': {'multiple_of': Decimal('5')},
                }
            ],
        ),
    ],
)
@pytest.mark.parametrize('mode', ['Field', 'condecimal', 'optional'])
def test_decimal_validation(mode, type_args, value, result):
    if mode == 'Field':

        class Model(BaseModel):
            foo: Decimal = Field(**type_args)

    elif mode == 'optional':

        class Model(BaseModel):
            foo: Optional[Decimal] = Field(**type_args)

    else:

        class Model(BaseModel):
            foo: condecimal(**type_args)

    if not isinstance(result, Decimal):
        with pytest.raises(ValidationError) as exc_info:
            m = Model(foo=value)
            print(f'unexpected result: {m!r}')
        # debug(exc_info.value.errors(include_url=False))
        # dirty_equals.AnyThing() doesn't work with Decimal on PyPy, hence this hack
        errors = exc_info.value.errors(include_url=False)
        if result[0].get('input') is ANY_THING:
            for e in errors:
                e['input'] = ANY_THING
        assert errors == result
        # assert exc_info.value.json().startswith('[')
    else:
        assert Model(foo=value).foo == result


@pytest.fixture(scope='module', name='AllowInfModel')
def fix_allow_inf_model():
    class Model(BaseModel):
        v: condecimal(allow_inf_nan=True)

    return Model


@pytest.mark.parametrize(
    'value,result',
    [
        (Decimal('42'), 'unchanged'),
        *[(v, 'is_nan') for v in nan_values],
        *[(v, 'is_pos_inf') for v in pos_int_values],
        *[(v, 'is_neg_inf') for v in neg_int_values],
    ],
)
def test_decimal_not_finite(value, result, AllowInfModel):
    m = AllowInfModel(v=value)
    if result == 'unchanged':
        assert m.v == value
    elif result == 'is_nan':
        assert m.v.is_nan(), m.v
    elif result == 'is_pos_inf':
        assert m.v.is_infinite() and m.v > 0, m.v
    else:
        assert result == 'is_neg_inf'
        assert m.v.is_infinite() and m.v < 0, m.v


def test_decimal_invalid():
    with pytest.raises(SchemaError, match='allow_inf_nan=True cannot be used with max_digits or decimal_places'):

        class Model(BaseModel):
            v: condecimal(allow_inf_nan=True, max_digits=4)


@pytest.mark.parametrize('value,result', (('/test/path', Path('/test/path')), (Path('/test/path'), Path('/test/path'))))
def test_path_validation_success(value, result):
    class Model(BaseModel):
        foo: Path

    assert Model(foo=value).foo == result
    assert Model.model_validate_json(json.dumps({'foo': str(value)})).foo == result


def test_path_validation_constrained():
    ta = TypeAdapter(Annotated[Path, Field(min_length=9, max_length=20)])
    with pytest.raises(ValidationError):
        ta.validate_python('/short')
    with pytest.raises(ValidationError):
        ta.validate_python('/' + 'long' * 100)
    assert ta.validate_python('/just/right/enough') == Path('/just/right/enough')


def test_path_like():
    class Model(BaseModel):
        foo: os.PathLike

    assert Model(foo='/foo/bar').foo == Path('/foo/bar')
    assert Model(foo=Path('/foo/bar')).foo == Path('/foo/bar')
    assert Model.model_validate_json('{"foo": "abc"}').foo == Path('abc')
    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'type': 'object',
        'properties': {'foo': {'type': 'string', 'format': 'path', 'title': 'Foo'}},
        'required': ['foo'],
        'title': 'Model',
    }


def test_path_like_strict():
    class Model(BaseModel):
        model_config = dict(strict=True)

        foo: os.PathLike

    with pytest.raises(ValidationError, match='Input should be an instance of PathLike'):
        Model(foo='/foo/bar')
    assert Model(foo=Path('/foo/bar')).foo == Path('/foo/bar')
    assert Model.model_validate_json('{"foo": "abc"}').foo == Path('abc')
    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'type': 'object',
        'properties': {'foo': {'type': 'string', 'format': 'path', 'title': 'Foo'}},
        'required': ['foo'],
        'title': 'Model',
    }


def test_path_strict_override():
    class Model(BaseModel):
        model_config = ConfigDict(strict=True)

        x: Path = Field(strict=False)

    m = Model(x='/foo/bar')
    assert m.x == Path('/foo/bar')


def test_path_validation_fails():
    class Model(BaseModel):
        foo: Path

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=123)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'path_type', 'loc': ('foo',), 'msg': 'Input is not a valid path', 'input': 123}
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=None)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'path_type', 'loc': ('foo',), 'msg': 'Input is not a valid path', 'input': None}
    ]


def test_path_validation_strict():
    class Model(BaseModel):
        foo: Path

        model_config = ConfigDict(strict=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(foo='/test/path')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': ('foo',),
            'msg': 'Input should be an instance of Path',
            'input': '/test/path',
            'ctx': {'class': 'Path'},
        }
    ]

    assert Model(foo=Path('/test/path')).foo == Path('/test/path')


@pytest.mark.parametrize(
    'value,result',
    (('tests/test_types.py', Path('tests/test_types.py')), (Path('tests/test_types.py'), Path('tests/test_types.py'))),
)
def test_file_path_validation_success(value, result):
    class Model(BaseModel):
        foo: FilePath

    assert Model(foo=value).foo == result


@pytest.mark.parametrize('value', ['nonexistentfile', Path('nonexistentfile'), 'tests', Path('tests')])
def test_file_path_validation_fails(value):
    class Model(BaseModel):
        foo: FilePath

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'path_not_file',
            'loc': ('foo',),
            'msg': 'Path does not point to a file',
            'input': value,
        }
    ]


@pytest.mark.parametrize('value,result', (('tests', Path('tests')), (Path('tests'), Path('tests'))))
def test_directory_path_validation_success(value, result):
    class Model(BaseModel):
        foo: DirectoryPath

    assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value', ['nonexistentdirectory', Path('nonexistentdirectory'), 'tests/test_t.py', Path('tests/test_ypestypes.py')]
)
def test_directory_path_validation_fails(value):
    class Model(BaseModel):
        foo: DirectoryPath

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'path_not_directory',
            'loc': ('foo',),
            'msg': 'Path does not point to a directory',
            'input': value,
        }
    ]


@pytest.mark.parametrize('value', ('tests/test_types.py', Path('tests/test_types.py')))
def test_new_path_validation_path_already_exists(value):
    class Model(BaseModel):
        foo: NewPath

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'path_exists',
            'loc': ('foo',),
            'msg': 'Path already exists',
            'input': value,
        }
    ]


@pytest.mark.parametrize('value', ('/nonexistentdir/foo.py', Path('/nonexistentdir/foo.py')))
def test_new_path_validation_parent_does_not_exist(value):
    class Model(BaseModel):
        foo: NewPath

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'parent_does_not_exist',
            'loc': ('foo',),
            'msg': 'Parent directory does not exist',
            'input': value,
        }
    ]


@pytest.mark.parametrize(
    'value,result', (('tests/foo.py', Path('tests/foo.py')), (Path('tests/foo.py'), Path('tests/foo.py')))
)
def test_new_path_validation_success(value, result):
    class Model(BaseModel):
        foo: NewPath

    assert Model(foo=value).foo == result


def test_number_gt():
    class Model(BaseModel):
        a: conint(gt=-1) = 0

    assert Model(a=0).model_dump() == {'a': 0}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('a',),
            'msg': 'Input should be greater than -1',
            'input': -1,
            'ctx': {'gt': -1},
        }
    ]


def test_number_ge():
    class Model(BaseModel):
        a: conint(ge=0) = 0

    assert Model(a=0).model_dump() == {'a': 0}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than_equal',
            'loc': ('a',),
            'msg': 'Input should be greater than or equal to 0',
            'input': -1,
            'ctx': {'ge': 0},
        }
    ]


def test_number_lt():
    class Model(BaseModel):
        a: conint(lt=5) = 0

    assert Model(a=4).model_dump() == {'a': 4}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=5)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'less_than',
            'loc': ('a',),
            'msg': 'Input should be less than 5',
            'input': 5,
            'ctx': {'lt': 5},
        }
    ]


def test_number_le():
    class Model(BaseModel):
        a: conint(le=5) = 0

    assert Model(a=5).model_dump() == {'a': 5}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=6)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'less_than_equal',
            'loc': ('a',),
            'msg': 'Input should be less than or equal to 5',
            'input': 6,
            'ctx': {'le': 5},
        }
    ]


@pytest.mark.parametrize('value', (10, 100, 20))
def test_number_multiple_of_int_valid(value):
    class Model(BaseModel):
        a: conint(multiple_of=5)

    assert Model(a=value).model_dump() == {'a': value}


@pytest.mark.parametrize('value', [1337, 23, 6, 14])
def test_number_multiple_of_int_invalid(value):
    class Model(BaseModel):
        a: conint(multiple_of=5)

    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'multiple_of',
            'loc': ('a',),
            'msg': 'Input should be a multiple of 5',
            'input': value,
            'ctx': {'multiple_of': 5},
        }
    ]


@pytest.mark.parametrize('value', [0.2, 0.3, 0.4, 0.5, 1])
def test_number_multiple_of_float_valid(value):
    class Model(BaseModel):
        a: confloat(multiple_of=0.1)

    assert Model(a=value).model_dump() == {'a': value}


@pytest.mark.parametrize('value', [0.07, 1.27, 1.003])
def test_number_multiple_of_float_invalid(value):
    class Model(BaseModel):
        a: confloat(multiple_of=0.1)

    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'multiple_of',
            'loc': ('a',),
            'msg': 'Input should be a multiple of 0.1',
            'input': value,
            'ctx': {'multiple_of': 0.1},
        }
    ]


def test_new_type_success():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', List[int])

    class Model(BaseModel):
        a: a_type
        b: b_type
        c: c_type

    m = Model(a=42, b=24, c=[1, 2, 3])
    assert m.model_dump() == {'a': 42, 'b': 24, 'c': [1, 2, 3]}


def test_new_type_fails():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', List[int])

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


@pytest.mark.parametrize('gen_type', [lambda: Json, lambda: Json[Any]])
def test_invalid_simple_json(gen_type):
    t = gen_type()

    class JsonModel(BaseModel):
        json_obj: t

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
        json_obj: Json[List[int]]

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
        b: List[int]

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
        b: List[int]

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
        json_obj: Json[List[int]]

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
        json_obj: Json[List[int]]

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
        json_obj: Optional[Json]

    assert JsonOptionalModel(json_obj=None).model_dump() == {'json_obj': None}
    assert JsonOptionalModel(json_obj='["x", "y", "z"]').model_dump() == {'json_obj': ['x', 'y', 'z']}


def test_json_optional_complex():
    class JsonOptionalModel(BaseModel):
        json_obj: Optional[Json[List[int]]]

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


@pytest.mark.parametrize(
    ('pattern_type', 'pattern_value', 'matching_value', 'non_matching_value'),
    [
        pytest.param(re.Pattern, r'^whatev.r\d$', 'whatever1', ' whatever1', id='re.Pattern'),
        pytest.param(Pattern, r'^whatev.r\d$', 'whatever1', ' whatever1', id='Pattern'),
        pytest.param(Pattern[str], r'^whatev.r\d$', 'whatever1', ' whatever1', id='Pattern[str]'),
        pytest.param(Pattern[bytes], rb'^whatev.r\d$', b'whatever1', b' whatever1', id='Pattern[bytes]'),
    ],
)
def test_pattern(pattern_type, pattern_value, matching_value, non_matching_value):
    class Foobar(BaseModel):
        pattern: pattern_type

    f = Foobar(pattern=pattern_value)
    assert f.pattern.__class__.__name__ == 'Pattern'
    # check it's really a proper pattern
    assert f.pattern.match(matching_value)
    assert not f.pattern.match(non_matching_value)

    # Check that pre-compiled patterns are accepted unchanged
    p = re.compile(pattern_value)
    f2 = Foobar(pattern=p)
    assert f2.pattern is p

    assert Foobar.model_json_schema() == {
        'type': 'object',
        'title': 'Foobar',
        'properties': {'pattern': {'type': 'string', 'format': 'regex', 'title': 'Pattern'}},
        'required': ['pattern'],
    }


@pytest.mark.parametrize(
    'use_field',
    [pytest.param(True, id='Field'), pytest.param(False, id='constr')],
)
def test_compiled_pattern_in_field(use_field):
    """
    https://github.com/pydantic/pydantic/issues/9052
    https://github.com/pydantic/pydantic/pull/9053
    """
    pattern_value = r'^whatev.r\d$'
    field_pattern = re.compile(pattern_value)

    if use_field:

        class Foobar(BaseModel):
            str_regex: str = Field(..., pattern=field_pattern)
    else:

        class Foobar(BaseModel):
            str_regex: constr(pattern=field_pattern) = ...

    field_general_metadata = Foobar.model_fields['str_regex'].metadata
    assert len(field_general_metadata) == 1
    field_metadata_pattern = field_general_metadata[0].pattern

    assert field_metadata_pattern == field_pattern
    assert isinstance(field_metadata_pattern, re.Pattern)

    matching_value = 'whatever1'
    f = Foobar(str_regex=matching_value)
    assert f.str_regex == matching_value

    with pytest.raises(
        ValidationError,
        match=re.escape("String should match pattern '" + pattern_value + "'"),
    ):
        Foobar(str_regex=' whatever1')

    assert Foobar.model_json_schema() == {
        'type': 'object',
        'title': 'Foobar',
        'properties': {'str_regex': {'pattern': pattern_value, 'title': 'Str Regex', 'type': 'string'}},
        'required': ['str_regex'],
    }


def test_pattern_with_invalid_param():
    with pytest.raises(
        PydanticSchemaGenerationError,
        match=re.escape('Unable to generate pydantic-core schema for typing.Pattern[int].'),
    ):

        class Foo(BaseModel):
            pattern: Pattern[int]


@pytest.mark.parametrize(
    ('pattern_type', 'pattern_value', 'error_type', 'error_msg'),
    [
        pytest.param(
            re.Pattern,
            '[xx',
            'pattern_regex',
            'Input should be a valid regular expression',
            id='re.Pattern-pattern_regex',
        ),
        pytest.param(
            Pattern, '[xx', 'pattern_regex', 'Input should be a valid regular expression', id='re.Pattern-pattern_regex'
        ),
        pytest.param(
            re.Pattern, (), 'pattern_type', 'Input should be a valid pattern', id='typing.Pattern-pattern_type'
        ),
        pytest.param(Pattern, (), 'pattern_type', 'Input should be a valid pattern', id='typing.Pattern-pattern_type'),
        pytest.param(
            Pattern[str],
            re.compile(b''),
            'pattern_str_type',
            'Input should be a string pattern',
            id='typing.Pattern[str]-pattern_str_type-non_str',
        ),
        pytest.param(
            Pattern[str],
            b'',
            'pattern_str_type',
            'Input should be a string pattern',
            id='typing.Pattern[str]-pattern_str_type-bytes',
        ),
        pytest.param(
            Pattern[str], (), 'pattern_type', 'Input should be a valid pattern', id='typing.Pattern[str]-pattern_type'
        ),
        pytest.param(
            Pattern[bytes],
            re.compile(''),
            'pattern_bytes_type',
            'Input should be a bytes pattern',
            id='typing.Pattern[bytes]-pattern_bytes_type-non_bytes',
        ),
        pytest.param(
            Pattern[bytes],
            '',
            'pattern_bytes_type',
            'Input should be a bytes pattern',
            id='typing.Pattern[bytes]-pattern_bytes_type-str',
        ),
        pytest.param(
            Pattern[bytes],
            (),
            'pattern_type',
            'Input should be a valid pattern',
            id='typing.Pattern[bytes]-pattern_type',
        ),
    ],
)
def test_pattern_error(pattern_type, pattern_value, error_type, error_msg):
    class Foobar(BaseModel):
        pattern: pattern_type

    with pytest.raises(ValidationError) as exc_info:
        Foobar(pattern=pattern_value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': error_type, 'loc': ('pattern',), 'msg': error_msg, 'input': pattern_value}
    ]


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
        1e1000,
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
        x: Union[Secret[int], Secret[str]]

    model = Base(x=1)
    assert model.model_dump() == {'x': Secret[int](1)}
    assert model.model_dump_json() == '{"x":"**********"}'


@pytest.mark.parametrize(
    'pydantic_type',
    [
        Strict,
        StrictBool,
        conint,
        PositiveInt,
        NegativeInt,
        NonPositiveInt,
        NonNegativeInt,
        StrictInt,
        confloat,
        PositiveFloat,
        NegativeFloat,
        NonPositiveFloat,
        NonNegativeFloat,
        StrictFloat,
        FiniteFloat,
        conbytes,
        Secret,
        SecretBytes,
        constr,
        StrictStr,
        SecretStr,
        ImportString,
        conset,
        confrozenset,
        conlist,
        condecimal,
        UUID1,
        UUID3,
        UUID4,
        UUID5,
        FilePath,
        DirectoryPath,
        NewPath,
        Json,
        ByteSize,
        condate,
        PastDate,
        FutureDate,
        PastDatetime,
        FutureDatetime,
        AwareDatetime,
        NaiveDatetime,
    ],
)
def test_is_hashable(pydantic_type):
    assert type(hash(pydantic_type)) is int


def test_model_contain_hashable_type():
    class MyModel(BaseModel):
        v: Union[str, StrictStr]

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
        generic_list: List
        generic_dict: Dict
        generic_tuple: Tuple

    m = Model(generic_list=[0, 'a'], generic_dict={0: 'a', 'a': 0}, generic_tuple=(1, 'q'))
    assert m.model_dump() == {'generic_list': [0, 'a'], 'generic_dict': {0: 'a', 'a': 0}, 'generic_tuple': (1, 'q')}


def test_generic_without_params_error():
    class Model(BaseModel):
        generic_list: List
        generic_dict: Dict
        generic_tuple: Tuple

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


def test_literal_single():
    class Model(BaseModel):
        a: Literal['a']

    Model(a='a')
    with pytest.raises(ValidationError) as exc_info:
        Model(a='b')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ('a',),
            'msg': "Input should be 'a'",
            'input': 'b',
            'ctx': {'expected': "'a'"},
        }
    ]


def test_literal_multiple():
    class Model(BaseModel):
        a_or_b: Literal['a', 'b']

    Model(a_or_b='a')
    Model(a_or_b='b')
    with pytest.raises(ValidationError) as exc_info:
        Model(a_or_b='c')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ('a_or_b',),
            'msg': "Input should be 'a' or 'b'",
            'input': 'c',
            'ctx': {'expected': "'a' or 'b'"},
        }
    ]


def test_typing_mutable_set():
    s1 = TypeAdapter(Set[int]).core_schema
    s1.pop('metadata', None)
    s2 = TypeAdapter(typing.MutableSet[int]).core_schema
    s2.pop('metadata', None)
    assert s1 == s2


def test_frozenset_field():
    class FrozenSetModel(BaseModel):
        set: FrozenSet[int]

    test_set = frozenset({1, 2, 3})
    object_under_test = FrozenSetModel(set=test_set)

    assert object_under_test.set == test_set


@pytest.mark.parametrize(
    'value,result',
    [
        ([1, 2, 3], frozenset([1, 2, 3])),
        ({1, 2, 3}, frozenset([1, 2, 3])),
        ((1, 2, 3), frozenset([1, 2, 3])),
        (deque([1, 2, 3]), frozenset([1, 2, 3])),
    ],
)
def test_frozenset_field_conversion(value, result):
    class FrozenSetModel(BaseModel):
        set: FrozenSet[int]

    object_under_test = FrozenSetModel(set=value)

    assert object_under_test.set == result


def test_frozenset_field_not_convertible():
    class FrozenSetModel(BaseModel):
        set: FrozenSet[int]

    with pytest.raises(ValidationError, match=r'frozenset'):
        FrozenSetModel(set=42)


@pytest.mark.parametrize(
    'input_value,output,human_bin,human_dec,human_sep',
    (
        (1, 1, '1B', '1B', '1 B'),
        ('1', 1, '1B', '1B', '1 B'),
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


def test_deque_success():
    class Model(BaseModel):
        v: deque

    assert Model(v=[1, 2, 3]).v == deque([1, 2, 3])


@pytest.mark.parametrize(
    'cls,value,result',
    (
        (int, [1, 2, 3], deque([1, 2, 3])),
        (int, (1, 2, 3), deque((1, 2, 3))),
        (int, deque((1, 2, 3)), deque((1, 2, 3))),
        (float, [1.0, 2.0, 3.0], deque([1.0, 2.0, 3.0])),
        (Set[int], [{1, 2}, {3, 4}, {5, 6}], deque([{1, 2}, {3, 4}, {5, 6}])),
        (Tuple[int, str], ((1, 'a'), (2, 'b'), (3, 'c')), deque(((1, 'a'), (2, 'b'), (3, 'c')))),
        (str, [w for w in 'one two three'.split()], deque(['one', 'two', 'three'])),
        (
            int,
            {1: 10, 2: 20, 3: 30}.keys(),
            deque([1, 2, 3]),
        ),
        (
            int,
            {1: 10, 2: 20, 3: 30}.values(),
            deque([10, 20, 30]),
        ),
        (
            Tuple[int, int],
            {1: 10, 2: 20, 3: 30}.items(),
            deque([(1, 10), (2, 20), (3, 30)]),
        ),
        (
            float,
            {1, 2, 3},
            deque([1, 2, 3]),
        ),
        (
            float,
            frozenset((1, 2, 3)),
            deque([1, 2, 3]),
        ),
    ),
)
def test_deque_generic_success(cls, value, result):
    class Model(BaseModel):
        v: Deque[cls]

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'cls,value,result',
    (
        (int, deque((1, 2, 3)), deque((1, 2, 3))),
        (str, deque(('1', '2', '3')), deque(('1', '2', '3'))),
    ),
)
def test_deque_generic_success_strict(cls, value: Any, result):
    class Model(BaseModel):
        v: Deque[cls]

        model_config = ConfigDict(strict=True)

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'cls,value,expected_error',
    (
        (
            int,
            [1, 'a', 3],
            {
                'type': 'int_parsing',
                'loc': ('v', 1),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'a',
            },
        ),
        (
            int,
            (1, 2, 'a'),
            {
                'type': 'int_parsing',
                'loc': ('v', 2),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'a',
            },
        ),
        (
            Tuple[int, str],
            ((1, 'a'), ('a', 'a'), (3, 'c')),
            {
                'type': 'int_parsing',
                'loc': ('v', 1, 0),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'a',
            },
        ),
        (
            List[int],
            [{'a': 1, 'b': 2}, [1, 2], [2, 3]],
            {
                'type': 'list_type',
                'loc': ('v', 0),
                'msg': 'Input should be a valid list',
                'input': {
                    'a': 1,
                    'b': 2,
                },
            },
        ),
    ),
)
def test_deque_fails(cls, value, expected_error):
    class Model(BaseModel):
        v: Deque[cls]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    # debug(exc_info.value.errors(include_url=False))
    assert len(exc_info.value.errors(include_url=False)) == 1
    assert expected_error == exc_info.value.errors(include_url=False)[0]


def test_deque_model():
    class Model2(BaseModel):
        x: int

    class Model(BaseModel):
        v: Deque[Model2]

    seq = [Model2(x=1), Model2(x=2)]
    assert Model(v=seq).v == deque(seq)


def test_deque_json():
    class Model(BaseModel):
        v: Deque[int]

    assert Model(v=deque((1, 2, 3))).model_dump_json() == '{"v":[1,2,3]}'


def test_deque_any_maxlen():
    class DequeModel1(BaseModel):
        field: deque

    assert DequeModel1(field=deque()).field.maxlen is None
    assert DequeModel1(field=deque(maxlen=8)).field.maxlen == 8

    class DequeModel2(BaseModel):
        field: deque = deque()

    assert DequeModel2().field.maxlen is None
    assert DequeModel2(field=deque()).field.maxlen is None
    assert DequeModel2(field=deque(maxlen=8)).field.maxlen == 8

    class DequeModel3(BaseModel):
        field: deque = deque(maxlen=5)

    assert DequeModel3().field.maxlen == 5
    assert DequeModel3(field=deque()).field.maxlen is None
    assert DequeModel3(field=deque(maxlen=8)).field.maxlen == 8


def test_deque_typed_maxlen():
    class DequeModel1(BaseModel):
        field: Deque[int]

    assert DequeModel1(field=deque()).field.maxlen is None
    assert DequeModel1(field=deque(maxlen=8)).field.maxlen == 8

    class DequeModel2(BaseModel):
        field: Deque[int] = deque()

    assert DequeModel2().field.maxlen is None
    assert DequeModel2(field=deque()).field.maxlen is None
    assert DequeModel2(field=deque(maxlen=8)).field.maxlen == 8

    class DequeModel3(BaseModel):
        field: Deque[int] = deque(maxlen=5)

    assert DequeModel3().field.maxlen == 5
    assert DequeModel3(field=deque()).field.maxlen is None
    assert DequeModel3(field=deque(maxlen=8)).field.maxlen == 8


def test_deque_set_maxlen():
    class DequeModel1(BaseModel):
        field: Annotated[Deque[int], Field(max_length=10)]

    assert DequeModel1(field=deque()).field.maxlen == 10
    assert DequeModel1(field=deque(maxlen=8)).field.maxlen == 8
    assert DequeModel1(field=deque(maxlen=15)).field.maxlen == 10

    class DequeModel2(BaseModel):
        field: Annotated[Deque[int], Field(max_length=10)] = deque()

    assert DequeModel2().field.maxlen is None
    assert DequeModel2(field=deque()).field.maxlen == 10
    assert DequeModel2(field=deque(maxlen=8)).field.maxlen == 8
    assert DequeModel2(field=deque(maxlen=15)).field.maxlen == 10

    class DequeModel3(DequeModel2):
        model_config = ConfigDict(validate_default=True)

    assert DequeModel3().field.maxlen == 10

    class DequeModel4(BaseModel):
        field: Annotated[Deque[int], Field(max_length=10)] = deque(maxlen=5)

    assert DequeModel4().field.maxlen == 5

    class DequeModel5(DequeModel4):
        model_config = ConfigDict(validate_default=True)

    assert DequeModel4().field.maxlen == 5


@pytest.mark.parametrize('value_type', (None, type(None), None.__class__))
def test_none(value_type):
    class Model(BaseModel):
        my_none: value_type
        my_none_list: List[value_type]
        my_none_dict: Dict[str, value_type]
        my_json_none: Json[value_type]

    Model(
        my_none=None,
        my_none_list=[None] * 3,
        my_none_dict={'a': None, 'b': None},
        my_json_none='null',
    )

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'my_none': {'type': 'null', 'title': 'My None'},
            'my_none_list': {'type': 'array', 'items': {'type': 'null'}, 'title': 'My None List'},
            'my_none_dict': {'type': 'object', 'additionalProperties': {'type': 'null'}, 'title': 'My None Dict'},
            'my_json_none': {
                'contentMediaType': 'application/json',
                'contentSchema': {'type': 'null'},
                'title': 'My Json None',
                'type': 'string',
            },
        },
        'required': ['my_none', 'my_none_list', 'my_none_dict', 'my_json_none'],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(
            my_none='qwe',
            my_none_list=[1, None, 'qwe'],
            my_none_dict={'a': 1, 'b': None},
            my_json_none='"a"',
        )
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'none_required', 'loc': ('my_none',), 'msg': 'Input should be None', 'input': 'qwe'},
        {'type': 'none_required', 'loc': ('my_none_list', 0), 'msg': 'Input should be None', 'input': 1},
        {
            'type': 'none_required',
            'loc': ('my_none_list', 2),
            'msg': 'Input should be None',
            'input': 'qwe',
        },
        {
            'type': 'none_required',
            'loc': ('my_none_dict', 'a'),
            'msg': 'Input should be None',
            'input': 1,
        },
        {'type': 'none_required', 'loc': ('my_json_none',), 'msg': 'Input should be None', 'input': 'a'},
    ]


def test_none_literal():
    class Model(BaseModel):
        my_none: Literal[None]
        my_none_list: List[Literal[None]]
        my_none_dict: Dict[str, Literal[None]]
        my_json_none: Json[Literal[None]]

    Model(
        my_none=None,
        my_none_list=[None] * 3,
        my_none_dict={'a': None, 'b': None},
        my_json_none='null',
    )

    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'my_none': {'const': None, 'enum': [None], 'title': 'My None', 'type': 'null'},
            'my_none_list': {
                'items': {'const': None, 'enum': [None], 'type': 'null'},
                'title': 'My None List',
                'type': 'array',
            },
            'my_none_dict': {
                'additionalProperties': {'const': None, 'enum': [None], 'type': 'null'},
                'title': 'My None Dict',
                'type': 'object',
            },
            'my_json_none': {
                'contentMediaType': 'application/json',
                'contentSchema': {'const': None, 'enum': [None], 'type': 'null'},
                'title': 'My Json None',
                'type': 'string',
            },
        },
        'required': ['my_none', 'my_none_list', 'my_none_dict', 'my_json_none'],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(
            my_none='qwe',
            my_none_list=[1, None, 'qwe'],
            my_none_dict={'a': 1, 'b': None},
            my_json_none='"a"',
        )
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ('my_none',),
            'msg': 'Input should be None',
            'input': 'qwe',
            'ctx': {'expected': 'None'},
        },
        {
            'type': 'literal_error',
            'loc': ('my_none_list', 0),
            'msg': 'Input should be None',
            'input': 1,
            'ctx': {'expected': 'None'},
        },
        {
            'type': 'literal_error',
            'loc': ('my_none_list', 2),
            'msg': 'Input should be None',
            'input': 'qwe',
            'ctx': {'expected': 'None'},
        },
        {
            'type': 'literal_error',
            'loc': ('my_none_dict', 'a'),
            'msg': 'Input should be None',
            'input': 1,
            'ctx': {'expected': 'None'},
        },
        {
            'type': 'literal_error',
            'loc': ('my_json_none',),
            'msg': 'Input should be None',
            'input': 'a',
            'ctx': {'expected': 'None'},
        },
    ]


def test_default_union_types():
    class DefaultModel(BaseModel):
        v: Union[int, bool, str]

    # do it this way since `1 == True`
    assert repr(DefaultModel(v=True).v) == 'True'
    assert repr(DefaultModel(v=1).v) == '1'
    assert repr(DefaultModel(v='1').v) == "'1'"

    assert DefaultModel.model_json_schema() == {
        'title': 'DefaultModel',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'anyOf': [{'type': t} for t in ('integer', 'boolean', 'string')]}},
        'required': ['v'],
    }


def test_default_union_types_left_to_right():
    class DefaultModel(BaseModel):
        v: Annotated[Union[int, bool, str], Field(union_mode='left_to_right')]

    print(DefaultModel.__pydantic_core_schema__)

    # int will coerce everything in left-to-right mode
    assert repr(DefaultModel(v=True).v) == '1'
    assert repr(DefaultModel(v=1).v) == '1'
    assert repr(DefaultModel(v='1').v) == '1'

    assert DefaultModel.model_json_schema() == {
        'title': 'DefaultModel',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'anyOf': [{'type': t} for t in ('integer', 'boolean', 'string')]}},
        'required': ['v'],
    }


def test_union_enum_int_left_to_right():
    class BinaryEnum(IntEnum):
        ZERO = 0
        ONE = 1

    # int will win over enum in this case
    assert TypeAdapter(Union[BinaryEnum, int]).validate_python(0) is not BinaryEnum.ZERO

    # in left to right mode, enum will validate successfully and take precedence
    assert (
        TypeAdapter(Annotated[Union[BinaryEnum, int], Field(union_mode='left_to_right')]).validate_python(0)
        is BinaryEnum.ZERO
    )


def test_union_uuid_str_left_to_right():
    IdOrSlug = Union[UUID, str]

    # in smart mode JSON and python are currently validated differently in this
    # case, because in Python this is a str but in JSON a str is also a UUID
    assert TypeAdapter(IdOrSlug).validate_json('"f4fe10b4-e0c8-4232-ba26-4acd491c2414"') == UUID(
        'f4fe10b4-e0c8-4232-ba26-4acd491c2414'
    )
    assert (
        TypeAdapter(IdOrSlug).validate_python('f4fe10b4-e0c8-4232-ba26-4acd491c2414')
        == 'f4fe10b4-e0c8-4232-ba26-4acd491c2414'
    )

    IdOrSlugLTR = Annotated[Union[UUID, str], Field(union_mode='left_to_right')]

    # in left to right mode both JSON and python are validated as UUID
    assert TypeAdapter(IdOrSlugLTR).validate_json('"f4fe10b4-e0c8-4232-ba26-4acd491c2414"') == UUID(
        'f4fe10b4-e0c8-4232-ba26-4acd491c2414'
    )
    assert TypeAdapter(IdOrSlugLTR).validate_python('f4fe10b4-e0c8-4232-ba26-4acd491c2414') == UUID(
        'f4fe10b4-e0c8-4232-ba26-4acd491c2414'
    )


def test_default_union_class():
    class A(BaseModel):
        x: str

    class B(BaseModel):
        x: str

    class Model(BaseModel):
        y: Union[A, B]

    assert isinstance(Model(y=A(x='a')).y, A)
    assert isinstance(Model(y=B(x='b')).y, B)


@pytest.mark.parametrize('max_length', [10, None])
def test_union_subclass(max_length: Union[int, None]):
    class MyStr(str): ...

    class Model(BaseModel):
        x: Union[int, Annotated[str, Field(max_length=max_length)]]

    v = Model(x=MyStr('1')).x
    assert type(v) is str
    assert v == '1'


def test_union_compound_types():
    class Model(BaseModel):
        values: Union[Dict[str, str], List[str], Dict[str, List[str]]]

    assert Model(values={'L': '1'}).model_dump() == {'values': {'L': '1'}}
    assert Model(values=['L1']).model_dump() == {'values': ['L1']}
    assert Model(values=('L1',)).model_dump() == {'values': ['L1']}
    assert Model(values={'x': ['pika']}) != {'values': {'x': ['pika']}}
    assert Model(values={'x': ('pika',)}).model_dump() == {'values': {'x': ['pika']}}
    with pytest.raises(ValidationError) as e:
        Model(values={'x': {'a': 'b'}})
    # insert_assert(e.value.errors(include_url=False))
    assert e.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': ('values', 'dict[str,str]', 'x'),
            'msg': 'Input should be a valid string',
            'input': {'a': 'b'},
        },
        {
            'type': 'list_type',
            'loc': ('values', 'list[str]'),
            'msg': 'Input should be a valid list',
            'input': {'x': {'a': 'b'}},
        },
        {
            'type': 'list_type',
            'loc': ('values', 'dict[str,list[str]]', 'x'),
            'msg': 'Input should be a valid list',
            'input': {'a': 'b'},
        },
    ]


def test_smart_union_compounded_types_edge_case():
    class Model(BaseModel):
        x: Union[List[str], List[int]]

    assert Model(x=[1, 2]).x == [1, 2]
    assert Model(x=['1', '2']).x == ['1', '2']
    assert Model(x=[1, '2']).x == [1, 2]


def test_union_typeddict():
    class Dict1(TypedDict):
        foo: str

    class Dict2(TypedDict):
        bar: str

    class M(BaseModel):
        d: Union[Dict2, Dict1]

    assert M(d=dict(foo='baz')).d == {'foo': 'baz'}


def test_custom_generic_containers():
    T = TypeVar('T')

    class GenericList(List[T]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.no_info_after_validator_function(GenericList, handler(List[get_args(source_type)[0]]))

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
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]


@pytest.mark.parametrize(
    ('field_type', 'input_data', 'expected_value', 'serialized_data'),
    [
        pytest.param(Base64Bytes, b'Zm9vIGJhcg==\n', b'foo bar', b'Zm9vIGJhcg==\n', id='Base64Bytes-reversible'),
        pytest.param(Base64Str, 'Zm9vIGJhcg==\n', 'foo bar', 'Zm9vIGJhcg==\n', id='Base64Str-reversible'),
        pytest.param(Base64Bytes, b'Zm9vIGJhcg==', b'foo bar', b'Zm9vIGJhcg==\n', id='Base64Bytes-bytes-input'),
        pytest.param(Base64Bytes, 'Zm9vIGJhcg==', b'foo bar', b'Zm9vIGJhcg==\n', id='Base64Bytes-str-input'),
        pytest.param(
            Base64Bytes, bytearray(b'Zm9vIGJhcg=='), b'foo bar', b'Zm9vIGJhcg==\n', id='Base64Bytes-bytearray-input'
        ),
        pytest.param(Base64Str, b'Zm9vIGJhcg==', 'foo bar', 'Zm9vIGJhcg==\n', id='Base64Str-bytes-input'),
        pytest.param(Base64Str, 'Zm9vIGJhcg==', 'foo bar', 'Zm9vIGJhcg==\n', id='Base64Str-str-input'),
        pytest.param(
            Base64Str, bytearray(b'Zm9vIGJhcg=='), 'foo bar', 'Zm9vIGJhcg==\n', id='Base64Str-bytearray-input'
        ),
        pytest.param(
            Base64Bytes,
            b'BCq+6+1/Paun/Q==',
            b'\x04*\xbe\xeb\xed\x7f=\xab\xa7\xfd',
            b'BCq+6+1/Paun/Q==\n',
            id='Base64Bytes-bytes-alphabet-vanilla',
        ),
    ],
)
def test_base64(field_type, input_data, expected_value, serialized_data):
    class Model(BaseModel):
        base64_value: field_type
        base64_value_or_none: Optional[field_type] = None

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
        base64url_value_or_none: Optional[field_type] = None

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


def test_sequence_subclass_without_core_schema() -> None:
    class MyList(List[int]):
        # The point of this is that subclasses can do arbitrary things
        # This is the reason why we don't try to handle them automatically
        # TBD if we introspect `__init__` / `__new__`
        # (which is the main thing that would mess us up if modified in a subclass)
        # and automatically handle cases where the subclass doesn't override it.
        # There's still edge cases (again, arbitrary behavior...)
        # and it's harder to explain, but could lead to a better user experience in some cases
        # It will depend on how the complaints (which have and will happen in both directions)
        # balance out
        def __init__(self, *args: Any, required: int, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)

    with pytest.raises(
        PydanticSchemaGenerationError, match='implement `__get_pydantic_core_schema__` on your type to fully support it'
    ):

        class _(BaseModel):
            x: MyList


def test_typing_coercion_defaultdict():
    class Model(BaseModel):
        x: DefaultDict[int, str]

    d = defaultdict(str)
    d['1']
    m = Model(x=d)
    assert isinstance(m.x, defaultdict)
    assert repr(m.x) == "defaultdict(<class 'str'>, {1: ''})"


def test_typing_coercion_counter():
    class Model(BaseModel):
        x: Counter[str]

    m = Model(x={'a': 10})
    assert isinstance(m.x, Counter)
    assert repr(m.x) == "Counter({'a': 10})"


def test_typing_counter_value_validation():
    class Model(BaseModel):
        x: Counter[str]

    with pytest.raises(ValidationError) as exc_info:
        Model(x={'a': 'a'})

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('x', 'a'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]


def test_mapping_subclass_without_core_schema() -> None:
    class MyDict(Dict[int, int]):
        # The point of this is that subclasses can do arbitrary things
        # This is the reason why we don't try to handle them automatically
        # TBD if we introspect `__init__` / `__new__`
        # (which is the main thing that would mess us up if modified in a subclass)
        # and automatically handle cases where the subclass doesn't override it.
        # There's still edge cases (again, arbitrary behavior...)
        # and it's harder to explain, but could lead to a better user experience in some cases
        # It will depend on how the complaints (which have and will happen in both directions)
        # balance out
        def __init__(self, *args: Any, required: int, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)

    with pytest.raises(
        PydanticSchemaGenerationError, match='implement `__get_pydantic_core_schema__` on your type to fully support it'
    ):

        class _(BaseModel):
            x: MyDict


def test_defaultdict_unknown_default_factory() -> None:
    """
    https://github.com/pydantic/pydantic/issues/4687
    """
    with pytest.raises(
        PydanticSchemaGenerationError,
        match=r'Unable to infer a default factory for keys of type typing.DefaultDict\[int, int\]',
    ):

        class Model(BaseModel):
            d: DefaultDict[int, DefaultDict[int, int]]


def test_defaultdict_infer_default_factory() -> None:
    class Model(BaseModel):
        a: DefaultDict[int, List[int]]
        b: DefaultDict[int, int]
        c: DefaultDict[int, set]

    m = Model(a={}, b={}, c={})
    assert m.a.default_factory is not None
    assert m.a.default_factory() == []
    assert m.b.default_factory is not None
    assert m.b.default_factory() == 0
    assert m.c.default_factory is not None
    assert m.c.default_factory() == set()


def test_defaultdict_explicit_default_factory() -> None:
    class MyList(List[int]):
        pass

    class Model(BaseModel):
        a: DefaultDict[int, Annotated[List[int], Field(default_factory=lambda: MyList())]]

    m = Model(a={})
    assert m.a.default_factory is not None
    assert isinstance(m.a.default_factory(), MyList)


def test_defaultdict_default_factory_preserved() -> None:
    class Model(BaseModel):
        a: DefaultDict[int, List[int]]

    class MyList(List[int]):
        pass

    m = Model(a=defaultdict(lambda: MyList()))
    assert m.a.default_factory is not None
    assert isinstance(m.a.default_factory(), MyList)


def test_custom_default_dict() -> None:
    KT = TypeVar('KT')
    VT = TypeVar('VT')

    class CustomDefaultDict(DefaultDict[KT, VT]):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            keys_type, values_type = get_args(source_type)
            return core_schema.no_info_after_validator_function(
                lambda x: cls(x.default_factory, x), handler(DefaultDict[keys_type, values_type])
            )

    ta = TypeAdapter(CustomDefaultDict[str, int])

    assert ta.validate_python({'a': 1}) == CustomDefaultDict(int, {'a': 1})


@pytest.mark.parametrize('field_type', [typing.OrderedDict, collections.OrderedDict])
def test_ordered_dict_from_ordered_dict(field_type):
    class Model(BaseModel):
        od_field: field_type

    od_value = collections.OrderedDict([('a', 1), ('b', 2)])

    m = Model(od_field=od_value)

    assert isinstance(m.od_field, collections.OrderedDict)
    assert m.od_field == od_value
    # we don't make any promises about preserving instances
    # at the moment we always copy them for consistency and predictability
    # so this is more so documenting the current behavior than a promise
    # we make to users
    assert m.od_field is not od_value

    assert m.model_json_schema() == {
        'properties': {'od_field': {'title': 'Od Field', 'type': 'object'}},
        'required': ['od_field'],
        'title': 'Model',
        'type': 'object',
    }


def test_ordered_dict_from_ordered_dict_typed():
    class Model(BaseModel):
        od_field: typing.OrderedDict[str, int]

    od_value = collections.OrderedDict([('a', 1), ('b', 2)])

    m = Model(od_field=od_value)

    assert isinstance(m.od_field, collections.OrderedDict)
    assert m.od_field == od_value

    assert m.model_json_schema() == {
        'properties': {
            'od_field': {
                'additionalProperties': {'type': 'integer'},
                'title': 'Od Field',
                'type': 'object',
            }
        },
        'required': ['od_field'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('field_type', [typing.OrderedDict, collections.OrderedDict])
def test_ordered_dict_from_dict(field_type):
    class Model(BaseModel):
        od_field: field_type

    od_value = {'a': 1, 'b': 2}

    m = Model(od_field=od_value)

    assert isinstance(m.od_field, collections.OrderedDict)
    assert m.od_field == collections.OrderedDict(od_value)

    assert m.model_json_schema() == {
        'properties': {'od_field': {'title': 'Od Field', 'type': 'object'}},
        'required': ['od_field'],
        'title': 'Model',
        'type': 'object',
    }


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
        type_hint = Optional[type_hint]

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


def test_transform_schema():
    ValidateStrAsInt = Annotated[str, GetPydanticSchema(lambda _s, h: core_schema.int_schema())]

    class Model(BaseModel):
        x: Optional[ValidateStrAsInt]

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


def test_iterable_arbitrary_type():
    class CustomIterable(Iterable):
        def __init__(self, iterable):
            self.iterable = iterable

        def __iter__(self):
            return self

        def __next__(self):
            return next(self.iterable)

    with pytest.raises(
        PydanticSchemaGenerationError,
        match='Unable to generate pydantic-core schema for .*CustomIterable.*. Set `arbitrary_types_allowed=True`',
    ):

        class Model(BaseModel):
            x: CustomIterable


def test_typing_extension_literal_field():
    from typing_extensions import Literal

    class Model(BaseModel):
        foo: Literal['foo']

    assert Model(foo='foo').foo == 'foo'


def test_typing_literal_field():
    from typing import Literal

    class Model(BaseModel):
        foo: Literal['foo']

    assert Model(foo='foo').foo == 'foo'


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

    class MyModel(BaseModel):
        a: InstanceOf[MyClass]
        b: Optional[InstanceOf[MyClass]]

    MyModel(a=MyClass(), b=None)
    MyModel(a=MyClass(), b=MyClass())
    with pytest.raises(ValidationError) as exc_info:
        MyModel(a=1, b=1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'test_instanceof_invalid_core_schema.<locals>.MyClass'},
            'input': 1,
            'loc': ('a',),
            'msg': 'Input should be an instance of ' 'test_instanceof_invalid_core_schema.<locals>.MyClass',
            'type': 'is_instance_of',
        },
        {
            'ctx': {'class': 'test_instanceof_invalid_core_schema.<locals>.MyClass'},
            'input': 1,
            'loc': ('b',),
            'msg': 'Input should be an instance of ' 'test_instanceof_invalid_core_schema.<locals>.MyClass',
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
            'msg': 'Predicate test_constraints_arbitrary_type.<locals>.Model.<lambda> failed',
            'input': CustomType(-1),
        },
    ]


def test_annotated_default_value() -> None:
    t = TypeAdapter(Annotated[List[int], Field(default=['1', '2'])])

    r = t.get_default_value()
    assert r is not None
    assert r.value == ['1', '2']

    # insert_assert(t.json_schema())
    assert t.json_schema() == {'type': 'array', 'items': {'type': 'integer'}, 'default': ['1', '2']}


def test_annotated_default_value_validate_default() -> None:
    t = TypeAdapter(Annotated[List[int], Field(default=['1', '2'])], config=ConfigDict(validate_default=True))

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
    for tp in (WithDefaultValue[WithAfterValidator[List[int]]], WithAfterValidator[WithDefaultValue[List[int]]]):
        t = TypeAdapter(tp, config=ConfigDict(validate_default=True))

        r = t.get_default_value()
        assert r is not None
        assert r.value == [2, 4]

        # insert_assert(t.json_schema())
        assert t.json_schema() == {'type': 'array', 'items': {'type': 'integer'}, 'default': ['1', '2']}


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


def test_enum_custom_schema() -> None:
    class MyEnum(str, Enum):
        foo = 'FOO'
        bar = 'BAR'
        baz = 'BAZ'

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source_type: Any,
            handler: GetCoreSchemaHandler,
        ) -> CoreSchema:
            # check that we can still call handler
            handler(source_type)

            # return a custom unrelated schema so we can test that
            # it gets used
            schema = core_schema.union_schema(
                [
                    core_schema.str_schema(),
                    core_schema.is_instance_schema(cls),
                ]
            )
            return core_schema.no_info_after_validator_function(
                function=lambda x: MyEnum(x.upper()) if isinstance(x, str) else x,
                schema=schema,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda x: x.value, return_schema=core_schema.int_schema()
                ),
            )

    ta = TypeAdapter(MyEnum)

    assert ta.validate_python('foo') == MyEnum.foo


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


def test_string_constraints() -> None:
    ta = TypeAdapter(
        Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True), AfterValidator(lambda x: x * 2)]
    )
    assert ta.validate_python(' ABC ') == 'abcabc'


def test_string_constraints_strict() -> None:
    ta = TypeAdapter(Annotated[str, StringConstraints(strict=False)])
    assert ta.validate_python(b'123') == '123'

    ta = TypeAdapter(Annotated[str, StringConstraints(strict=True)])
    with pytest.raises(ValidationError):
        ta.validate_python(b'123')


def test_decimal_float_precision() -> None:
    """https://github.com/pydantic/pydantic/issues/6807"""
    ta = TypeAdapter(Decimal)
    assert ta.validate_json('1.1') == Decimal('1.1')
    assert ta.validate_python(1.1) == Decimal('1.1')
    assert ta.validate_json('"1.1"') == Decimal('1.1')
    assert ta.validate_python('1.1') == Decimal('1.1')
    assert ta.validate_json('1') == Decimal('1')
    assert ta.validate_python(1) == Decimal('1')


def test_coerce_numbers_to_str_disabled_in_strict_mode() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(strict=True, coerce_numbers_to_str=True)
        value: str

    with pytest.raises(ValidationError, match='value'):
        Model.model_validate({'value': 42})
    with pytest.raises(ValidationError, match='value'):
        Model.model_validate_json('{"value": 42}')


@pytest.mark.parametrize('value_param', [True, False])
def test_coerce_numbers_to_str_raises_for_bool(value_param: bool) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)
        value: str

    with pytest.raises(ValidationError, match='value'):
        Model.model_validate({'value': value_param})
    with pytest.raises(ValidationError, match='value'):
        if value_param is True:
            Model.model_validate_json('{"value": true}')
        elif value_param is False:
            Model.model_validate_json('{"value": false}')

    @pydantic_dataclass(config=ConfigDict(coerce_numbers_to_str=True))
    class Model:
        value: str

    with pytest.raises(ValidationError, match='value'):
        Model(value=value_param)


@pytest.mark.parametrize(
    ('number', 'expected_str'),
    [
        pytest.param(42, '42', id='42'),
        pytest.param(42.0, '42.0', id='42.0'),
        pytest.param(Decimal('42.0'), '42.0', id="Decimal('42.0')"),
    ],
)
def test_coerce_numbers_to_str(number: Number, expected_str: str) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)
        value: str

    assert Model.model_validate({'value': number}).model_dump() == {'value': expected_str}


@pytest.mark.parametrize(
    ('number', 'expected_str'),
    [
        pytest.param('42', '42', id='42'),
        pytest.param('42.0', '42', id='42.0'),
        pytest.param('42.13', '42.13', id='42.13'),
    ],
)
def test_coerce_numbers_to_str_from_json(number: str, expected_str: str) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)
        value: str

    assert Model.model_validate_json(f'{{"value": {number}}}').model_dump() == {'value': expected_str}


def test_union_tags_in_errors():
    DoubledList = Annotated[List[int], AfterValidator(lambda x: x * 2)]
    StringsMap = Dict[str, str]

    adapter = TypeAdapter(Union[DoubledList, StringsMap])

    with pytest.raises(ValidationError) as exc_info:
        adapter.validate_python(['a'])

    # yuck
    assert '2 validation errors for union[function-after[<lambda>(), list[int]],dict[str,str]]' in str(exc_info)
    # the loc's are bad here:
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('function-after[<lambda>(), list[int]]', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {
            'input': ['a'],
            'loc': ('dict[str,str]',),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
        },
    ]

    tag_adapter = TypeAdapter(
        Union[Annotated[DoubledList, Tag('DoubledList')], Annotated[StringsMap, Tag('StringsMap')]]
    )
    with pytest.raises(ValidationError) as exc_info:
        tag_adapter.validate_python(['a'])

    assert '2 validation errors for union[DoubledList,StringsMap]' in str(exc_info)  # nice
    # the loc's are good here:
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('DoubledList', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {
            'input': ['a'],
            'loc': ('StringsMap',),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
        },
    ]


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
        val: Union[str, JsonValue]

    round_trip_value = json.loads(MyModel(val=True).model_dump_json())['val']
    assert round_trip_value is True, round_trip_value


def test_on_error_omit() -> None:
    OmittableInt = OnErrorOmit[int]

    class MyTypedDict(TypedDict):
        a: NotRequired[OmittableInt]
        b: NotRequired[OmittableInt]

    class Model(BaseModel):
        a_list: List[OmittableInt]
        a_dict: Dict[OmittableInt, OmittableInt]
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


def test_diff_enums_diff_configs() -> None:
    class MyEnum(str, Enum):
        A = 'a'

    class MyModel(BaseModel, use_enum_values=True):
        my_enum: MyEnum

    class OtherModel(BaseModel):
        my_enum: MyEnum

    class Model(BaseModel):
        my_model: MyModel
        other_model: OtherModel

    obj = Model.model_validate({'my_model': {'my_enum': 'a'}, 'other_model': {'my_enum': 'a'}})
    assert not isinstance(obj.my_model.my_enum, MyEnum)
    assert isinstance(obj.other_model.my_enum, MyEnum)


def test_can_serialize_deque_passed_to_sequence() -> None:
    ta = TypeAdapter(Sequence[int])
    my_dec = ta.validate_python(deque([1, 2, 3]))
    assert my_dec == deque([1, 2, 3])

    assert ta.dump_python(my_dec) == my_dec
    assert ta.dump_json(my_dec) == b'[1,2,3]'


def test_strict_enum_with_use_enum_values() -> None:
    class SomeEnum(int, Enum):
        SOME_KEY = 1

    class Foo(BaseModel):
        model_config = ConfigDict(strict=False, use_enum_values=True)
        foo: Annotated[SomeEnum, Strict(strict=True)]

    f = Foo(foo=SomeEnum.SOME_KEY)
    assert f.foo == 1

    # validation error raised bc foo field uses strict mode
    with pytest.raises(ValidationError):
        Foo(foo='1')


def test_python_re_respects_flags() -> None:
    class Model(BaseModel):
        a: Annotated[str, StringConstraints(pattern=re.compile(r'[A-Z]+', re.IGNORECASE))]

        model_config = ConfigDict(regex_engine='python-re')

    # allows lowercase letters, even though the pattern is uppercase only due to the IGNORECASE flag
    assert Model(a='abc').a == 'abc'


def test_constraints_on_str_like() -> None:
    """See https://github.com/pydantic/pydantic/issues/8577 for motivation."""

    class Foo(BaseModel):
        baz: Annotated[EmailStr, StringConstraints(to_lower=True, strip_whitespace=True)]

    assert Foo(baz=' uSeR@ExAmPlE.com  ').baz == 'user@example.com'


@pytest.mark.parametrize(
    'tp',
    [
        pytest.param(List[int], id='list'),
        pytest.param(Tuple[int, ...], id='tuple'),
        pytest.param(Set[int], id='set'),
        pytest.param(FrozenSet[int], id='frozenset'),
    ],
)
@pytest.mark.parametrize(
    ['fail_fast', 'decl'],
    [
        pytest.param(True, FailFast(), id='fail-fast-default'),
        pytest.param(True, FailFast(True), id='fail-fast-true'),
        pytest.param(False, FailFast(False), id='fail-fast-false'),
        pytest.param(False, Field(...), id='field-default'),
        pytest.param(True, Field(..., fail_fast=True), id='field-true'),
        pytest.param(False, Field(..., fail_fast=False), id='field-false'),
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
