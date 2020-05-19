from pydantic import BaseModel


class Foo(BaseModel):
    a: int = 123
    #: The sibling of `Foo` is referenced by string
    sibling: 'Foo' = None


Foo.update_forward_refs()

print(Foo())
print(Foo(sibling={'a': '321'}))
