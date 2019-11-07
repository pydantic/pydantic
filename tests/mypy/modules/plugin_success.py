from typing import ClassVar, Optional

from pydantic import BaseModel, Field


class Model(BaseModel):
    x: float
    y: str

    class Config:
        orm_mode = True

    class NotConfig:
        allow_mutation = False


class SelfReferencingModel(BaseModel):
    submodel: Optional['SelfReferencingModel']

    @property
    def prop(self) -> None:
        ...


SelfReferencingModel.update_forward_refs()

model = Model(x=1, y='y')
Model(x=1, y='y', z='z')
model.x = 2
model.from_orm(model)

self_referencing_model = SelfReferencingModel(submodel=SelfReferencingModel(submodel=None))


class InheritingModel(Model):
    z: int = 1


InheritingModel.from_orm(model)


class ForwardReferencingModel(Model):
    future: 'FutureModel'


class FutureModel(Model):
    pass


ForwardReferencingModel.update_forward_refs()
future_model = FutureModel(x=1, y='a')
forward_model = ForwardReferencingModel(x=1, y='a', future=future_model)


class NoMutationModel(BaseModel):
    x: int

    class Config:
        allow_mutation = False


class MutationModel(NoMutationModel):
    a = 1

    class Config:
        allow_mutation = True
        orm_mode = True


MutationModel(x=1).x = 2
MutationModel.from_orm(model)


class OverrideModel(Model):
    x: int


OverrideModel(x=1.5, y='b')


class Mixin:
    def f(self) -> None:
        pass


class MultiInheritanceModel(BaseModel, Mixin):
    pass


MultiInheritanceModel().f()


class AliasModel(BaseModel):
    x: str = Field(..., alias='y')


alias_model = AliasModel(y='hello')
assert alias_model.x == 'hello'


class ClassVarModel(BaseModel):
    x: int
    y: ClassVar[int] = 1


ClassVarModel(x=1)
