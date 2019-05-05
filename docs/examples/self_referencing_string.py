from pydantic import BaseModel

class Foo(BaseModel):
    a: int = 123
    #: The sibling of `Foo` is referenced by string
    sibling: 'Foo' = None

Foo.update_forward_refs()

print(Foo())
#> Foo a=123 sibling=None
print(Foo(sibling={'a': '321'}))
#> Foo a=123 sibling=<Foo a=321 sibling=None>
