from pydantic import BaseModel

class DatabaseFoo:
    def __init__(self, count, size=None):
        self.count = count
        self.size = size

class Foo(BaseModel):
    count: int = ...
    size: float = None

database_foo = DatabaseFoo(count=2, size=4.2)
m = Foo(database_foo)
print(m)
# Foo count=2 size=4.2
print(m.dict())
# {'count': 2, 'size': 4.2}
