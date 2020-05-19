from pydantic import BaseModel


class FooBarModel(BaseModel):
    a: str
    b: dict

    class Config:
        allow_mutation = False


foobar = FooBarModel(a='hello', b={'apple': 'pear'})

try:
    foobar.a = 'different'
except TypeError as e:
    print(e)

print(foobar.a)
print(foobar.b)
foobar.b['apple'] = 'grape'
print(foobar.b)
