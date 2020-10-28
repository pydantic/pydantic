import dataclasses

import pydantic


class ArbitraryType:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'ArbitraryType(value={self.value!r})'


@dataclasses.dataclass
class DC:
    a: ArbitraryType
    b: str


# valid as it is a builtin dataclass without validation
my_dc = DC(a=ArbitraryType(value=3), b='qwe')

try:
    class Model(pydantic.BaseModel):
        dc: DC
        other: str

    Model(dc=my_dc, other='other')
except RuntimeError as e:  # invalid as it is now a pydantic dataclass
    print(e)


class Model(pydantic.BaseModel):
    dc: DC
    other: str

    class Config:
        arbitrary_types_allowed = True


m = Model(dc=my_dc, other='other')
print(repr(m))
