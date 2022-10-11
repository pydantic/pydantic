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
    Annotated,
    Any,
    Callable,
    Deque,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    MutableSet,
    NewType,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
    Union,
)
from uuid import UUID

import annotated_types
import pytest
from dirty_equals import HasRepr
from pydantic_core._pydantic_core import SchemaError
from typing_extensions import Literal, TypedDict

from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    BaseModel,
    ByteSize,
    ConfigError,
    DirectoryPath,
    EmailStr,
    Field,
    FilePath,
    FiniteFloat,
    FutureDate,
    Json,
    NameEmail,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PastDate,
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
    create_model,
    errors,
    validator,
)
from pydantic.types import ImportString, SecretField, Strict

try:
    import email_validator
except ImportError:
    email_validator = None


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
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[kind=str_type,'):
        Model(v=b'fo')


def test_constrained_bytes_too_long(ConBytesModel):
    with pytest.raises(ValidationError) as exc_info:
        ConBytesModel(v=b'this is too long')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': ['v'],
            'message': 'Data should have at most 10 bytes',
            'input_value': b'this is too long',
            'context': {'max_length': 10},
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
            'kind': 'too_long',
            'loc': ['v'],
            'message': 'List should have at most 10 items after validation, not 11',
            'input_value': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
            'context': {'field_type': 'List', 'max_length': 10, 'actual_length': 11},
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
            'kind': 'too_short',
            'loc': ['v'],
            'message': 'List should have at least 1 item after validation, not 0',
            'input_value': [],
            'context': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_constrained_list_optional():
    class Model(BaseModel):
        req: Optional[conlist(str, min_length=1)]
        opt: Optional[conlist(str, min_length=1)] = None

    assert Model(req=None).dict() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).dict() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=[], opt=[])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_short',
            'loc': ['req'],
            'message': 'List should have at least 1 item after validation, not 0',
            'input_value': [],
            'context': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        },
        {
            'kind': 'too_short',
            'loc': ['opt'],
            'message': 'List should have at least 1 item after validation, not 0',
            'input_value': [],
            'context': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req=['a'], opt=['a']).dict() == {'req': ['a'], 'opt': ['a']}


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
            'kind': 'too_short',
            'loc': ['v'],
            'message': 'List should have at least 7 items after validation, not 6',
            'input_value': [0, 1, 2, 3, 4, 5],
            'context': {'field_type': 'List', 'min_length': 7, 'actual_length': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConListModelBoth(v=list(range(12)))
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': ['v'],
            'message': 'List should have at most 11 items after validation, not 12',
            'input_value': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'context': {'field_type': 'List', 'max_length': 11, 'actual_length': 12},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConListModelBoth(v=1)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'list_type', 'loc': ['v'], 'message': 'Input should be a valid list/array', 'input_value': 1}
    ]


def test_constrained_list_item_type_fails():
    class ConListModel(BaseModel):
        v: conlist(int) = []

    with pytest.raises(ValidationError) as exc_info:
        ConListModel(v=['a', 'b', 'c'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['v', 0],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'a',
        },
        {
            'kind': 'int_parsing',
            'loc': ['v', 1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'b',
        },
        {
            'kind': 'int_parsing',
            'loc': ['v', 2],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'c',
        },
    ]


def test_conlist():
    class Model(BaseModel):
        foo: List[int] = Field(..., min_length=2, max_length=4)
        bar: conlist(str, min_length=1, max_length=4) = None

    assert Model(foo=[1, 2], bar=['spoon']).dict() == {'foo': [1, 2], 'bar': ['spoon']}

    msg = r'List should have at least 2 items after validation, not 1 \[kind=too_short,'
    with pytest.raises(ValidationError, match=msg):
        Model(foo=[1])

    msg = r'List should have at most 4 items after validation, not 5 \[kind=too_long,'
    with pytest.raises(ValidationError, match=msg):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['foo', 1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'x',
        },
        {
            'kind': 'int_parsing',
            'loc': ['foo', 2],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'list_type', 'loc': ['foo'], 'message': 'Input should be a valid list/array', 'input_value': 1}
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
            'kind': 'too_long',
            'loc': ['v'],
            'message': 'Set should have at most 10 items after validation, not 11',
            'input_value': {'4', '3', '10', '9', '5', '6', '1', '8', '0', '7', '2'},
            'context': {'field_type': 'Set', 'max_length': 10, 'actual_length': 11},
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
            'kind': 'too_short',
            'loc': ['v'],
            'message': 'Set should have at least 1 item after validation, not 0',
            'input_value': [],
            'context': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_constrained_set_optional():
    class Model(BaseModel):
        req: Optional[conset(str, min_length=1)]
        opt: Optional[conset(str, min_length=1)] = None

    assert Model(req=None).dict() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).dict() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=set(), opt=set())
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_short',
            'loc': ['req'],
            'message': 'Set should have at least 1 item after validation, not 0',
            'input_value': set(),
            'context': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        },
        {
            'kind': 'too_short',
            'loc': ['opt'],
            'message': 'Set should have at least 1 item after validation, not 0',
            'input_value': set(),
            'context': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req={'a'}, opt={'a'}).dict() == {'req': {'a'}, 'opt': {'a'}}


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
            'kind': 'too_short',
            'loc': ['v'],
            'message': 'Set should have at least 7 items after validation, not 6',
            'input_value': {0, 1, 2, 3, 4, 5},
            'context': {'field_type': 'Set', 'min_length': 7, 'actual_length': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=set(range(12)))
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': ['v'],
            'message': 'Set should have at most 11 items after validation, not 12',
            'input_value': {0, 8, 1, 9, 2, 10, 3, 7, 11, 4, 6, 5},
            'context': {'field_type': 'Set', 'max_length': 11, 'actual_length': 12},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=1)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'set_type', 'loc': ['v'], 'message': 'Input should be a valid set', 'input_value': 1}
    ]


