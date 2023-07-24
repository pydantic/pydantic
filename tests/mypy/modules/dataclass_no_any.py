from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    foo: int


@dataclass(config=dict(title='Bar Title'))
class Bar:
    bar: str
