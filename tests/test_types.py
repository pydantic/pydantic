import itertools
import math
import os
import re
import sys
import uuid
from collections import OrderedDict, deque
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    FrozenSet,
    Iterable,
    List,
    MutableSet,
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
import pytest
from dirty_equals import HasRepr
from pydantic_core._pydantic_core import PydanticCustomError, SchemaError
from typing_extensions import Annotated, Literal, TypedDict

from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    BaseModel,
    ByteSize,
    ConfigDict,
    DirectoryPath,
    EmailStr,
    Field,
    FilePath,
    FiniteFloat,
    Json,
    NameEmail,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PositiveFloat,
    PositiveInt,
    SecretBytes,
    SecretStr,
    StrictBool,
    StrictBytes,
    StrictFloat,
    StrictInt,
    StrictStr,
    ValidationError,
    conbytes,
    condecimal,
    confloat,
    confrozenset,
    conint,
    conlist,
    conset,
    constr,
)
from pydantic.decorators import field_validator
from pydantic.types import ImportString, SecretField, Strict

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


def test_constrained_bytes_too_long(ConBytesModel):
    with pytest.raises(ValidationError) as exc_info:
        ConBytesModel(v=b'this is too long')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'bytes_too_long',
            'loc': ('v',),
            'msg': 'Data should have at most 10 bytes',
            'input': b'this is too long',
            'ctx': {'max_length': 10},
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'list_type', 'loc': ('v',), 'msg': 'Input should be a valid list', 'input': 1}
    ]


def test_constrained_list_item_type_fails():
    class ConListModel(BaseModel):
        v: conlist(int) = []

    with pytest.raises(ValidationError) as exc_info:
        ConListModel(v=['a', 'b', 'c'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'too_long',
            'loc': ('v',),
            'msg': 'Set should have at most 10 items after validation, not 11',
            'input': {'4', '3', '10', '9', '5', '6', '1', '8', '0', '7', '2'},
            'ctx': {'field_type': 'Set', 'max_length': 10, 'actual_length': 11},
        }
    ]


def test_constrained_set_too_short():
    class ConSetModelMin(BaseModel):
        v: conset(int, min_length=1)

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelMin(v=[])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'too_long',
            'loc': ('v',),
            'msg': 'Set should have at most 11 items after validation, not 12',
            'input': {0, 8, 1, 9, 2, 10, 3, 7, 11, 4, 6, 5},
            'ctx': {'field_type': 'Set', 'max_length': 11, 'actual_length': 12},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=1)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'set_type', 'loc': ('v',), 'msg': 'Input should be a valid set', 'input': 1}
    ]


def test_constrained_set_item_type_fails():
    class ConSetModel(BaseModel):
        v: conset(int) = []

    with pytest.raises(ValidationError) as exc_info:
        ConSetModel(v=['a', 'b', 'c'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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

    with pytest.raises(ValidationError, match='Set should have at most 4 items after validation, not 5'):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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

    with pytest.raises(ValidationError, match='Frozenset should have at most 4 items after validation, not 5'):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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


def test_constrained_str_too_long(ConStringModel):
    with pytest.raises(ValidationError) as exc_info:
        ConStringModel(v='this is too long')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'string_too_long',
            'loc': ('v',),
            'msg': 'String should have at most 10 characters',
            'input': 'this is too long',
            'ctx': {'max_length': 10},
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'import_error',
            'loc': ('callable',),
            'msg': 'Invalid python path: "foobar" doesn\'t look like a module path',
            'input': 'foobar',
            'ctx': {'error': '"foobar" doesn\'t look like a module path'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable='os.missing')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'import_error',
            'loc': ('callable',),
            'msg': 'Invalid python path: Module "os" does not define a "missing" attribute',
            'input': 'os.missing',
            'ctx': {'error': 'Module "os" does not define a "missing" attribute'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable='os.path')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'callable_type', 'loc': ('callable',), 'msg': 'Input should be callable', 'input': os.path}
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable=[1, 2, 3])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'callable_type', 'loc': ('callable',), 'msg': 'Input should be callable', 'input': [1, 2, 3]}
    ]


