from pydantic import BaseModel, Field


class Foo(BaseModel):
    a: int = Field(default=1, frozen=True)


foo = Foo()

foo.a = 2


class Parent(BaseModel):
    parent_attr: str = Field(exclude=True)


# We don't wan't to froze `parent_attr` in the plugin:
class Chield(Parent):
    child_attr: str = Field(exclude=True)

    @property
    def parent_attr(self) -> str:
        return self.child_attr
