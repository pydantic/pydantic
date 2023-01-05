from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

# returns a dictionary:
print(m.model_dump())
print(m.model_dump(include={'foo', 'bar'}))
print(m.model_dump(exclude={'foo', 'bar'}))