def test_string_import_any():
    class PyObjectModel(BaseModel):
        thing: ImportString

    assert PyObjectModel(thing='math.cos').model_dump() == {'thing': math.cos}
    assert PyObjectModel(thing='os.path').model_dump() == {'thing': os.path}
    assert PyObjectModel(thing=[1, 2, 3]).model_dump() == {'thing': [1, 2, 3]}


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

    assert PyObjectModel(thing='math.pi').model_dump() == {'thing': pytest.approx(3.141592654)}
    with pytest.raises(ValidationError, match='type=greater_than_equal'):
        PyObjectModel(thing='math.e')


def test_decimal():
    class Model(BaseModel):
        v: Decimal

    m = Model(v='1.234')
    assert m.v == Decimal('1.234')
    assert isinstance(m.v, Decimal)
    assert m.model_dump() == {'v': Decimal('1.234')}


def test_decimal_strict():
    class Model(BaseModel):
        v: Decimal

        model_config = ConfigDict(strict=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=1.23)
    assert exc_info.value.errors() == [
        {
            'type': 'decimal_type',
            'loc': ('v',),
            'msg': 'Input should be a valid Decimal instance or decimal string in JSON',
            'input': 1.23,
        }
    ]

    v = Decimal(1.23)
    assert Model(v=v).v == v
    assert Model(v=v).model_dump() == {'v': v}


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

    return CheckModel


class BoolCastable:
    def __bool__(self) -> bool:
        return True


@pytest.mark.xfail(sys.platform.startswith('win'), reason='https://github.com/PyO3/pyo3/issues/2913', strict=False)
@pytest.mark.parametrize(
    'field,value,result',
    [
        ('bool_check', True, True),
        ('bool_check', 1, True),
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
        ('bool_check', b'\x81', ValidationError),
        ('bool_check', BoolCastable(), ValidationError),
        ('str_check', 's', 's'),
        ('str_check', '  s  ', 's'),
        ('str_check', b's', 's'),
        ('str_check', b'  s  ', 's'),
        ('str_check', 1, ValidationError),
        ('str_check', 'x' * 11, ValidationError),
        ('str_check', b'x' * 11, ValidationError),
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
        ('int_check', '1', 1),
        ('int_check', '1.9', ValidationError),
        ('int_check', b'1', 1),
        ('int_check', 12, 12),
        ('int_check', '12', 12),
        ('int_check', b'12', 12),
        ('float_check', 1, 1.0),
        ('float_check', 1.0, 1.0),
        ('float_check', '1.0', 1.0),
        ('float_check', '1', 1.0),
        ('float_check', b'1.0', 1.0),
        ('float_check', b'1', 1.0),
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'datetime_parsing',
            'loc': ('dt',),
            'msg': 'Input should be a valid datetime, month value is outside expected range of 1-12',
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'literal_error',
            'loc': ('tool',),
            'msg': 'Input should be 1 or 2',
            'input': 3,
            'ctx': {'expected': '1 or 2'},
        }
    ]


def test_int_enum_successful_for_str_int(cooking_model):
    FruitEnum, ToolEnum, CookingModel = cooking_model
    m = CookingModel(tool='2')
    assert m.tool == ToolEnum.wrench
    assert repr(m.tool) == '<ToolEnum.wrench: 2>'


def test_enum_type():
    with pytest.raises(SchemaError, match='"expected" should have length > 0'):

        class Model(BaseModel):
            my_int_enum: Enum


def test_int_enum_type():
    with pytest.raises(SchemaError, match='"expected" should have length > 0'):

        class Model(BaseModel):
            my_int_enum: IntEnum


