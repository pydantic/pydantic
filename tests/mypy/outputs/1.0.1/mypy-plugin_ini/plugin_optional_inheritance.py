from pydantic import BaseModel


class Foo(BaseModel):
    id: int | None


class Bar(BaseModel):
    foo: Foo | None


class Baz(Bar):
    name: str


b = Bar(foo={"id": 1})
assert b.foo.id == 1
# MYPY: error: Item "None" of "Optional[Foo]" has no attribute "id"  [union-attr]

z = Baz(foo={"id": 1}, name="test")
assert z.foo.id == 1
# MYPY: error: Item "None" of "Optional[Foo]" has no attribute "id"  [union-attr]
