from pydantic import BaseConfig, BaseModel

BaseConfig.arbitrary_types_allowed = True


class MyClass:
    """A random class"""


class Model(BaseModel):
    x: MyClass
