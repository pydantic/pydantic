from pydantic import BaseModel, Field


class Foo(BaseModel):
    private_name: int = Field(0, alias='public_name')


foo = Foo(public_name=1)
foo.private_name  # returns 1
