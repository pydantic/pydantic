from pydantic import BaseModel, Field


class Foo(BaseModel):
    a: int = Field(default=1, frozen=True)


foo = Foo()

foo.a = 2
# MYPY: error: Property "a" defined in "Foo" is read-only  [misc]


class Parent(BaseModel):
    parent_attr: str = Field(exclude=True)


# `parent_attr` is writable, mypy should error when overriding with a read-only property
class Child(Parent):
    child_attr: str = Field(exclude=True)

    @property
# MYPY: error: BaseModel field may only be overridden by another field  [misc]
    def parent_attr(self) -> str:
# MYPY: error: Cannot override writeable attribute with read-only property  [override]
        return self.child_attr
