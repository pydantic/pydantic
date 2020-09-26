import pickle
from pydantic import BaseModel


class FooBarModel(BaseModel):
    a: str
    b: int


m = FooBarModel(a='hello', b=123)
print(m)
data = pickle.dumps(m)
print(data)
m2 = pickle.loads(data)
print(m2)
