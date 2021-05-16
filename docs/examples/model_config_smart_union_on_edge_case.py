from typing import List, Union

from pydantic import BaseModel


class Model(BaseModel):
    x: Union[List[str], List[int]]


print(Model(x=[1, 2]))
