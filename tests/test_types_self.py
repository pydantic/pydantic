def test_recursive_model(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from typing import Optional, Self
from pydantic import BaseModel

class SelfRef(BaseModel):
    data: int
    ref: Optional[Self] = None
"""
    )
    self_ref = module.SelfRef(data=1, ref={'data': 2})
    assert self_ref.model_dump() == {'data': 1, 'ref': {'data': 2, 'ref': None}}
