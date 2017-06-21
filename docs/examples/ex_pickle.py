import pickle
from pydantic import BaseModel


class FooBarModel(BaseModel):
    a: str
    b: int


m = FooBarModel(a='hello', b=123)
print(m)
# > FooBarModel a='hello' b=123

data = pickle.dumps(m)
print(data)
# > b'\x80\x03c...'

m2 = pickle.loads(data)
print(m2)
# > FooBarModel a='hello' b=123
