from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    foo: int


@dataclass(config={})
class Bar:
    bar: str
