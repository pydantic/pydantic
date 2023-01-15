from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b = 2
    c: int = 1
    d = 0
    e: float


print(Model.model_fields.keys())
m = Model(e=2, a=1)
print(m.model_dump())
try:
    Model(a='x', b='x', c='x', d='x', e='x')
except ValidationError as err:
    error_locations = [e['loc'] for e in err.errors()]

print(error_locations)
