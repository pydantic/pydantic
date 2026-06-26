from datetime import datetime

import pytest

from pydantic import BaseModel
from pydantic.color import Color


@pytest.fixture(scope='session', name='User')
def user_fixture():
    class User(BaseModel):
        id: int
        name: str = 'John Doe'
        signup_ts: datetime | None = None
        friends: list[int] = []

    return User


def test_rich_repr(User):
    user = User(id=22)
    rich_repr = list(user.__rich_repr__())

    assert rich_repr == [
        ('id', 22),
        ('name', 'John Doe', 'John Doe'),
        ('signup_ts', None, None),
        ('friends', [], []),
    ]


def test_rich_repr_non_default_fields(User):
    user = User(id=22, name='Jane', friends=[1, 2])
    rich_repr = list(user.__rich_repr__())

    assert rich_repr == [
        ('id', 22),
        ('name', 'Jane', 'John Doe'),
        ('signup_ts', None, None),
        ('friends', [1, 2], []),
    ]


def test_rich_repr_with_rich(User):
    pytest.importorskip('rich')
    from rich.pretty import pretty_repr

    user = User(id=22)
    assert pretty_repr(user) == 'User(id=22)'

    user = User(id=22, name='Jane')
    assert pretty_repr(user) == "User(id=22, name='Jane')"


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_rich_repr_color(User):
    color = Color((10, 20, 30, 0.1))
    rich_repr = list(color.__rich_repr__())

    assert rich_repr == ['#0a141e1a', ('rgb', (10, 20, 30, 0.1))]
