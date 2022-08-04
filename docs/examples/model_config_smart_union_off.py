from typing import Union

from pydantic import BaseModel


class Foo(BaseModel):
    pass


class Bar(BaseModel):
    pass


class Model(BaseModel):
    x: Union[str, int]
    y: Union[Foo, Bar]


print(Model(x=1, y=Bar()))
