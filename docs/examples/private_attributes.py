from datetime import datetime

from pydantic import BaseModel, Field

storage = {}

def get_new_id():
    return max(storage) + 1 if storage else 0

class BaseStorageModel(BaseModel):
    __slots__ = ('_dirty', '_created')
    _dirty: bool = True
    _created: datetime = None

    id: int = Field(default_factory=get_new_id)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name not in self.__private_attributes__:
            self._dirty = True

    def save(self):
        if self._dirty:
            if self.id not in storage:
                self._created = datetime.utcnow()
            storage[self.id] = self.dict()
            self._dirty = False

class Model(BaseStorageModel):
    foo: str
    bar: int = 42

m = Model(foo='bar')
print(m._dirty, m._created, storage)

m.save()
print(m._dirty, m._created, storage)

m.foo = 'baz'
print(m._dirty)

m.save()
print(m._dirty, storage)
