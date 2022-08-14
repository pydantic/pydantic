import sys

import pytest

pytestmark = pytest.mark.skipif(sys.version_info < (3, 10), reason='requires python 3.10 or higher')


@pytestmark
def test_match_args(create_module):
    create_module(
        # language=Python
        """
from pydantic import BaseModel

class Model(BaseModel):
    a: str
    b: str

m = Model(a='a', b='b')
match m:
    case Model('a', b):
        assert b == 'b'
    case _:
        assert False
"""
    )


@pytestmark
def test_match_kwargs(create_module):
    create_module(
        # language=Python
        """
from pydantic import BaseModel

class Model(BaseModel):
    a: str
    b: str

m = Model(a='a', b='b')

match m:
    case Model(a='a', b=b):
        assert b == 'b'
    case _:
        assert False

match m:
    case Model(b=b, a='a'):
        assert b == 'b'
    case _:
        assert False
"""
    )


@pytestmark
def test_match_args_private_attr(create_module):
    create_module(
        # language=Python
        """
from pydantic import BaseModel, PrivateAttr

class Model(BaseModel):
    a: str
    _b: str = PrivateAttr(default='b')
    c: str

m = Model(a='a', c='c')
match m:
    case Model('a', 'c'):
        pass
    case _:
        assert False
"""
    )
