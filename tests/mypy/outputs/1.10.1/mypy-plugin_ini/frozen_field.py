from pydantic import BaseModel, Field


class Foo(BaseModel):
    a: int = Field(default=1, frozen=True)


foo = Foo()

foo.a = 2
# MYPY: error: Property "a" defined in "Foo" is read-only  [misc]
