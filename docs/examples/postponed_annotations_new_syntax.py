from __future__ import annotations

from pydantic import BaseModel


class Foo(BaseModel):
    values: list[int | str]
    optional: str | None = None


Foo(values=[1, 'qwe'])