def test_constrained_set_item_type_fails():
    class ConSetModel(BaseModel):
        v: conset(int) = []

    with pytest.raises(ValidationError) as exc_info:
        ConSetModel(v=['a', 'b', 'c'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['v', 0],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'a',
        },
        {
            'kind': 'int_parsing',
            'loc': ['v', 1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'b',
        },
        {
            'kind': 'int_parsing',
            'loc': ['v', 2],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'c',
        },
    ]


def test_conset():
    class Model(BaseModel):
        foo: Set[int] = Field(..., min_length=2, max_length=4)
        bar: conset(str, min_length=1, max_length=4) = None

    assert Model(foo=[1, 2], bar=['spoon']).dict() == {'foo': {1, 2}, 'bar': {'spoon'}}

    assert Model(foo=[1, 1, 1, 2, 2], bar=['spoon']).dict() == {'foo': {1, 2}, 'bar': {'spoon'}}

    with pytest.raises(ValidationError, match='Set should have at least 2 items after validation, not 1'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='Set should have at most 4 items after validation, not 5'):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['foo', 1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'x',
        },
        {
            'kind': 'int_parsing',
            'loc': ['foo', 2],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'set_type', 'loc': ['foo'], 'message': 'Input should be a valid set', 'input_value': 1}
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
    assert m.dict() == {'foo': {1, 2}, 'bar': {'spoon'}}
    assert isinstance(m.foo, frozenset)
    assert isinstance(m.bar, frozenset)

    assert Model(foo=[1, 1, 1, 2, 2], bar=['spoon']).dict() == {'foo': {1, 2}, 'bar': {'spoon'}}

    with pytest.raises(ValidationError, match='Frozenset should have at least 2 items after validation, not 1'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='Frozenset should have at most 4 items after validation, not 5'):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['foo', 1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'x',
        },
        {
            'kind': 'int_parsing',
            'loc': ['foo', 2],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'frozen_set_type', 'loc': ['foo'], 'message': 'Input should be a valid frozenset', 'input_value': 1}
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

    assert Model(req=None).dict() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).dict() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=frozenset(), opt=frozenset())
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_short',
            'loc': ['req'],
            'message': 'Frozenset should have at least 1 item after validation, not 0',
            'input_value': frozenset(),
            'context': {'field_type': 'Frozenset', 'min_length': 1, 'actual_length': 0},
        },
        {
            'kind': 'too_short',
            'loc': ['opt'],
            'message': 'Frozenset should have at least 1 item after validation, not 0',
            'input_value': frozenset(),
            'context': {'field_type': 'Frozenset', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req={'a'}, opt={'a'}).dict() == {'req': {'a'}, 'opt': {'a'}}


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
            'kind': 'too_long',
            'loc': ['v'],
            'message': 'String should have at most 10 characters',
            'input_value': 'this is too long',
            'context': {'max_length': 10},
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
            'kind': 'too_long',
            'loc': ['v'],
            'message': 'String should have at most 0 characters',
            'input_value': 'qwe',
            'context': {'max_length': 0},
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
            'kind': 'import_error',
            'loc': ['callable'],
            'message': 'Invalid python path: "foobar" doesn\'t look like a module path',
            'input_value': 'foobar',
            'context': {'error': '"foobar" doesn\'t look like a module path'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable='os.missing')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'import_error',
            'loc': ['callable'],
            'message': 'Invalid python path: Module "os" does not define a "missing" attribute',
            'input_value': 'os.missing',
            'context': {'error': 'Module "os" does not define a "missing" attribute'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable='os.path')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'callable_type', 'loc': ['callable'], 'message': 'Input should be callable', 'input_value': os.path}
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(callable=[1, 2, 3])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'callable_type', 'loc': ['callable'], 'message': 'Input should be callable', 'input_value': [1, 2, 3]}
    ]


def test_string_import_any():
    class PyObjectModel(BaseModel):
        thing: ImportString

    assert PyObjectModel(thing='math.cos').dict() == {'thing': math.cos}
    assert PyObjectModel(thing='os.path').dict() == {'thing': os.path}
    assert PyObjectModel(thing=[1, 2, 3]).dict() == {'thing': [1, 2, 3]}


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

    assert PyObjectModel(thing='math.pi').dict() == {'thing': pytest.approx(3.141592654)}
    with pytest.raises(ValidationError, match='kind=greater_than_equal'):
        PyObjectModel(thing='math.e')


def test_decimal():
    class Model(BaseModel):
        v: Decimal

    m = Model(v='1.234')
    assert m.v == Decimal('1.234')
    assert isinstance(m.v, Decimal)
    assert m.dict() == {'v': Decimal('1.234')}


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
        ('decimal_check', b'42.24', Decimal('42.24')),
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
        assert CheckModel(**kwargs).dict()[field] == result


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
            'kind': 'too_long',
            'loc': ['str_check'],
            'message': 'String should have at most 10 characters',
            'input_value': 'x' * 150,
            'context': {'max_length': 10},
        }
    ]


def test_string_too_short(StrModel):
    with pytest.raises(ValidationError) as exc_info:
        StrModel(str_check='x')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_short',
            'loc': ['str_check'],
            'message': 'String should have at least 5 characters',
            'input_value': 'x',
            'context': {'min_length': 5},
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
            'kind': 'datetime_parsing',
            'loc': ['dt'],
            'message': 'Input should be a valid datetime, month value is outside expected range of 1-12',
            'input_value': '2017-13-05T19:47:07',
            'context': {'error': 'month value is outside expected range of 1-12'},
        },
        {
            'kind': 'date_from_datetime_parsing',
            'loc': ['date_'],
            'message': 'Input should be a valid date or datetime, invalid character in year',
            'input_value': 'XX1494012000',
            'context': {'error': 'invalid character in year'},
        },
        {
            'kind': 'time_parsing',
            'loc': ['time_'],
            'message': 'Input should be in a valid time format, hour value is outside expected range of 0-23',
            'input_value': '25:20:30.400',
            'context': {'error': 'hour value is outside expected range of 0-23'},
        },
        {
            'kind': 'time_delta_parsing',
            'loc': ['duration'],
            'message': 'Input should be a valid timedelta, unexpected extra characters at the end of the input',
            'input_value': '15:30.0001broken',
            'context': {'error': 'unexpected extra characters at the end of the input'},
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
            'kind': 'literal_error',
            'loc': ['tool'],
            'message': 'Input should be one of: 1, 2',
            'input_value': 3,
            'context': {'expected': '1, 2'},
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


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_string_success():
    class MoreStringsModel(BaseModel):
        str_strip_enabled: constr(strip_whitespace=True)
        str_strip_disabled: constr(strip_whitespace=False)
        str_regex: constr(pattern=r'^xxx\d{3}$') = ...  # noqa: F722
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
        str_regex: constr(pattern=r'^xxx\d{3}$') = ...  # noqa: F722
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
            'kind': 'str_pattern_mismatch',
            'loc': ['str_regex'],
            'message': "String should match pattern '^xxx\\d{3}$'",
            'input_value': 'xxx123xxx',
            'context': {'pattern': '^xxx\\d{3}$'},
        },
        {
            'kind': 'too_short',
            'loc': ['str_min_length'],
            'message': 'String should have at least 5 characters',
            'input_value': '1234',
            'context': {'min_length': 5},
        },
        {
            'kind': 'value_error',
            'loc': ['str_email'],
            'message': (
                'value is not a valid email address: The email address contains invalid '
                'characters before the @-sign: LESS-THAN SIGN.'
            ),
            'input_value': 'foobar<@example.com',
            'context': {'reason': 'The email address contains invalid characters before the @-sign: LESS-THAN SIGN.'},
        },
        {
            'kind': 'value_error',
            'loc': ['name_email'],
            'message': (
                'value is not a valid email address: The email address contains invalid characters '
                'before the @-sign: SPACE.'
            ),
            'input_value': 'foobar @example.com',
            'context': {'reason': 'The email address contains invalid characters before the @-sign: SPACE.'},
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
            'kind': 'dict_type',
            'loc': ['v'],
            'message': 'Input should be a valid dictionary',
            'input_value': [(1, 2), (3, 4)],
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, 3])
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'dict_type', 'loc': ['v'], 'message': 'Input should be a valid dictionary', 'input_value': [1, 2, 3]}
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
            'kind': 'list_type',
            'loc': ['v'],
            'message': 'Input should be a valid list/array',
            'input_value': value,
        }
    ]


