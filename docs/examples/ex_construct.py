from pydantic import BaseModel, ValidationError

class Model(BaseModel):
    a: int

c = Model.construct(a='dog')
print(c)
