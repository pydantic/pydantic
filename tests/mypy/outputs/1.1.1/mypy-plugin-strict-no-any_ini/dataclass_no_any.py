from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    foo: int


@dataclass(config=ConfigDict(title='Bar Title'))
class Bar:
    bar: str
