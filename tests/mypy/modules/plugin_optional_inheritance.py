from typing import Optional

from pydantic import BaseModel


class Foo(BaseModel):
    id: Optional[int]


class Bar(BaseModel):
    foo: Optional[Foo]


class Baz(Bar):
    name: str


b = Bar(foo={'id': 1})
assert b.foo.id == 1

z = Baz(foo={'id': 1}, name='test')
assert z.foo.id == 1
