from typing import List, Union

from pydantic import BaseModel


class Model(BaseModel, smart_union=True):
    x: Union[List[str], List[int]]


# Expected coercion
print(Model(x=[1, '2']))

# Unexpected coercion
print(Model(x=[1, 2]))
