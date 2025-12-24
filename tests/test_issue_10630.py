from __future__ import annotations

from pydantic import BaseModel


def test_issue_10630_recursion_error():
    class Model(BaseModel):
        x: Model | None = None

    m1 = Model()
    m2 = Model()
    m1.x = m1
    m2.x = m2
    assert m1 == m2
