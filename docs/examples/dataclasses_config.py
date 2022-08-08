from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


# Option 1 - use directly a dict
# Note: `mypy` will still raise typo error
@dataclass(config=dict(validate_assignment=True))
class MyDataclass1:
    a: int


# Option 2 - use `ConfigDict`
# (same as before at runtime since it's a `TypedDict` but with intellisense)
@dataclass(config=ConfigDict(validate_assignment=True))
class MyDataclass2:
    a: int


# Option 3 - use a `Config` class like for a `BaseModel`
class Config:
    validate_assignment = True


@dataclass(config=Config)
class MyDataclass3:
    a: int
