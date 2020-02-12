import inspect
from pydantic import BaseModel

class FooModel(BaseModel):
    id: int
    name: str = None
    description: str = 'Foo'
    apple: int = Field(..., alias='pear')

print(inspect.signature(FooModel))
