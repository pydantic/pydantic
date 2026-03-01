from datetime import datetime
from typing import Optional

import pytest

from pydantic import BaseModel, Field, computed_field
from pydantic.color import Color


@pytest.fixture(scope='session', name='User')
def user_fixture():
    class User(BaseModel):
        id: int
        name: str = 'John Doe'
        signup_ts: Optional[datetime] = None
        friends: list[int] = []

    return User


def test_rich_repr(User):
    user = User(id=22)
    rich_repr = list(user.__rich_repr__())

    assert rich_repr == [
        ('id', 22),
        ('name', 'John Doe'),
        ('signup_ts', None),
        ('friends', []),
    ]


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_rich_repr_color(User):
    color = Color((10, 20, 30, 0.1))
    rich_repr = list(color.__rich_repr__())

    assert rich_repr == ['#0a141e1a', ('rgb', (10, 20, 30, 0.1))]


def test_rich_repr_computed_field_on_uninitialized_model():
    """Regression test for https://github.com/pydantic/pydantic/issues/10739.

    When a ValidationError is raised during __init__, __rich_repr__ should
    not crash when the model has computed fields.
    """

    class MyModel(BaseModel):
        version: str = Field()

        @computed_field
        @property
        def link(self) -> str:
            return f'/{self.version}'

    try:
        MyModel()
    except Exception as err:
        tb = err.__traceback__
        frame = tb.tb_next.tb_frame
        instance = frame.f_locals['self']
        # Should not raise AttributeError:
        result = list(instance.__rich_repr__())
        assert result == []