@pytest.mark.xfail(reason='todo')
def test_ordered_dict():
    class Model(BaseModel):
        v: OrderedDict

    assert Model(v=OrderedDict([(1, 10), (2, 20)])).v == OrderedDict([(1, 10), (2, 20)])
    assert Model(v={1: 10, 2: 20}).v in (OrderedDict([(1, 10), (2, 20)]), OrderedDict([(2, 20), (1, 10)]))
    assert Model(v=[(1, 2), (3, 4)]).v == OrderedDict([(1, 2), (3, 4)])

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, 3])
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'}]


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
        {'kind': 'tuple_type', 'loc': ['v'], 'message': 'Input should be a valid tuple', 'input_value': value}
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
            [{'kind': 'str_type', 'loc': ['v', 2], 'message': 'Input should be a valid string', 'input_value': [1, 2]}],
        ),
        (
            ('a', 'b', [1, 2], 'c', [3, 4]),
            str,
            [
                {
                    'kind': 'str_type',
                    'loc': ['v', 2],
                    'message': 'Input should be a valid string',
                    'input_value': [1, 2],
                },
                {
                    'kind': 'str_type',
                    'loc': ['v', 4],
                    'message': 'Input should be a valid string',
                    'input_value': [3, 4],
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
        {'kind': 'set_type', 'loc': ['v'], 'message': 'Input should be a valid set', 'input_value': value}
    ]


def test_list_type_fails():
    class Model(BaseModel):
        v: List[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'list_type', 'loc': ['v'], 'message': 'Input should be a valid list/array', 'input_value': '123'}
    ]


def test_set_type_fails():
    class Model(BaseModel):
        v: Set[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'set_type', 'loc': ['v'], 'message': 'Input should be a valid set', 'input_value': '123'}
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

    assert repr(m.it).startswith('<generator object validate_yield')

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
            'kind': 'int_parsing',
            'loc': [],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'f',
        }
    ]


def test_iterable_any():
    class Model(BaseModel):
        it: Iterable[Any]

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
        {'kind': 'iterable_type', 'loc': ['it'], 'message': 'Input should be a valid iterable', 'input_value': 3}
    ]


def test_invalid_iterable():
    class Model(BaseModel):
        it: Iterable[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(it=3)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'iterable_type', 'loc': ['it'], 'message': 'Input should be a valid iterable', 'input_value': 3}
    ]


def test_infinite_iterable_validate_first():
    class Model(BaseModel):
        it: Iterable[int]
        b: int

        @validator('it')
        def infinite_first_int(cls, it, **kwargs):
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
            'kind': 'int_parsing',
            'loc': ['it'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'f',
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
            'kind': 'is_instance_of',
            'loc': ['v'],
            'message': 'Input should be an instance of Sequence',
            'input_value': gen,
            'context': {'class': 'Sequence'},
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
                    'kind': 'int_parsing',
                    'loc': ['v', 1],
                    'message': 'Input should be a valid integer, unable to parse string as an integer',
                    'input_value': 'a',
                },
            ],
        ),
        (
            int,
            (1, 2, 'a'),
            [
                {
                    'kind': 'int_parsing',
                    'loc': ['v', 2],
                    'message': 'Input should be a valid integer, unable to parse string as an integer',
                    'input_value': 'a',
                },
            ],
        ),
        (
            float,
            ('a', 2.2, 3.3),
            [
                {
                    'kind': 'float_parsing',
                    'loc': ['v', 0],
                    'message': 'Input should be a valid number, unable to parse string as an number',
                    'input_value': 'a',
                },
            ],
        ),
        (
            float,
            (1.1, 2.2, 'a'),
            [
                {
                    'kind': 'float_parsing',
                    'loc': ['v', 2],
                    'message': 'Input should be a valid number, unable to parse string as an number',
                    'input_value': 'a',
                },
            ],
        ),
        (
            float,
            {1.0, 2.0, 3.0},
            [
                {
                    'kind': 'is_instance_of',
                    'loc': ['v'],
                    'message': 'Input should be an instance of Sequence',
                    'input_value': {
                        1.0,
                        2.0,
                        3.0,
                    },
                    'context': {
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
                    'kind': 'int_parsing',
                    'loc': ['v', 2, 0],
                    'message': 'Input should be a valid integer, unable to parse string as an integer',
                    'input_value': 'd',
                }
            ],
        ),
        (
            Tuple[int, str],
            ((1, 'a'), ('a', 'a'), (3, 'c')),
            [
                {
                    'kind': 'int_parsing',
                    'loc': ['v', 1, 0],
                    'message': 'Input should be a valid integer, unable to parse string as an integer',
                    'input_value': 'a',
                }
            ],
        ),
        (
            List[int],
            [{'a': 1, 'b': 2}, [1, 2], [2, 3]],
            [
                {
                    'kind': 'list_type',
                    'loc': ['v', 0],
                    'message': 'Input should be a valid list/array',
                    'input_value': {'a': 1, 'b': 2},
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
    debug(exc_info.value.errors())
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
    assert m == {'a': 5, 'b': -5, 'c': 0, 'd': 0, 'e': 5, 'f': 0, 'g': 25}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-5, b=5, c=-5, d=5, e=-5, f=11, g=42)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'greater_than',
            'loc': ['a'],
            'message': 'Input should be greater than 0',
            'input_value': -5,
            'context': {'gt': 0},
        },
        {
            'kind': 'less_than',
            'loc': ['b'],
            'message': 'Input should be less than 0',
            'input_value': 5,
            'context': {'lt': 0},
        },
        {
            'kind': 'greater_than_equal',
            'loc': ['c'],
            'message': 'Input should be greater than or equal to 0',
            'input_value': -5,
            'context': {'ge': 0},
        },
        {
            'kind': 'less_than_equal',
            'loc': ['d'],
            'message': 'Input should be less than or equal to 0',
            'input_value': 5,
            'context': {'le': 0},
        },
        {
            'kind': 'greater_than',
            'loc': ['e'],
            'message': 'Input should be greater than 4',
            'input_value': -5,
            'context': {'gt': 4},
        },
        {
            'kind': 'less_than_equal',
            'loc': ['f'],
            'message': 'Input should be less than or equal to 10',
            'input_value': 11,
            'context': {'le': 10},
        },
        {
            'kind': 'multiple_of',
            'loc': ['g'],
            'message': 'Input should be a multiple of 5',
            'input_value': 42,
            'context': {'multiple_of': 5},
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
    assert m.dict() == {'a': 5.1, 'b': -5.2, 'c': 0, 'd': 0, 'e': 5.3, 'f': 9.9, 'g': 2.5, 'h': 42}

    assert Model(a=float('inf')).a == float('inf')
    assert Model(b=float('-inf')).b == float('-inf')

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-5.1, b=5.2, c=-5.1, d=5.1, e=-5.3, f=9.91, g=4.2, h=float('nan'))
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'greater_than',
            'loc': ['a'],
            'message': 'Input should be greater than 0',
            'input_value': -5.1,
            'context': {
                'gt': 0.0,
            },
        },
        {
            'kind': 'less_than',
            'loc': ['b'],
            'message': 'Input should be less than 0',
            'input_value': 5.2,
            'context': {
                'lt': 0.0,
            },
        },
        {
            'kind': 'greater_than_equal',
            'loc': ['c'],
            'message': 'Input should be greater than or equal to 0',
            'input_value': -5.1,
            'context': {
                'ge': 0.0,
            },
        },
        {
            'kind': 'less_than_equal',
            'loc': ['d'],
            'message': 'Input should be less than or equal to 0',
            'input_value': 5.1,
            'context': {
                'le': 0.0,
            },
        },
        {
            'kind': 'greater_than',
            'loc': ['e'],
            'message': 'Input should be greater than 4',
            'input_value': -5.3,
            'context': {
                'gt': 4.0,
            },
        },
        {
            'kind': 'less_than_equal',
            'loc': ['f'],
            'message': 'Input should be less than or equal to 9.9',
            'input_value': 9.91,
            'context': {
                'le': 9.9,
            },
        },
        {
            'kind': 'multiple_of',
            'loc': ['g'],
            'message': 'Input should be a multiple of 0.5',
            'input_value': 4.2,
            'context': {
                'multiple_of': 0.5,
            },
        },
        {
            'kind': 'finite_number',
            'loc': ['h'],
            'message': 'Input should be a finite number',
            'input_value': HasRepr('nan'),
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
            'kind': 'finite_number',
            'loc': ['a'],
            'message': 'Input should be a finite number',
            'input_value': HasRepr(repr(value)),
        }
    ]