@pytest.mark.parametrize(
    'kwargs,type_',
    [
        ({'max_length': 5}, int),
        ({'min_length': 2}, float),
        ({'frozen': True}, bool),
        ({'pattern': '^foo$'}, int),
        ({'gt': 2}, str),
        ({'lt': 5}, bytes),
        ({'ge': 2}, str),
        ({'le': 5}, bool),
        ({'gt': 0}, Callable),
        ({'gt': 0}, Callable[[int], int]),
        ({'gt': 0}, conlist(int, min_length=4)),
        ({'gt': 0}, conset(int, min_length=4)),
        ({'gt': 0}, confrozenset(int, min_length=4)),
    ],
)
def test_invalid_schema_constraints(kwargs, type_):
    with pytest.raises(SchemaError, match='Invalid Schema:\n.*\n  Extra inputs are not permitted'):

        class Foo(BaseModel):
            a: type_ = Field('foo', title='A title', description='A description', **kwargs)


def test_invalid_decimal_constraint():
    with pytest.raises(TypeError, match="'max_length' is not a valid constraint for DecimalValidator"):

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

    m = MoreStringsModel(
        str_strip_enabled='   xxx123   ',
        str_strip_disabled='   xxx123   ',
        str_regex='xxx123',
        str_min_length='12345',
        str_email='foobar@example.com  ',
        name_email='foo bar  <foobaR@example.com>',
    )
    assert m.str_strip_enabled == 'xxx123'
    assert m.str_strip_disabled == '   xxx123   '
    assert m.str_regex == 'xxx123'
    assert m.str_email == 'foobar@example.com'
    assert repr(m.name_email) == "NameEmail(name='foo bar', email='foobaR@example.com')"
    assert str(m.name_email) == 'foo bar <foobaR@example.com>'
    assert m.name_email.name == 'foo bar'
    assert m.name_email.email == 'foobaR@example.com'


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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
            'msg': (
                'value is not a valid email address: The email address contains invalid '
                'characters before the @-sign: LESS-THAN SIGN.'
            ),
            'input': 'foobar<@example.com',
            'ctx': {'reason': 'The email address contains invalid characters before the @-sign: LESS-THAN SIGN.'},
        },
        {
            'type': 'value_error',
            'loc': ('name_email',),
            'msg': (
                'value is not a valid email address: The email address contains invalid characters '
                'before the @-sign: SPACE.'
            ),
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'dict_type',
            'loc': ('v',),
            'msg': 'Input should be a valid dictionary',
            'input': [(1, 2), (3, 4)],
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, 3])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'dict_type', 'loc': ('v',), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]


@pytest.mark.parametrize(
    'value,result',
    (
        ([1, 2, '3'], [1, 2, '3']),
        ((1, 2, '3'), [1, 2, '3']),
        ((i**2 for i in range(5)), [0, 1, 4, 9, 16]),
        (deque([1, 2, 3]), [1, 2, 3]),
    ),
)
def test_list_success(value, result):
    class Model(BaseModel):
        v: list

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (123, '123', {1, 2, '3'}))
def test_list_fails(value):
    class Model(BaseModel):
        v: list

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'dict_type', 'loc': ('v',), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]


@pytest.mark.parametrize(
    'value,result',
    (
        ([1, 2, '3'], (1, 2, '3')),
        ((1, 2, '3'), (1, 2, '3')),
        ((i**2 for i in range(5)), (0, 1, 4, 9, 16)),
        (deque([1, 2, 3]), (1, 2, 3)),
    ),
)
def test_tuple_success(value, result):
    class Model(BaseModel):
        v: tuple

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (123, '123', {1, 2, '3'}))
def test_tuple_fails(value):
    class Model(BaseModel):
        v: tuple

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    assert exc_info.value.errors() == exc


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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'set_type', 'loc': ('v',), 'msg': 'Input should be a valid set', 'input': value}
    ]


def test_list_type_fails():
    class Model(BaseModel):
        v: List[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'list_type', 'loc': ('v',), 'msg': 'Input should be a valid list', 'input': '123'}
    ]


