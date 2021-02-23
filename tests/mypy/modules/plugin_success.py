from typing import ClassVar, Optional, Union

from pydantic import BaseModel, Field, create_model
from pydantic.dataclasses import dataclass


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


class Config:
    validate_assignment = True


@dataclass(config=Config)
class AddProject:
    name: str
    slug: Optional[str]
    description: Optional[str]


p = AddProject(name='x', slug='y', description='z')


class TypeAliasAsAttribute(BaseModel):
    __type_alias_attribute__ = Union[str, bytes]


class NestedModel(BaseModel):
    class Model(BaseModel):
        id: str

    model: Model


_ = NestedModel.Model


DynamicModel = create_model('DynamicModel', __base__=Model)

dynamic_model = DynamicModel(x=1, y='y')
dynamic_model.x = 2


class FrozenModel(BaseModel):
    x: int

    class Config:
        frozen = True


class NotFrozenModel(FrozenModel):
    a: int = 1

    class Config:
        frozen = False
        orm_mode = True


NotFrozenModel(x=1).x = 2
NotFrozenModel.from_orm(model)
