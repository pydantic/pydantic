from __future__ import annotations
from pydantic import BaseModel


class Foo(BaseModel):
    a: int = 123
    #: The sibling of `Foo` is referenced directly by type
    sibling: Foo = None


Foo.update_forward_refs()

print(Foo())
print(Foo(sibling={'a': '321'}))
