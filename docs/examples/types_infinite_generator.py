from typing import Iterable
from pydantic import BaseModel


class Model(BaseModel):
    infinite: Iterable[int]


def infinite_ints():
    i = 0
    while True:
        yield i
        i += 1


m = Model(infinite=infinite_ints())
print(m)

for i in m.infinite:
    print(i)
    if i == 10:
        break