def test_finite_float_config():
    class Model(BaseModel):
        a: float

        class Config:
            allow_inf_nan = False

    assert Model(a=42).a == 42
    with pytest.raises(ValidationError) as exc_info:
        Model(a=float('nan'))
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'finite_number',
            'loc': ['a'],
            'message': 'Input should be a finite number',
            'input_value': HasRepr('nan'),
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

    with pytest.raises(ValidationError, match=r'Input should be a valid bytes \[kind=bytes_type'):
        Model(u=123)
    with pytest.raises(ValidationError, match=r'Data should have at most 5 bytes \[kind=too_long'):
        Model(u=b'1234567')


@pytest.mark.xfail(reason="TODO string enums definitely shouldn't be allowed")
def test_strict_str():
    class FruitEnum(str, Enum):
        pear = 'pear'
        banana = 'banana'

    class Model(BaseModel):
        v: StrictStr

    assert Model(v='foobar').v == 'foobar'

    with pytest.raises(ValidationError, match='Input should be a valid string'):
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

    with pytest.raises(ValidationError, match=r'String should have at most 5 characters \[kind=too_long,'):
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

    with pytest.raises(ValidationError, match=r'Input should be a valid integer \[kind=int_type,'):
        Model(v='123456')

    with pytest.raises(ValidationError, match=r'Input should be a valid integer \[kind=int_type,'):
        Model(v=3.14159)


def test_strict_float():
    class Model(BaseModel):
        v: StrictFloat

    assert Model(v=3.14159).v == 3.14159
    assert Model(v=123456).v == 123456

    with pytest.raises(ValidationError, match=r'Input should be a valid number \[kind=float_type,'):
        Model(v='3.14159')


def test_bool_unhashable_fails():
    class Model(BaseModel):
        v: bool

    with pytest.raises(ValidationError) as exc_info:
        Model(v={})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'bool_type', 'loc': ['v'], 'message': 'Input should be a valid boolean', 'input_value': {}}
    ]


def test_uuid_error():
    class Model(BaseModel):
        v: UUID

    with pytest.raises(ValidationError) as exc_info:
        Model(v='ebcdab58-6eb8-46fb-a190-d07a3')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'uuid_type',
            'loc': ['v'],
            'message': 'Input should be a valid UUID, string, or bytes',
            'input_value': 'ebcdab58-6eb8-46fb-a190-d07a3',
        }
    ]

    with pytest.raises(ValidationError, match='Input should be a valid UUID, string, or bytes'):
        Model(v=None)


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
    assert m.dict() == {'a': a, 'b': b, 'c': c, 'd': d}

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=d, b=c, c=b, d=a)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'uuid_version',
            'loc': ['a'],
            'message': 'uuid version 1 expected',
            'input_value': d,
            'context': {'required_version': 1},
        },
        {
            'kind': 'uuid_version',
            'loc': ['b'],
            'message': 'uuid version 3 expected',
            'input_value': c,
            'context': {'required_version': 3},
        },
        {
            'kind': 'uuid_version',
            'loc': ['c'],
            'message': 'uuid version 4 expected',
            'input_value': b,
            'context': {'required_version': 4},
        },
        {
            'kind': 'uuid_version',
            'loc': ['d'],
            'message': 'uuid version 5 expected',
            'input_value': a,
            'context': {'required_version': 5},
        },
    ]


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [
        (True, '  123  ', '123'),
        (True, '  123\t\n', '123'),
        (False, '  123  ', '  123  '),
    ],
)
def test_anystr_strip_whitespace(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        class Config:
            anystr_strip_whitespace = enabled

    m = Model(str_check=str_check)
    assert m.str_check == result_str_check


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [(True, 'ABCDefG', 'ABCDEFG'), (False, 'ABCDefG', 'ABCDefG')],
)
def test_anystr_upper(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        class Config:
            anystr_upper = enabled

    m = Model(str_check=str_check)

    assert m.str_check == result_str_check


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [(True, 'ABCDefG', 'abcdefg'), (False, 'ABCDefG', 'ABCDefG')],
)
def test_anystr_lower(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        class Config:
            anystr_lower = enabled

    m = Model(str_check=str_check)

    assert m.str_check == result_str_check


@pytest.mark.xfail(reason='todo')
@pytest.mark.parametrize(
    'type_args,value,result',
    [
        (dict(gt=Decimal('42.24')), Decimal('43'), Decimal('43')),
        (
            dict(gt=Decimal('42.24')),
            Decimal('42'),
            [
                {
                    'kind': 'greater_than',
                    'loc': ['foo'],
                    'message': 'Input should be greater than 42.24',
                    'input_value': Decimal('42'),
                    'context': {'gt': 42.24},
                }
            ],
        ),
        (dict(lt=Decimal('42.24')), Decimal('42'), Decimal('42')),
        (
            dict(lt=Decimal('42.24')),
            Decimal('43'),
            [
                {
                    'kind': 'less_than',
                    'loc': ['foo'],
                    'message': 'Input should be less than 42.24',
                    'input_value': Decimal('43'),
                    'context': {
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
                    'kind': 'greater_than_equal',
                    'loc': ['foo'],
                    'message': 'Input should be greater than or equal to 42.24',
                    'input_value': Decimal('42'),
                    'context': {
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
                    'kind': 'less_than_equal',
                    'loc': ['foo'],
                    'message': 'Input should be less than or equal to 42.24',
                    'input_value': Decimal('43'),
                    'context': {
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
                    'kind': 'decimal_max_places',
                    'loc': ['foo'],
                    'message': 'ensure that there are no more than 1 decimal places',
                    'input_value': Decimal('0.99'),
                    'context': {
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
                    'type': 'value_error.decimal.whole_digits',
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
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 20 digits in total',
                    'type': 'value_error.decimal.max_digits',
                    'ctx': {'max_digits': 20},
                }
            ],
        ),
        (dict(max_digits=5, decimal_places=2), Decimal('7304E-1'), Decimal('7304E-1')),
        (
            dict(max_digits=5, decimal_places=2),
            Decimal('7304E-3'),
            [
                {
                    'kind': 'decimal_max_places',
                    'loc': ['foo'],
                    'message': 'ensure that there are no more than 2 decimal places',
                    'input_value': Decimal('7.304'),
                    'context': {'decimal_places': 2},
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
                    'type': 'value_error.decimal.max_digits',
                    'ctx': {'max_digits': 5},
                }
            ],
        ),
        *[
            (
                dict(decimal_places=2, max_digits=10),
                value,
                [{'loc': ('foo',), 'msg': 'value is not a valid decimal', 'type': 'value_error.decimal.not_finite'}],
            )
            for value in (
                'NaN',
                '-NaN',
                '+NaN',
                'sNaN',
                '-sNaN',
                '+sNaN',
                'Inf',
                '-Inf',
                '+Inf',
                'Infinity',
                '-Infinity',
                '-Infinity',
            )
        ],
        *[
            (
                dict(decimal_places=2, max_digits=10),
                Decimal(value),
                [{'loc': ('foo',), 'msg': 'value is not a valid decimal', 'type': 'value_error.decimal.not_finite'}],
            )
            for value in (
                'NaN',
                '-NaN',
                '+NaN',
                'sNaN',
                '-sNaN',
                '+sNaN',
                'Inf',
                '-Inf',
                '+Inf',
                'Infinity',
                '-Infinity',
                '-Infinity',
            )
        ],
        (
            dict(multiple_of=Decimal('5')),
            Decimal('42'),
            [
                {
                    'kind': 'decimal_multiple_of',
                    'loc': ['foo'],
                    'message': 'Input should be a multiple of 5',
                    'input_value': Decimal('42'),
                    'context': {
                        'multiple_of': Decimal('5'),
                    },
                }
            ],
        ),
    ],
    ids=repr,
)
def test_decimal_validation(type_args, value, result):
    modela = create_model('DecimalModel', foo=(condecimal(**type_args), ...))
    modelb = create_model('DecimalModel', foo=(Decimal, Field(..., **type_args)))

    for model in (modela, modelb):
        if not isinstance(result, Decimal):
            with pytest.raises(ValidationError) as exc_info:
                m = model(foo=value)
                print(f'unexpected result: {m!r}')
            # debug(exc_info.value.errors())
            assert exc_info.value.errors() == result
            # assert exc_info.value.json().startswith('[')
        else:
            assert model(foo=value).foo == result


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
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'value is not a valid path', 'type': 'type_error.path'}]


@pytest.mark.parametrize(
    'value,result',
    (('tests/test_types.py', Path('tests/test_types.py')), (Path('tests/test_types.py'), Path('tests/test_types.py'))),
)
def test_file_path_validation_success(value, result):
    class Model(BaseModel):
        foo: FilePath

    assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value,errors',
    (
        (
            'nonexistentfile',
            [
                {
                    'loc': ('foo',),
                    'msg': 'file or directory at path "nonexistentfile" does not exist',
                    'type': 'value_error.path.not_exists',
                    'ctx': {'path': 'nonexistentfile'},
                }
            ],
        ),
        (
            Path('nonexistentfile'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'file or directory at path "nonexistentfile" does not exist',
                    'type': 'value_error.path.not_exists',
                    'ctx': {'path': 'nonexistentfile'},
                }
            ],
        ),
        (
            'tests',
            [
                {
                    'loc': ('foo',),
                    'msg': 'path "tests" does not point to a file',
                    'type': 'value_error.path.not_a_file',
                    'ctx': {'path': 'tests'},
                }
            ],
        ),
        (
            Path('tests'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'path "tests" does not point to a file',
                    'type': 'value_error.path.not_a_file',
                    'ctx': {'path': 'tests'},
                }
            ],
        ),
    ),
)
def test_file_path_validation_fails(value, errors):
    class Model(BaseModel):
        foo: FilePath

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors() == errors


