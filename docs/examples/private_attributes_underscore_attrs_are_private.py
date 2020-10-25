from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    __class_var__: ClassVar[str] = 'class var value'
    __private_attr__: str = 'private attr value'

    class Config:
        underscore_attrs_are_private = True


print(Model.__class_var__)
print(Model.__private_attr__)
print(Model().__private_attr__)
