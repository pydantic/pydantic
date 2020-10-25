from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    _class_var: ClassVar[str] = 'class var value'
    _private_attr: str = 'private attr value'

    class Config:
        underscore_attrs_are_private = True


print(Model._class_var)
print(Model._private_attr)
print(Model()._private_attr)
