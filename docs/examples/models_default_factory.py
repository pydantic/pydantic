from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class Model(BaseModel):
    uid: UUID = Field(default_factory=uuid4)

m1 = Model()
m2 = Model()
assert m1.uid != m2.uid