def test_set_type_fails():
    class Model(BaseModel):
        v: Set[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'iterable_type', 'loc': ('it',), 'msg': 'Input should be iterable', 'input': 3}
    ]


def test_invalid_iterable():
    class Model(BaseModel):
        it: Iterable[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(it=3)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'iterable_type', 'loc': ('it',), 'msg': 'Input should be iterable', 'input': 3}
    ]


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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
                    'msg': 'Input should be a valid number, unable to parse string as an number',
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
                    'msg': 'Input should be a valid number, unable to parse string as an number',
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
    assert exc_info.value.errors() == errors


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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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


def test_finite_float_validation():
    class Model(BaseModel):
        a: float = None

    assert Model(a=float('inf')).a == float('inf')
    assert Model(a=float('-inf')).a == float('-inf')
    assert math.isnan(Model(a=float('nan')).a)


@pytest.mark.parametrize('value', [float('inf'), float('-inf'), float('nan')])
def test_finite_float_validation_error(value):
    class Model(BaseModel):
        a: FiniteFloat

    assert Model(a=42).a == 42
    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
        pear = 'pear'
        banana = 'banana'

    class Model(BaseModel):
        v: StrictStr

    assert Model(v='foobar').v == 'foobar'

    msg = r'Input should be a string, not an instance of a subclass of str \[type=string_sub_type,'
    with pytest.raises(ValidationError, match=msg):
        Model(v=FruitEnum.banana)

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


def test_strict_float():
    class Model(BaseModel):
        v: StrictFloat

    assert Model(v=3.14159).v == 3.14159
    assert Model(v=123456).v == 123456

    with pytest.raises(ValidationError, match=r'Input should be a valid number \[type=float_type,'):
        Model(v='3.14159')


def test_bool_unhashable_fails():
    class Model(BaseModel):
        v: bool

    with pytest.raises(ValidationError) as exc_info:
        Model(v={})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'bool_type', 'loc': ('v',), 'msg': 'Input should be a valid boolean', 'input': {}}
    ]


def test_uuid_error():
    class Model(BaseModel):
        v: UUID

    with pytest.raises(ValidationError) as exc_info:
        Model(v='ebcdab58-6eb8-46fb-a190-d07a3')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'uuid_type',
            'loc': ('v',),
            'msg': 'Input should be a valid UUID, string, or bytes',
            'input': 'ebcdab58-6eb8-46fb-a190-d07a3',
        }
    ]

    with pytest.raises(ValidationError, match='Input should be a valid UUID, string, or bytes'):
        Model(v=None)


@pytest.mark.xfail(sys.platform.startswith('win'), reason='https://github.com/PyO3/pyo3/issues/2913', strict=False)
def test_uuid_validation():
    class UUIDModel(BaseModel):
        a: UUID1
        b: UUID3
        c: UUID4
        d: UUID5

    a = uuid.uuid1()
    b = uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
    c = uuid.uuid4()
    d = uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')

    m = UUIDModel(a=a, b=b, c=c, d=d)
    assert m.model_dump() == {'a': a, 'b': b, 'c': c, 'd': d}

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=d, b=c, c=b, d=a)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'uuid_version',
            'loc': ('a',),
            'msg': 'uuid version 1 expected',
            'input': d,
            'ctx': {'required_version': 1},
        },
        {
            'type': 'uuid_version',
            'loc': ('b',),
            'msg': 'uuid version 3 expected',
            'input': c,
            'ctx': {'required_version': 3},
        },
        {
            'type': 'uuid_version',
            'loc': ('c',),
            'msg': 'uuid version 4 expected',
            'input': b,
            'ctx': {'required_version': 4},
        },
        {
            'type': 'uuid_version',
            'loc': ('d',),
            'msg': 'uuid version 5 expected',
            'input': a,
            'ctx': {'required_version': 5},
        },
    ]


