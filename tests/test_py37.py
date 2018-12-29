"""
Tests for python 3.7 behaviour, eg postponed annotations and (in future maybe) ForwardRef.
"""
import sys

import pytest

skip_not_37 = pytest.mark.skipif(sys.version_info < (3, 7), reason='testing >= 3.7 behaviour only')


@skip_not_37
def test_postponed_annotations(create_module):
    module = create_module(
        """
from __future__ import annotations
from pydantic import BaseModel

class Model(BaseModel):
    a: int
"""
    )
    m = module.Model(a='123')
    assert m.dict() == {'a': 123}


@skip_not_37
def test_postponed_annotations_optional(create_module):
    module = create_module(
        """
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

class Model(BaseModel):
    a: Optional[int]
"""
    )
    assert module.Model(a='123').dict() == {'a': 123}
    assert module.Model().dict() == {'a': None}


@skip_not_37
def test_basic_forward_ref(create_module):
    module = create_module(
        """
from typing import ForwardRef, Optional
from pydantic import BaseModel

class Foo(BaseModel):
    a: int

FooRef = ForwardRef('Foo')

class Bar(BaseModel):
    b: Optional[FooRef]
"""
    )

    assert module.Bar().dict() == {'b': None}
    assert module.Bar(b={'a': '123'}).dict() == {'b': {'a': 123}}


@skip_not_37
def test_self_forward_ref(create_module):
    module = create_module(
        """
from typing import ForwardRef
from pydantic import BaseModel

Foo = ForwardRef('Foo')

class Foo(BaseModel):
    a: int = 123
    b: Foo = None
    
Foo.update_forward_refs()
    """
    )

    assert module.Foo().dict() == {'a': 123, 'b': None}
    debug(module.Foo(b={'a': '321'}).dict())
    assert module.Foo(b={'a': '321'}).dict() == {'a': 123, 'b': {'a': 321, 'b': None}}
