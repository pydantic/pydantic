import sys

import pytest


@pytest.mark.skipif(sys.version_info < (3, 10), reason='requires python 3.10 or higher')
def test_match_kwargs(create_module):
    module = create_module(
        # language=Python
        """
from pydantic import BaseModel

class Model(BaseModel):
    a: str
    b: str

def main(model):
    match model:
        case Model(a='a', b=b):
            return b
        case Model(a='a2'):
            return 'b2'
        case _:
            return None
"""
    )
    assert module.main(module.Model(a='a', b='b')) == 'b'
    assert module.main(module.Model(a='a2', b='b')) == 'b2'
    assert module.main(module.Model(a='x', b='b')) is None
