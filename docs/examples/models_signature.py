import inspect
from pydantic import BaseModel

class FooModel(BaseModel):
    id: int
    name: str = None
    description: str = 'Foo'

print(inspect.signature(FooModel))
