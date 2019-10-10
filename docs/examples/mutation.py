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
    # > "FooBarModel" is immutable and does not support item assignment

print(foobar.a)
#> hello

print(foobar.b)
#> {'apple': 'pear'}

foobar.b['apple'] = 'grape'
print(foobar.b)
#> {'apple': 'grape'}
