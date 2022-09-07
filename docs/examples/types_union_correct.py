from uuid import UUID
from typing import Union
from pydantic import BaseModel


class User(BaseModel):
    id: Union[UUID, int, str]
    name: str


user_03_uuid = UUID('cf57432e-809e-4353-adbd-9d5c0d733868')
user_03 = User(id=user_03_uuid, name='John Doe')
print(user_03)
print(user_03.id)
print(user_03_uuid.int)
