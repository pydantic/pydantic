from typing import Final

from pydantic import BaseModel


class Model(BaseModel):
    f: Final[int] = 1


Model()
Model(f=2)
Model(f='not an int')
# MYPY: error: Argument "f" to "Model" has incompatible type "str"; expected "int"  [arg-type]
