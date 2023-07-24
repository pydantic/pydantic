from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass
# MYPY: error: Expression type contains "Any" (has type overloaded function)  [misc]
class Foo:
    foo: int


@dataclass(config=ConfigDict(title='Bar Title'))
# MYPY: error: Expression type contains "Any" (has type "type[ConfigDict]")  [misc]
# MYPY: error: Expression type contains "Any" (has type "ConfigDict")  [misc]
class Bar:
    bar: str
