from pydantic import BaseModel, ValidationError

class Model(BaseModel):
    a: int
    b = 2
    c: int = 1
    d = 0
    e: float

print(Model.__fields__.keys())
#> dict_keys(['a', 'c', 'e', 'b', 'd'])
m = Model(e=2, a=1)
print(m.dict())
#> {'a': 1, 'c': 'x', 'e': 2.0, 'b': 2, 'd': 'y'}

try:
    Model(a='x', b='x', c='x', d='x', e='x')
except ValidationError as e:
    error_logs = [e['loc'] for e in e.errors()]

print(error_logs)
#> [('a',), ('c',), ('e',), ('b',), ('d',)]
