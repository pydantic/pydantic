# To be changed in V3 (see https://github.com/pydantic/pydantic/issues/11119)
from typing import Final

from pydantic import BaseModel


class Model(BaseModel):
    f: Final[int] = 1


Model()