@pytest.mark.parametrize('value,result', (('tests', Path('tests')), (Path('tests'), Path('tests'))))
def test_directory_path_validation_success(value, result):
    class Model(BaseModel):
        foo: DirectoryPath

    assert Model(foo=value).foo == result


@pytest.mark.skipif(sys.platform.startswith('win'), reason='paths look different on windows')
@pytest.mark.parametrize(
    'value,errors',
    (
        (
            'nonexistentdirectory',
            [
                {
                    'loc': ('foo',),
                    'msg': 'file or directory at path "nonexistentdirectory" does not exist',
                    'type': 'value_error.path.not_exists',
                    'ctx': {'path': 'nonexistentdirectory'},
                }
            ],
        ),
        (
            Path('nonexistentdirectory'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'file or directory at path "nonexistentdirectory" does not exist',
                    'type': 'value_error.path.not_exists',
                    'ctx': {'path': 'nonexistentdirectory'},
                }
            ],
        ),
        (
            'tests/test_types.py',
            [
                {
                    'loc': ('foo',),
                    'msg': 'path "tests/test_types.py" does not point to a directory',
                    'type': 'value_error.path.not_a_directory',
                    'ctx': {'path': 'tests/test_types.py'},
                }
            ],
        ),
        (
            Path('tests/test_types.py'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'path "tests/test_types.py" does not point to a directory',
                    'type': 'value_error.path.not_a_directory',
                    'ctx': {'path': 'tests/test_types.py'},
                }
            ],
        ),
    ),
)
def test_directory_path_validation_fails(value, errors):
    class Model(BaseModel):
        foo: DirectoryPath

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors() == errors


base_message = r'.*ensure this value is {msg} \(type=value_error.number.not_{ty}; limit_value={value}\).*'


def test_number_gt():
    class Model(BaseModel):
        a: conint(gt=-1) = 0

    assert Model(a=0).dict() == {'a': 0}

    message = base_message.format(msg='greater than -1', ty='gt', value=-1)
    with pytest.raises(ValidationError, match=message):
        Model(a=-1)


def test_number_ge():
    class Model(BaseModel):
        a: conint(ge=0) = 0

    assert Model(a=0).dict() == {'a': 0}

    message = base_message.format(msg='greater than or equal to 0', ty='ge', value=0)
    with pytest.raises(ValidationError, match=message):
        Model(a=-1)


def test_number_lt():
    class Model(BaseModel):
        a: conint(lt=5) = 0

    assert Model(a=4).dict() == {'a': 4}

    message = base_message.format(msg='less than 5', ty='lt', value=5)
    with pytest.raises(ValidationError, match=message):
        Model(a=5)


def test_number_le():
    class Model(BaseModel):
        a: conint(le=5) = 0

    assert Model(a=5).dict() == {'a': 5}

    message = base_message.format(msg='less than or equal to 5', ty='le', value=5)
    with pytest.raises(ValidationError, match=message):
        Model(a=6)


@pytest.mark.parametrize('value', ((10), (100), (20)))
def test_number_multiple_of_int_valid(value):
    class Model(BaseModel):
        a: conint(multiple_of=5)

    assert Model(a=value).dict() == {'a': value}


@pytest.mark.parametrize('value', ((1337), (23), (6), (14)))
def test_number_multiple_of_int_invalid(value):
    class Model(BaseModel):
        a: conint(multiple_of=5)

    multiple_message = base_message.replace('limit_value', 'multiple_of')
    message = multiple_message.format(msg='a multiple of 5', ty='multiple', value=5)
    with pytest.raises(ValidationError, match=message):
        Model(a=value)


