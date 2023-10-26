from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    foo: int


@dataclass(config={'title': 'Bar Title'})
class Bar:
    bar: str
