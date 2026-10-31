from datetime import datetime

import pytest

from pydantic import BaseModel


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
        ('name', 'John Doe'),
        ('signup_ts', None),
        ('friends', []),
    ]