def test_uuid_strict() -> None:
    class UUIDModel(BaseModel):
        a: UUID1
        b: UUID3
        c: UUID4
        d: UUID5

        model_config = ConfigDict(strict=True)

    a = uuid.UUID('7fb48116-ca6b-11ed-a439-3274d3adddac')  # uuid1
    b = uuid.UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e')  # uuid3
    c = uuid.UUID('260d1600-3680-4f4f-a968-f6fa622ffd8d')  # uuid4
    d = uuid.UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d')  # uuid5

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=str(a), b=str(b), c=str(c), d=str(d))
    assert exc_info.value.errors() == [
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
    ]

    m = UUIDModel(a=a, b=b, c=c, d=d)
    assert isinstance(m.a, type(a)) and m.a == a
    assert isinstance(m.b, type(b)) and m.b == b
    assert isinstance(m.c, type(c)) and m.c == c
    assert isinstance(m.d, type(d)) and m.d == d


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
                    'ctx': {'gt': 42.24},
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
                        'lt': 42.24,
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
                        'ge': 42.24,
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
                        'le': 42.24,
                    },
                }
            ],
        ),
        (dict(max_digits=2, decimal_places=2), Decimal('0.99'), Decimal('0.99')),
        (
            dict(max_digits=2, decimal_places=1),
            Decimal('0.99'),
            [
                {
                    'type': 'decimal_max_places',
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 1 decimal places',
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
                    'msg': 'ensure that there are no more than 2 digits before the decimal point',
                    'type': 'decimal_whole_digits',
                    'input': Decimal('999'),
                    'ctx': {'whole_digits': 2},
                }
            ],
        ),
        (dict(max_digits=4, decimal_places=1), Decimal('999'), Decimal('999')),
        (dict(max_digits=20, decimal_places=2), Decimal('742403889818000000'), Decimal('742403889818000000')),
        (dict(max_digits=20, decimal_places=2), Decimal('7.42403889818E+17'), Decimal('7.42403889818E+17')),
        (
            dict(max_digits=20, decimal_places=2),
            Decimal('7424742403889818000000'),
            [
                {
                    'type': 'decimal_max_digits',
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 20 digits in total',
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
                    'msg': 'ensure that there are no more than 2 decimal places',
                    'input': Decimal('7.304'),
                    'ctx': {'decimal_places': 2},
                }
            ],
        ),
        (dict(max_digits=5, decimal_places=5), Decimal('70E-5'), Decimal('70E-5')),
        (
            dict(max_digits=5, decimal_places=5),
            Decimal('70E-6'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 5 digits in total',
                    'type': 'decimal_max_digits',
                    'input': Decimal('0.000070'),
                    'ctx': {'max_digits': 5},
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
                    'type': 'decimal_multiple_of',
                    'loc': ('foo',),
                    'msg': 'Input should be a multiple of 5',
                    'input': Decimal('42'),
                    'ctx': {
                        'multiple_of': Decimal('5'),
                    },
                }
            ],
        ),
    ],
)
@pytest.mark.parametrize('mode', ['Field', 'condecimal'])
def test_decimal_validation(mode, type_args, value, result):
    if mode == 'Field':

        class Model(BaseModel):
            foo: Decimal = Field(**type_args)

    else:

        class Model(BaseModel):
            foo: condecimal(**type_args)

    if not isinstance(result, Decimal):
        with pytest.raises(ValidationError) as exc_info:
            m = Model(foo=value)
            print(f'unexpected result: {m!r}')
        # debug(exc_info.value.errors())
        # dirty_equals.AnyThing() doesn't work with Decimal on PyPy, hence this hack
        errors = exc_info.value.errors()
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
    with pytest.raises(ValueError, match='allow_inf_nan=True cannot be used with max_digits or decimal_places'):

        class Model(BaseModel):
            v: condecimal(allow_inf_nan=True, max_digits=4)


