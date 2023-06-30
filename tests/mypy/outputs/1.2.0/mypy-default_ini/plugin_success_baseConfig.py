from typing import ClassVar, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field, create_model, field_validator
from pydantic.dataclasses import dataclass


class Model(BaseModel):
    x: float
    y: str

    model_config = dict(from_attributes=True)

    class NotConfig:
        frozen = True


class SelfReferencingModel(BaseModel):
    submodel: Optional['SelfReferencingModel']

    @property
    def prop(self) -> None:
        ...


SelfReferencingModel.model_rebuild()

model = Model(x=1, y='y')
Model(x=1, y='y', z='z')
# MYPY: error: Unexpected keyword argument "z" for "Model"  [call-arg]
model.x = 2
model.model_validate(model)

self_referencing_model = SelfReferencingModel(submodel=SelfReferencingModel(submodel=None))


class KwargsModel(BaseModel, from_attributes=True):
    x: float
    y: str

    class NotConfig:
        frozen = True


kwargs_model = KwargsModel(x=1, y='y')
KwargsModel(x=1, y='y', z='z')
# MYPY: error: Unexpected keyword argument "z" for "KwargsModel"  [call-arg]
kwargs_model.x = 2
kwargs_model.model_validate(kwargs_model.__dict__)


class InheritingModel(Model):
    z: int = 1


InheritingModel.model_validate(model.__dict__)


class ForwardReferencingModel(Model):
    future: 'FutureModel'


class FutureModel(Model):
    pass


ForwardReferencingModel.model_rebuild()
future_model = FutureModel(x=1, y='a')
forward_model = ForwardReferencingModel(x=1, y='a', future=future_model)


class NoMutationModel(BaseModel):
    x: int

    model_config = dict(frozen=True)


class MutationModel(NoMutationModel):
    a: int = 1

    model_config = dict(frozen=False, from_attributes=True)


MutationModel(x=1).x = 2
MutationModel.model_validate(model.__dict__)


class KwargsNoMutationModel(BaseModel, frozen=True):
    x: int


class KwargsMutationModel(KwargsNoMutationModel, frozen=False, from_attributes=True):
# MYPY: error: Cannot inherit non-frozen dataclass from a frozen one  [misc]
    a: int = 1


KwargsMutationModel(x=1).x = 2
# MYPY: error: Property "x" defined in "KwargsNoMutationModel" is read-only  [misc]
KwargsMutationModel.model_validate(model.__dict__)


class OverrideModel(Model):
    x: int


OverrideModel(x=1, y='b')


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


@dataclass(config=dict(validate_assignment=True))
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

    model_config = dict(frozen=True)


class NotFrozenModel(FrozenModel):
    a: int = 1

    model_config = dict(frozen=False, from_attributes=True)


NotFrozenModel(x=1).x = 2
NotFrozenModel.model_validate(model.__dict__)


class KwargsFrozenModel(BaseModel, frozen=True):
    x: int


class KwargsNotFrozenModel(FrozenModel, frozen=False, from_attributes=True):
    a: int = 1


KwargsNotFrozenModel(x=1).x = 2
KwargsNotFrozenModel.model_validate(model.__dict__)


class ModelWithSelfField(BaseModel):
    self: str


def f(name: str) -> str:
    return name


class ModelWithAllowReuseValidator(BaseModel):
    name: str
    normalize_name = field_validator('name')(f)


model_with_allow_reuse_validator = ModelWithAllowReuseValidator(name='xyz')


T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    data: T
    error: Optional[str]


response = Response[Model](data=model, error=None)


class ModelWithAnnotatedValidator(BaseModel):
    name: str

    @field_validator('name')
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
