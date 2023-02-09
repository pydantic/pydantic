from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from pydantic.color import Color


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: List[int] = []


def test_rich_repr() -> None:
    user = User(id=22)
    rich_repr = list(user.__rich_repr__())

    assert rich_repr == [
        ('id', 22),
        ('name', 'John Doe'),
        ('signup_ts', None),
        ('friends', []),
    ]


def test_rich_repr_color() -> None:
    color = Color((10, 20, 30, 0.1))
    rich_repr = list(color.__rich_repr__())

    assert rich_repr == ['#0a141e1a', ('rgb', (10, 20, 30, 0.1))]
