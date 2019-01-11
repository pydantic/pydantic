from typing import ForwardRef
from pydantic import BaseModel

Foo = ForwardRef('Foo')

class Foo(BaseModel):
    a: int = 123
    b: Foo = None

Foo.update_forward_refs()

print(Foo())
#> Foo a=123 b=None
print(Foo(b={'a': '321'}))
#> Foo a=123 b=<Foo a=321 b=None>