@pytest.mark.parametrize('value,result', (('/test/path', Path('/test/path')), (Path('/test/path'), Path('/test/path'))))
def test_path_validation_success(value, result):
    class Model(BaseModel):
        foo: Path

    assert Model(foo=value).foo == result


def test_path_validation_fails():
    class Model(BaseModel):
        foo: Path

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=123)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'path_type', 'loc': ('foo',), 'msg': 'Input is not a valid path', 'input': 123}
    ]


def test_path_validation_strict():
    class Model(BaseModel):
        foo: Path

        model_config = ConfigDict(strict=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(foo='/test/path')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    assert exc_info.value.errors() == [
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
    assert exc_info.value.errors() == [
        {
            'type': 'path_not_directory',
            'loc': ('foo',),
            'msg': 'Path does not point to a directory',
            'input': value,
        }
    ]


def test_number_gt():
    class Model(BaseModel):
        a: conint(gt=-1) = 0

    assert Model(a=0).model_dump() == {'a': 0}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-1)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'missing', 'loc': ('json_obj', 'b'), 'msg': 'Field required', 'input': {'a': 1, 'c': [2, 3]}}
    ]


def test_invalid_detailed_json_type_error():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = '["a", "b", "c"]'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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


@pytest.mark.parametrize('pattern_type', [re.Pattern, Pattern])
def test_pattern(pattern_type):
    class Foobar(BaseModel):
        pattern: pattern_type

    f = Foobar(pattern=r'^whatev.r\d$')
    assert f.pattern.__class__.__name__ == 'Pattern'
    # check it's really a proper pattern
    assert f.pattern.match('whatever1')
    assert not f.pattern.match(' whatever1')

    # Check that pre-compiled patterns are accepted unchanged
    p = re.compile(r'^whatev.r\d$')
    f2 = Foobar(pattern=p)
    assert f2.pattern is p

    # assert Foobar.model_json_schema() == {
    #     'type': 'object',
    #     'title': 'Foobar',
    #     'properties': {'pattern': {'type': 'string', 'format': 'regex', 'title': 'Pattern'}},
    #     'required': ['pattern'],
    # }


@pytest.mark.parametrize('pattern_type', [re.Pattern, Pattern])
def test_pattern_error(pattern_type):
    class Foobar(BaseModel):
        pattern: pattern_type

    with pytest.raises(ValidationError) as exc_info:
        Foobar(pattern='[xx')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'pattern_regex',
            'loc': ('pattern',),
            'msg': 'Input should be a valid regular expression',
            'input': '[xx',
        }
    ]


def test_secretstr():
    class Foobar(BaseModel):
        password: SecretStr
        empty_password: SecretStr

    # Initialize the model.
    f = Foobar(password='1234', empty_password='')

    # Assert correct types.
    assert f.password.__class__.__name__ == 'SecretStr'
    assert f.empty_password.__class__.__name__ == 'SecretStr'

    # Assert str and repr are correct.
    assert str(f.password) == '**********'
    assert str(f.empty_password) == ''
    assert repr(f.password) == "SecretStr('**********')"
    assert repr(f.empty_password) == "SecretStr('')"

    # Assert retrieval of secret value is correct
    assert f.password.get_secret_value() == '1234'
    assert f.empty_password.get_secret_value() == ''


def test_secretstr_is_secret_field():
    assert issubclass(SecretStr, SecretField)


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


def test_secretstr_is_hashable():
    assert type(hash(SecretStr('secret'))) is int


def test_secretstr_error():
    class Foobar(BaseModel):
        password: SecretStr

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=[6, 23, 'abc'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'string_type',
            'loc': ('password',),
            'msg': 'Input should be a valid string',
            'input': [6, 23, 'abc'],
        }
    ]


