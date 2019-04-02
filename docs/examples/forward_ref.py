from typing import ForwardRef
from pydantic import BaseModel

Foo = ForwardRef('Foo')

class Foo(BaseModel):
    a: int = None
    b: Dict[str, FooType] = {}
    c: List[Foo] = []


Foo.update_forward_refs()

print(Foo())
#> Foo a=123 b={} c=[]
print(Foo(b={'bar': {'a': '321'}}, c=[{'a': 345}]))
#> Foo a=123 b={'bar': <Foo a=321 b={} c=[]>} c=[<Foo a=345 b={} c=[]>]
#> Foo a=123 b=<Foo a=321 b=None>
