import sys
from dataclasses import InitVar

import pytest

import pydantic.dataclasses


@pytest.mark.skipif(sys.version_info >= (3, 8), reason='No error is thrown for `InitVar` for Python 3.8+')
def test_init_var_does_not_work():
    with pytest.raises(RuntimeError) as e:

        @pydantic.dataclasses.dataclass
        class Model:
            some_field: InitVar[str]

    assert e.value.args == ('InitVar is not supported in Python 3.7 as type information is lost',)