def test_secret_str_min_max_length():
    class Foobar(BaseModel):
        password: SecretStr = Field(min_length=6, max_length=10)

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password='')

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'string_too_short',
            'loc': ('password',),
            'msg': 'String should have at least 6 characters',
            'input': '',
            'ctx': {'min_length': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password='1' * 20)

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'string_too_long',
            'loc': ('password',),
            'msg': 'String should have at most 10 characters',
            'input': '11111111111111111111',
            'ctx': {'max_length': 10},
        }
    ]

    value = '1' * 8
    assert Foobar(password=value).password.get_secret_value() == value


def test_secretbytes():
    class Foobar(BaseModel):
        password: SecretBytes
        empty_password: SecretBytes

    # Initialize the model.
    f = Foobar(password=b'wearebytes', empty_password=b'')

    # Assert correct types.
    assert f.password.__class__.__name__ == 'SecretBytes'
    assert f.empty_password.__class__.__name__ == 'SecretBytes'

    # Assert str and repr are correct.
    assert str(f.password) == "b'**********'"
    assert str(f.empty_password) == "b''"
    assert repr(f.password) == "SecretBytes(b'**********')"
    assert repr(f.empty_password) == "SecretBytes(b'')"

    # Assert retrieval of secret value is correct
    assert f.password.get_secret_value() == b'wearebytes'
    assert f.empty_password.get_secret_value() == b''

    # Assert that SecretBytes is equal to SecretBytes if the secret is the same.
    assert f == f.model_copy()
    copied_with_changes = f.model_copy()
    copied_with_changes.password = SecretBytes(b'4321')
    assert f != copied_with_changes


def test_secretbytes_is_secret_field():
    assert issubclass(SecretBytes, SecretField)


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


def test_secretbytes_is_hashable():
    assert type(hash(SecretBytes(b'secret'))) is int


def test_secretbytes_error():
    class Foobar(BaseModel):
        password: SecretBytes

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=[6, 23, 'abc'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'bytes_too_short',
            'loc': ('password',),
            'msg': 'Data should have at least 6 bytes',
            'input': b'',
            'ctx': {'min_length': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=b'1' * 20)

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'bytes_too_long',
            'loc': ('password',),
            'msg': 'Data should have at most 10 bytes',
            'input': b'11111111111111111111',
            'ctx': {'max_length': 10},
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'literal_error',
            'loc': ('a_or_b',),
            'msg': "Input should be 'a' or 'b'",
            'input': 'c',
            'ctx': {'expected': "'a' or 'b'"},
        }
    ]


def test_unsupported_field_type():
    with pytest.raises(TypeError, match=r'Unable to generate pydantic-core schema MutableSet'):

        class UnsupportedModel(BaseModel):
            unsupported: MutableSet[int]


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
    'input_value,output,human_bin,human_dec',
    (
        ('1', 1, '1B', '1B'),
        ('1.0', 1, '1B', '1B'),
        ('1b', 1, '1B', '1B'),
        ('1.5 KB', int(1.5e3), '1.5KiB', '1.5KB'),
        ('1.5 K', int(1.5e3), '1.5KiB', '1.5KB'),
        ('1.5 MB', int(1.5e6), '1.4MiB', '1.5MB'),
        ('1.5 M', int(1.5e6), '1.4MiB', '1.5MB'),
        ('5.1kib', 5222, '5.1KiB', '5.2KB'),
        ('6.2EiB', 7148113328562451456, '6.2EiB', '7.1EB'),
    ),
)
def test_bytesize_conversions(input_value, output, human_bin, human_dec):
    class Model(BaseModel):
        size: ByteSize

    m = Model(size=input_value)

    assert m.size == output

    assert m.size.human_readable() == human_bin
    assert m.size.human_readable(decimal=True) == human_dec


def test_bytesize_to():
    class Model(BaseModel):
        size: ByteSize

    m = Model(size='1GiB')

    assert m.size.to('MiB') == pytest.approx(1024)
    assert m.size.to('MB') == pytest.approx(1073.741824)
    assert m.size.to('TiB') == pytest.approx(0.0009765625)


