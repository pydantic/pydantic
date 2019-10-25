from typing import Any, Optional, Union

from pydantic import BaseModel, Extra, Field


class Model(BaseModel):
    x: int
    y: str

    def method(self) -> None:
        pass

    class Config:
        allow_mutation = False
        extra = Extra.forbid

        def config_method(self) -> None:
            ...


model = Model(x=1, y='y', z='z')
model = Model(x=1)
model.y = 'a'
model.from_orm({})


class ForbidExtraModel(BaseModel):
    class Config:
        extra = 'forbid'


ForbidExtraModel(x=1)


class ForbidExtraModel2(BaseModel):
    class Config:
        extra = 'forbid'
        validate_all = False

    Config.validate_all = True


ForbidExtraModel2(x=1)


class BadExtraModel(BaseModel):
    class Config:
        extra = 1


class BadConfig1(BaseModel):
    class Config:
        orm_mode: Any = {}  # not sensible, but should still be handled gracefully


class BadConfig2(BaseModel):
    class Config:
        orm_mode = list  # not sensible, but should still be handled gracefully


class InheritingModel(Model):
    class Config:
        allow_mutation = True


class DefaultTestingModel(BaseModel):
    # Required
    a: int
    b: int = ...
    c: int = Field(...)
    d: Union[int, str]
    e = ...

    # Not required
    f: Optional[int]
    g: int = 1
    h: int = Field(1)
    i: int = Field(None)
    j = 1


DefaultTestingModel()


class UndefinedAnnotationModel(BaseModel):
    undefined: Undefined  # noqa F821


UndefinedAnnotationModel()

# Strict mode fails
model = Model(x='1', y='2')
inheriting = InheritingModel(x='1', y='1')
