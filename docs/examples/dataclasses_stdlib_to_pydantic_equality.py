import dataclasses

import pydantic


@dataclasses.dataclass
class StdlibUser:
    name: str
    age: int


PydanticUser = pydantic.dataclasses.dataclass(StdlibUser)

assert StdlibUser(name='pika', age=7) == PydanticUser(name='pika', age='7')
