from typing import ClassVar, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, create_model, validator
from pydantic.dataclasses import dataclass


# placeholder for removed line
class Model(BaseModel):
    x: float
    y: str

    model_config = ConfigDict(from_attributes=True)

    not_config = ConfigDict(frozen=True)


class SelfReferencingModel(BaseModel):
    submodel: Optional['SelfReferencingModel']

    @property
    def prop(self) -> None:
        ...


SelfReferencingModel.model_rebuild()

model = Model(x=1, y='y')
Model(x=1, y='y', z='z')
model.x = 2
model.from_orm(model)

self_referencing_model = SelfReferencingModel(submodel=SelfReferencingModel(submodel=None))


class KwargsModel(BaseModel, from_attributes=True):
    x: float
    y: str

    not_config = ConfigDict(frozen=True)


kwargs_model = KwargsModel(x=1, y='y')
KwargsModel(x=1, y='y', z='z')
kwargs_model.x = 2
kwargs_model.from_orm(kwargs_model)


class InheritingModel(Model):
    z: int = 1


InheritingModel.from_orm(model)


class ForwardReferencingModel(Model):
    future: 'FutureModel'


class FutureModel(Model):
    pass


ForwardReferencingModel.model_rebuild()
future_model = FutureModel(x=1, y='a')
forward_model = ForwardReferencingModel(x=1, y='a', future=future_model)


class NoMutationModel(BaseModel):
    x: int

    model_config = ConfigDict(frozen=True)


class MutationModel(NoMutationModel):
    a = 1

    model_config = ConfigDict(frozen=False, from_attributes=True)


MutationModel(x=1).x = 2
MutationModel.from_orm(model)


class KwargsNoMutationModel(BaseModel, frozen=True):
    x: int


class KwargsMutationModel(KwargsNoMutationModel, frozen=False, from_attributes=True):
    a = 1


KwargsMutationModel(x=1).x = 2
KwargsMutationModel.from_orm(model)


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

    model_config = ConfigDict(frozen=True)


class NotFrozenModel(FrozenModel):
    a: int = 1

    model_config = ConfigDict(frozen=False, from_attributes=True)


NotFrozenModel(x=1).x = 2
NotFrozenModel.from_orm(model)


class KwargsFrozenModel(BaseModel, frozen=True):
    x: int


class KwargsNotFrozenModel(FrozenModel, frozen=False, from_attributes=True):
    a: int = 1


KwargsNotFrozenModel(x=1).x = 2
KwargsNotFrozenModel.from_orm(model)


class ModelWithSelfField(BaseModel):
    self: str


def f(name: str) -> str:
    return name


class ModelWithAllowReuseValidator(BaseModel):
    name: str
    _normalize_name = validator('name', allow_reuse=True)(f)


model_with_allow_reuse_validator = ModelWithAllowReuseValidator(name='xyz')


T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    data: T
    error: Optional[str]


response = Response[Model](data=model, error=None)


class ModelWithAnnotatedValidator(BaseModel):
    name: str

    @validator('name')
    def noop_validator_with_annotations(cls, name: str) -> str:
        return name


def _default_factory_str() -> str:
    return 'x'


def _default_factory_list() -> List[int]:
    return [1, 2, 3]


class FieldDefaultTestingModel(BaseModel):
    # Required
    a: int
    b: int = Field()
    c: int = Field(...)

    # Default
    d: int = Field(1)

    # Default factory
    g: List[int] = Field(default_factory=_default_factory_list)
    h: str = Field(default_factory=_default_factory_str)
    i: str = Field(default_factory=lambda: 'test')


_TModel = TypeVar('_TModel')
_TType = TypeVar('_TType')


class OrmMixin(Generic[_TModel, _TType]):
    @classmethod
    def from_orm(cls, model: _TModel) -> _TType:
        raise NotImplementedError

    @classmethod
    def from_orm_optional(cls, model: Optional[_TModel]) -> Optional[_TType]:
        if model is None:
            return None
        return cls.from_orm(model)
