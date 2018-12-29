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
