from pydantic import BaseModel, create_model


class FooModel(BaseModel):
    foo: str
    bar: int = 123


BarModel = create_model('BarModel', apple='russet', banana='yellow', __base__=FooModel)
print(BarModel)
#> <class 'pydantic.main.BarModel'>
print(', '.join(BarModel.__fields__.keys()))
#> foo, bar, apple, banana