@pytest.mark.parametrize('value', ((0.2), (0.3), (0.4), (0.5), (1)))
def test_number_multiple_of_float_valid(value):
    class Model(BaseModel):
        a: confloat(multiple_of=0.1)

    assert Model(a=value).dict() == {'a': value}


@pytest.mark.parametrize('value', ((0.07), (1.27), (1.003)))
def test_number_multiple_of_float_invalid(value):
    class Model(BaseModel):
        a: confloat(multiple_of=0.1)

    multiple_message = base_message.replace('limit_value', 'multiple_of')
    message = multiple_message.format(msg='a multiple of 0.1', ty='multiple', value=0.1)
    with pytest.raises(ValidationError, match=message):
        Model(a=value)


@pytest.mark.parametrize('fn', [conint, confloat, condecimal])
def test_bounds_config_exceptions(fn):
    with pytest.raises(ConfigError):
        fn(gt=0, ge=0)

    with pytest.raises(ConfigError):
        fn(lt=0, le=0)


def test_new_type_success():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', List[int])

    class Model(BaseModel):
        a: a_type
        b: b_type
        c: c_type

    m = Model(a=42, b=24, c=[1, 2, 3])
    assert m.dict() == {'a': 42, 'b': 24, 'c': [1, 2, 3]}
    assert repr(Model.__fields__['c']) == "ModelField(name='c', type=List[int], required=True)"


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
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('c', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_json_any_is_json():
    """Mypy doesn't allow plain Json, so Json[Any] must behave just as Json did."""
    assert Json[Any] is Json


def test_valid_simple_json():
    class JsonModel(BaseModel):
        json_obj: Json

    obj = '{"a": 1, "b": [2, 3]}'
    assert JsonModel(json_obj=obj).dict() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_valid_simple_json_any():
    class JsonModel(BaseModel):
        json_obj: Json[Any]

    obj = '{"a": 1, "b": [2, 3]}'
    assert JsonModel(json_obj=obj).dict() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_invalid_simple_json():
    class JsonModel(BaseModel):
        json_obj: Json

    obj = '{a: 1, b: [2, 3]}'
    with pytest.raises(ValidationError) as exc_info:
        JsonModel(json_obj=obj)
    assert exc_info.value.errors()[0] == {'loc': ('json_obj',), 'msg': 'Invalid JSON', 'type': 'value_error.json'}


def test_invalid_simple_json_any():
    class JsonModel(BaseModel):
        json_obj: Json[Any]

    obj = '{a: 1, b: [2, 3]}'
    with pytest.raises(ValidationError) as exc_info:
        JsonModel(json_obj=obj)
    assert exc_info.value.errors()[0] == {'loc': ('json_obj',), 'msg': 'Invalid JSON', 'type': 'value_error.json'}


def test_valid_simple_json_bytes():
    class JsonModel(BaseModel):
        json_obj: Json

    obj = b'{"a": 1, "b": [2, 3]}'
    assert JsonModel(json_obj=obj).dict() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_valid_detailed_json():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = '[1, 2, 3]'
    assert JsonDetailedModel(json_obj=obj).dict() == {'json_obj': [1, 2, 3]}


def test_invalid_detailed_json_value_error():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = '(1, 2, 3)'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    assert exc_info.value.errors()[0] == {'loc': ('json_obj',), 'msg': 'Invalid JSON', 'type': 'value_error.json'}


def test_valid_detailed_json_bytes():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = b'[1, 2, 3]'
    assert JsonDetailedModel(json_obj=obj).dict() == {'json_obj': [1, 2, 3]}


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
    assert m.dict() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_invalid_model_json():
    class Model(BaseModel):
        a: int
        b: List[int]

    class JsonDetailedModel(BaseModel):
        json_obj: Json[Model]

    obj = '{"a": 1, "c": [2, 3]}'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)

    assert exc_info.value.errors() == [
        {'loc': ('json_obj', 'b'), 'msg': 'field required', 'type': 'value_error.missing'}
    ]


