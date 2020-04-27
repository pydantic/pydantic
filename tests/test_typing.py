import pytest

from pydantic.typing import Literal
from pydantic.validators import all_literal_values


@pytest.mark.skipif(not Literal, reason='typing_extensions not installed')
def test_all_literal_values():
    L1 = Literal['1']
    assert all_literal_values(L1) == ('1',)

    L2 = Literal['2']
    L12 = Literal[L1, L2]
    assert sorted(all_literal_values(L12)) == sorted(('1', '2'))

    L312 = Literal['3', Literal[L1, L2]]
    assert sorted(all_literal_values(L312)) == sorted(('1', '2', '3'))
