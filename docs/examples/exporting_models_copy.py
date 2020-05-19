from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

print(m.copy(include={'foo', 'bar'}))
print(m.copy(exclude={'foo', 'bar'}))
print(m.copy(update={'banana': 0}))
print(id(m.bar), id(m.copy().bar))
# normal copy gives the same object reference for `bar`
print(id(m.bar), id(m.copy(deep=True).bar))
# deep copy gives a new object reference for `bar`
