from __future__ import annotations

from pydantic import BaseModel


def test_issue_10630_recursion_error():
    class Model(BaseModel):
        x: Model | None = None

    m = Model()
    m.x = m
    assert m == m
