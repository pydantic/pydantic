from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b = 2
    c: int = 1
    d = 0
    e: float


print(Model.__fields__.keys())
m = Model(e=2, a=1)
print(m.dict())
try:
    Model(a='x', b='x', c='x', d='x', e='x')
except ValidationError as e:
    error_locations = [e['loc'] for e in e.errors()]

print(error_locations)
