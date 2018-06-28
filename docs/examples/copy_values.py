from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

print(m.dict())
# (returns a dictionary)
# > {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': 123}}

print(m.json())
# (returns a str)
# > {"banana": 3.14, "foo": "hello", "bar": {"whatever": 123}}

print(m.dict(include={'foo', 'bar'}))
# > {'foo': 'hello', 'bar': {'whatever': 123}}

print(m.dict(exclude={'foo', 'bar'}))
# > {'banana': 3.14}

print(m.copy())
# > FooBarModel banana=3.14 foo='hello' bar=<BarModel whatever=123>

print(m.copy(include={'foo', 'bar'}))
# > FooBarModel foo='hello' bar=<BarModel whatever=123>

print(m.copy(exclude={'foo', 'bar'}))
# > FooBarModel banana=3.14

print(m.copy(update={'banana': 0}))
# > FooBarModel banana=0 foo='hello' bar=<BarModel whatever=123>