def test_invalid_detailed_json_type_error():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = '["a", "b", "c"]'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    assert exc_info.value.errors() == [
        {'loc': ('json_obj', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('json_obj', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('json_obj', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_json_not_str():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = 12
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    assert exc_info.value.errors()[0] == {
        'loc': ('json_obj',),
        'msg': 'JSON object must be str, bytes or bytearray',
        'type': 'type_error.json',
    }


def test_json_pre_validator():
    call_count = 0

    class JsonModel(BaseModel):
        json_obj: Json

        @validator('json_obj', pre=True)
        def check(cls, v):
            assert v == '"foobar"'
            nonlocal call_count
            call_count += 1
            return v

    assert JsonModel(json_obj='"foobar"').dict() == {'json_obj': 'foobar'}
    assert call_count == 1


def test_json_optional_simple():
    class JsonOptionalModel(BaseModel):
        json_obj: Optional[Json]

    assert JsonOptionalModel(json_obj=None).dict() == {'json_obj': None}
    assert JsonOptionalModel(json_obj='["x", "y", "z"]').dict() == {'json_obj': ['x', 'y', 'z']}


def test_json_optional_complex():
    class JsonOptionalModel(BaseModel):
        json_obj: Optional[Json[List[int]]]

    JsonOptionalModel(json_obj=None)

    good = JsonOptionalModel(json_obj='[1, 2, 3]')
    assert good.json_obj == [1, 2, 3]

    with pytest.raises(ValidationError) as exc_info:
        JsonOptionalModel(json_obj='["i should fail"]')
    assert exc_info.value.errors() == [
        {'loc': ('json_obj', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_json_explicitly_required():
    class JsonRequired(BaseModel):
        json_obj: Json = ...

    assert JsonRequired(json_obj=None).dict() == {'json_obj': None}
    assert JsonRequired(json_obj='["x", "y", "z"]').dict() == {'json_obj': ['x', 'y', 'z']}
    with pytest.raises(ValidationError) as exc_info:
        JsonRequired()
    assert exc_info.value.errors() == [{'loc': ('json_obj',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_json_no_default():
    class JsonRequired(BaseModel):
        json_obj: Json

    assert JsonRequired(json_obj=None).dict() == {'json_obj': None}
    assert JsonRequired(json_obj='["x", "y", "z"]').dict() == {'json_obj': ['x', 'y', 'z']}
    assert JsonRequired().dict() == {'json_obj': None}


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

    assert Foobar.schema() == {
        'type': 'object',
        'title': 'Foobar',
        'properties': {'pattern': {'type': 'string', 'format': 'regex', 'title': 'Pattern'}},
        'required': ['pattern'],
    }


@pytest.mark.parametrize('pattern_type', [re.Pattern, Pattern])
def test_pattern_error(pattern_type):
    class Foobar(BaseModel):
        pattern: pattern_type

    with pytest.raises(ValidationError) as exc_info:
        Foobar(pattern='[xx')
    assert exc_info.value.errors() == [
        {'loc': ('pattern',), 'msg': 'Invalid regular expression', 'type': 'value_error.regex_pattern'}
    ]


def test_secretfield():
    class Foobar(SecretField):
        ...

    message = "Can't instantiate abstract class Foobar with abstract methods? get_secret_value"

    with pytest.raises(TypeError, match=message):
        Foobar()


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

    with pytest.warns(DeprecationWarning, match=r'`secret_str.display\(\)` is deprecated'):
        assert f.password.display() == '**********'
    with pytest.warns(DeprecationWarning, match=r'`secret_str.display\(\)` is deprecated'):
        assert f.empty_password.display() == ''

    # Assert that SecretStr is equal to SecretStr if the secret is the same.
    assert f == f.copy()
    assert f != f.copy(update=dict(password='4321'))


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
    assert exc_info.value.errors() == [{'loc': ('password',), 'msg': 'str type expected', 'type': 'type_error.str'}]


def test_secretstr_min_max_length():
    class Foobar(BaseModel):
        password: SecretStr = Field(min_length=6, max_length=10)

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password='')

    assert exc_info.value.errors() == [
        {
            'loc': ('password',),
            'msg': 'ensure this value has at least 6 characters',
            'type': 'value_error.any_str.min_length',
            'ctx': {'limit_value': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password='1' * 20)

    assert exc_info.value.errors() == [
        {
            'loc': ('password',),
            'msg': 'ensure this value has at most 10 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 10},
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
    assert str(f.password) == '**********'
    assert str(f.empty_password) == ''
    assert repr(f.password) == "SecretBytes(b'**********')"
    assert repr(f.empty_password) == "SecretBytes(b'')"

    # Assert retrieval of secret value is correct
    assert f.password.get_secret_value() == b'wearebytes'
    assert f.empty_password.get_secret_value() == b''

    with pytest.warns(DeprecationWarning, match=r'`secret_bytes.display\(\)` is deprecated'):
        assert f.password.display() == '**********'
    with pytest.warns(DeprecationWarning, match=r'`secret_bytes.display\(\)` is deprecated'):
        assert f.empty_password.display() == ''

    # Assert that SecretBytes is equal to SecretBytes if the secret is the same.
    assert f == f.copy()
    assert f != f.copy(update=dict(password=b'4321'))


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
    assert exc_info.value.errors() == [{'loc': ('password',), 'msg': 'byte type expected', 'type': 'type_error.bytes'}]


def test_secretbytes_min_max_length():
    class Foobar(BaseModel):
        password: SecretBytes = Field(min_length=6, max_length=10)

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=b'')

    assert exc_info.value.errors() == [
        {
            'loc': ('password',),
            'msg': 'ensure this value has at least 6 characters',
            'type': 'value_error.any_str.min_length',
            'ctx': {'limit_value': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=b'1' * 20)

    assert exc_info.value.errors() == [
        {
            'loc': ('password',),
            'msg': 'ensure this value has at most 10 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 10},
        }
    ]

    value = b'1' * 8
    assert Foobar(password=value).password.get_secret_value() == value


@pytest.mark.parametrize('secret_cls', [SecretStr, SecretBytes])
@pytest.mark.parametrize(
    'field_kw,schema_kw',
    [
        [{}, {}],
        [{'min_length': 6}, {'minLength': 6}],
        [{'max_length': 10}, {'maxLength': 10}],
        [{'min_length': 6, 'max_length': 10}, {'minLength': 6, 'maxLength': 10}],
    ],
    ids=['no-constrains', 'min-constraint', 'max-constraint', 'min-max-constraints'],
)
def test_secrets_schema(secret_cls, field_kw, schema_kw):
    class Foobar(BaseModel):
        password: secret_cls = Field(**field_kw)

    assert Foobar.schema() == {
        'title': 'Foobar',
        'type': 'object',
        'properties': {
            'password': {'title': 'Password', 'type': 'string', 'writeOnly': True, 'format': 'password', **schema_kw}
        },
        'required': ['password'],
    }


def test_generic_without_params():
    class Model(BaseModel):
        generic_list: List
        generic_dict: Dict
        generic_tuple: Tuple

    m = Model(generic_list=[0, 'a'], generic_dict={0: 'a', 'a': 0}, generic_tuple=(1, 'q'))
    assert m.dict() == {'generic_list': [0, 'a'], 'generic_dict': {0: 'a', 'a': 0}, 'generic_tuple': (1, 'q')}


def test_generic_without_params_error():
    class Model(BaseModel):
        generic_list: List
        generic_dict: Dict
        generic_tuple: Tuple

    with pytest.raises(ValidationError) as exc_info:
        Model(generic_list=0, generic_dict=0, generic_tuple=0)
    assert exc_info.value.errors() == [
        {'loc': ('generic_list',), 'msg': 'value is not a valid list', 'type': 'type_error.list'},
        {'loc': ('generic_dict',), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'},
        {'loc': ('generic_tuple',), 'msg': 'value is not a valid tuple', 'type': 'type_error.tuple'},
    ]


def test_literal_single():
    class Model(BaseModel):
        a: Literal['a']

    Model(a='a')
    with pytest.raises(ValidationError) as exc_info:
        Model(a='b')
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': "unexpected value; permitted: 'a'",
            'type': 'value_error.const',
            'ctx': {'given': 'b', 'permitted': ('a',)},
        }
    ]


def test_literal_multiple():
    class Model(BaseModel):
        a_or_b: Literal['a', 'b']

    Model(a_or_b='a')
    Model(a_or_b='b')
    with pytest.raises(ValidationError) as exc_info:
        Model(a_or_b='c')
    assert exc_info.value.errors() == [
        {
            'loc': ('a_or_b',),
            'msg': "unexpected value; permitted: 'a', 'b'",
            'type': 'value_error.const',
            'ctx': {'given': 'c', 'permitted': ('a', 'b')},
        }
    ]


def test_unsupported_field_type():
    with pytest.raises(TypeError, match=r'MutableSet(.*)not supported'):

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
        ('1', 1, '1.0B', '1.0B'),
        ('1.0', 1, '1.0B', '1.0B'),
        ('1b', 1, '1.0B', '1.0B'),
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
    with pytest.raises(errors.InvalidByteSizeUnit, match='byte unit'):
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
        (float, {1.0, 2.0, 3.0}, deque({1.0, 2.0, 3.0})),
        (Set[int], [{1, 2}, {3, 4}, {5, 6}], deque([{1, 2}, {3, 4}, {5, 6}])),
        (Tuple[int, str], ((1, 'a'), (2, 'b'), (3, 'c')), deque(((1, 'a'), (2, 'b'), (3, 'c')))),
        (str, [w for w in 'one two three'.split()], deque(['one', 'two', 'three'])),
        (int, frozenset([1, 2, 3]), deque([1, 2, 3])),
    ),
)
def test_deque_generic_success(cls, value, result):
    class Model(BaseModel):
        v: Deque[cls]

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'cls,value,errors',
    (
        (int, [1, 'a', 3], [{'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]),
        (int, (1, 2, 'a'), [{'loc': ('v', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]),
        (float, range(10), [{'loc': ('v',), 'msg': 'value is not a valid sequence', 'type': 'type_error.sequence'}]),
        (float, ('a', 2.2, 3.3), [{'loc': ('v', 0), 'msg': 'value is not a valid float', 'type': 'type_error.float'}]),
        (float, (1.1, 2.2, 'a'), [{'loc': ('v', 2), 'msg': 'value is not a valid float', 'type': 'type_error.float'}]),
        (
            Set[int],
            [{1, 2}, {2, 3}, {'d'}],
            [{'loc': ('v', 2, 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}],
        ),
        (
            Tuple[int, str],
            ((1, 'a'), ('a', 'a'), (3, 'c')),
            [{'loc': ('v', 1, 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}],
        ),
        (
            List[int],
            [{'a': 1, 'b': 2}, [1, 2], [2, 3]],
            [{'loc': ('v', 0), 'msg': 'value is not a valid list', 'type': 'type_error.list'}],
        ),
    ),
)
def test_deque_fails(cls, value, errors):
    class Model(BaseModel):
        v: Deque[cls]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == errors


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

    assert Model(v=deque((1, 2, 3))).json() == '{"v": [1, 2, 3]}'


none_value_type_cases = None, type(None), None.__class__, Literal[None]


@pytest.mark.parametrize('value_type', none_value_type_cases)
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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'my_none': {'title': 'My None', 'type': 'null'},
            'my_none_list': {
                'title': 'My None List',
                'type': 'array',
                'items': {'type': 'null'},
            },
            'my_none_dict': {
                'title': 'My None Dict',
                'type': 'object',
                'additionalProperties': {'type': 'null'},
            },
            'my_json_none': {'title': 'My Json None', 'type': 'null'},
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
    assert exc_info.value.errors() == [
        {'loc': ('my_none',), 'msg': 'value is not None', 'type': 'type_error.not_none'},
        {'loc': ('my_none_list', 0), 'msg': 'value is not None', 'type': 'type_error.not_none'},
        {'loc': ('my_none_list', 2), 'msg': 'value is not None', 'type': 'type_error.not_none'},
        {'loc': ('my_none_dict', 'a'), 'msg': 'value is not None', 'type': 'type_error.not_none'},
        {'loc': ('my_json_none',), 'msg': 'value is not None', 'type': 'type_error.not_none'},
    ]


def test_default_union_types():
    class DefaultModel(BaseModel):
        v: Union[int, bool, str]

    assert DefaultModel(v=True).dict() == {'v': 1}
    assert DefaultModel(v=1).dict() == {'v': 1}
    assert DefaultModel(v='1').dict() == {'v': 1}

    assert DefaultModel.schema() == {
        'title': 'DefaultModel',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'anyOf': [{'type': t} for t in ('integer', 'boolean', 'string')]}},
        'required': ['v'],
    }


def test_smart_union_types():
    class SmartModel(BaseModel):
        v: Union[int, bool, str]

        class Config:
            smart_union = True

    assert SmartModel(v=1).dict() == {'v': 1}
    assert SmartModel(v=True).dict() == {'v': True}
    assert SmartModel(v='1').dict() == {'v': '1'}

    assert SmartModel.schema() == {
        'title': 'SmartModel',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'anyOf': [{'type': t} for t in ('integer', 'boolean', 'string')]}},
        'required': ['v'],
    }


def test_default_union_class():
    class A(BaseModel):
        x: str

    class B(BaseModel):
        x: str

    class Model(BaseModel):
        y: Union[A, B]

    assert isinstance(Model(y=A(x='a')).y, A)
    # `B` instance is coerced to `A`
    assert isinstance(Model(y=B(x='b')).y, A)


def test_smart_union_class():
    class A(BaseModel):
        x: str

    class B(BaseModel):
        x: str

    class Model(BaseModel):
        y: Union[A, B]

        class Config:
            smart_union = True

    assert isinstance(Model(y=A(x='a')).y, A)
    assert isinstance(Model(y=B(x='b')).y, B)


def test_default_union_subclass():
    class MyStr(str):
        ...

    class Model(BaseModel):
        x: Union[int, str]

    assert Model(x=MyStr('1')).x == 1


def test_smart_union_subclass():
    class MyStr(str):
        ...

    class Model(BaseModel):
        x: Union[int, str]

        class Config:
            smart_union = True

    assert Model(x=MyStr('1')).x == '1'


def test_default_union_compound_types():
    class Model(BaseModel):
        values: Union[Dict[str, str], List[str]]

    assert Model(values={'L': '1'}).dict() == {'values': {'L': '1'}}
    assert Model(values=['L1']).dict() == {'values': {'L': '1'}}  # dict(['L1']) == {'L': '1'}


def test_smart_union_compound_types():
    class Model(BaseModel):
        values: Union[Dict[str, str], List[str], Dict[str, List[str]]]

        class Config:
            smart_union = True

    assert Model(values={'L': '1'}).dict() == {'values': {'L': '1'}}
    assert Model(values=['L1']).dict() == {'values': ['L1']}
    assert Model(values=('L1',)).dict() == {'values': {'L': '1'}}  # expected coercion into first dict if not a list
    assert Model(values={'x': ['pika']}) == {'values': {'x': ['pika']}}
    assert Model(values={'x': ('pika',)}).dict() == {'values': {'x': ['pika']}}
    with pytest.raises(ValidationError) as e:
        Model(values={'x': {'a': 'b'}})
    assert e.value.errors() == [
        {'loc': ('values', 'x'), 'msg': 'str type expected', 'type': 'type_error.str'},
        {'loc': ('values',), 'msg': 'value is not a valid list', 'type': 'type_error.list'},
        {'loc': ('values', 'x'), 'msg': 'value is not a valid list', 'type': 'type_error.list'},
    ]


def test_smart_union_compouned_types_edge_case():
    """For now, `smart_union` does not support well compound types"""

    class Model(BaseModel, smart_union=True):
        x: Union[List[str], List[int]]

    # should consider [1, 2] valid and not coerce once `smart_union` is improved
    assert Model(x=[1, 2]).x == ['1', '2']
    # still coerce if needed
    assert Model(x=[1, '2']).x == ['1', '2']


def test_smart_union_typeddict():
    class Dict1(TypedDict):
        foo: str

    class Dict2(TypedDict):
        bar: str

    class M(BaseModel):
        d: Union[Dict2, Dict1]

        class Config:
            smart_union = True

    assert M(d=dict(foo='baz')).d == {'foo': 'baz'}


@pytest.mark.parametrize(
    'value,result',
    (
        ('1996-01-22', date(1996, 1, 22)),
        (date(1996, 1, 22), date(1996, 1, 22)),
    ),
)
def test_past_date_validation_success(value, result):
    class Model(BaseModel):
        foo: PastDate

    assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value',
    (
        date.today(),
        date.today() + timedelta(1),
        datetime.today(),
        datetime.today() + timedelta(1),
        '2064-06-01',
    ),
)
def test_past_date_validation_fails(value):
    class Model(BaseModel):
        foo: PastDate

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors() == [
        {
            'loc': ('foo',),
            'msg': 'date is not in the past',
            'type': 'value_error.date.not_in_the_past',
        }
    ]


@pytest.mark.parametrize(
    'value,result',
    (
        (date.today() + timedelta(1), date.today() + timedelta(1)),
        (datetime.today() + timedelta(1), date.today() + timedelta(1)),
        ('2064-06-01', date(2064, 6, 1)),
    ),
)
def test_future_date_validation_success(value, result):
    class Model(BaseModel):
        foo: FutureDate

    assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value',
    (
        date.today(),
        date.today() - timedelta(1),
        datetime.today(),
        datetime.today() - timedelta(1),
        '1996-01-22',
    ),
)
def test_future_date_validation_fails(value):
    class Model(BaseModel):
        foo: FutureDate

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors() == [
        {
            'loc': ('foo',),
            'msg': 'date is not in the future',
            'type': 'value_error.date.not_in_the_future',
        }
    ]