def test_bytesize_raises():
    class Model(BaseModel):
        size: ByteSize

    with pytest.raises(ValidationError, match='parse value'):
        Model(size='d1MB')

    with pytest.raises(ValidationError, match='byte unit'):
        Model(size='1LiB')

    # 1Gi is not a valid unit unlike 1G
    with pytest.raises(ValidationError, match='byte unit'):
        Model(size='1Gi')

    m = Model(size='1MB')
    with pytest.raises(PydanticCustomError, match='byte unit'):
        m.size.to('bad_unit')


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
            float,
            {1, 2, 3},
            {
                'type': 'list_type',
                'loc': ('v',),
                'msg': 'Input should be a valid list',
                'input': {1, 2, 3},
            },
        ),
        (
            float,
            frozenset((1, 2, 3)),
            {
                'type': 'list_type',
                'loc': ('v',),
                'msg': 'Input should be a valid list',
                'input': frozenset((1, 2, 3)),
            },
        ),
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
    # debug(exc_info.value.errors())
    assert len(exc_info.value.errors()) == 1
    assert expected_error == exc_info.value.errors()[0]


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


@pytest.mark.parametrize('value_type', (None, type(None), None.__class__, Literal[None]))
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

    # assert Model.model_json_schema() == {
    #     'title': 'Model',
    #     'type': 'object',
    #     'properties': {
    #         'my_none': {'title': 'My None', 'type': 'null'},
    #         'my_none_list': {
    #             'title': 'My None List',
    #             'type': 'array',
    #             'items': {'type': 'null'},
    #         },
    #         'my_none_dict': {
    #             'title': 'My None Dict',
    #             'type': 'object',
    #             'additionalProperties': {'type': 'null'},
    #         },
    #         'my_json_none': {'title': 'My Json None', 'type': 'null'},
    #     },
    #     'required': ['my_none', 'my_none_list', 'my_none_dict', 'my_json_none'],
    # }

    with pytest.raises(ValidationError) as exc_info:
        Model(
            my_none='qwe',
            my_none_list=[1, None, 'qwe'],
            my_none_dict={'a': 1, 'b': None},
            my_json_none='"a"',
        )
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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


def test_default_union_types():
    class DefaultModel(BaseModel):
        v: Union[int, bool, str]

    # do it this way since `1 == True`
    assert repr(DefaultModel(v=True).v) == 'True'
    assert repr(DefaultModel(v=1).v) == '1'
    assert repr(DefaultModel(v='1').v) == "'1'"

    # assert DefaultModel.model_json_schema() == {
    #     'title': 'DefaultModel',
    #     'type': 'object',
    #     'properties': {'v': {'title': 'V', 'anyOf': [{'type': t} for t in ('integer', 'boolean', 'string')]}},
    #     'required': ['v'],
    # }


def test_default_union_class():
    class A(BaseModel):
        x: str

    class B(BaseModel):
        x: str

    class Model(BaseModel):
        y: Union[A, B]

    assert isinstance(Model(y=A(x='a')).y, A)
    assert isinstance(Model(y=B(x='b')).y, B)


def test_union_subclass():
    class MyStr(str):
        ...

    class Model(BaseModel):
        x: Union[int, str]

    # see https://github.com/pydantic/pydantic-core/pull/294, since subclasses are no-longer allowed as valid
    # inputs to strict-string, this doesn't work
    assert Model(x=MyStr('1')).x == 1


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
    # insert_assert(e.value.errors())
    assert e.value.errors() == [
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
        pass

    class Model(BaseModel):
        field: GenericList[int]

    model = Model(field=['1', '2'])
    assert model.field == [1, 2]
    assert isinstance(model.field, GenericList)

    with pytest.raises(ValidationError) as exc_info:
        Model(field=['a'])
    assert exc_info.value.errors() == [
        {
            'input': 'a',
            'loc': ('field', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]
