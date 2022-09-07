from typing import ForwardRef
from pydantic import BaseModel

Foo = ForwardRef('Foo')


class Foo(BaseModel):
    a: int = 123
    b: Foo = None


Foo.update_forward_refs()

print(Foo())
print(Foo(b={'a': '321'}))
