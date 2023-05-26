from typing import Any, ClassVar, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator, model_validator, validator
from pydantic.dataclasses import dataclass


# placeholder for removed line
class Model(BaseModel):
    x: float
    y: str

    model_config = ConfigDict(from_attributes=True)


class SelfReferencingModel(BaseModel):
    submodel: Optional['SelfReferencingModel']

    @property
    def prop(self) -> None:
        ...


SelfReferencingModel.model_rebuild()

model = Model(x=1, y='y')
Model(x=1, y='y', z='z')
model.x = 2
model.model_validate(model)

self_referencing_model = SelfReferencingModel(submodel=SelfReferencingModel(submodel=None))


class KwargsModel(BaseModel, from_attributes=True):
    x: float
    y: str


kwargs_model = KwargsModel(x=1, y='y')
KwargsModel(x=1, y='y', z='z')
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

    model_config = ConfigDict(frozen=True)


class MutationModel(NoMutationModel):
    a: int = 1

    model_config = ConfigDict(frozen=False, from_attributes=True)


MutationModel(x=1).x = 2
MutationModel.model_validate(model.__dict__)


class KwargsNoMutationModel(BaseModel, frozen=True):
    x: int


class KwargsMutationModel(KwargsNoMutationModel, frozen=False, from_attributes=True):
    a: int = 1


KwargsMutationModel(x=1).x = 2
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


@dataclass(config={'validate_assignment': True})
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


import sys  # noqa E402

if sys.version_info >= (3, 8):
    from dataclasses import InitVar  # E402

    InitVarStr = InitVar[str]
else:
    # InitVar is not supported in 3.7 due to loss of type information
    InitVarStr = str


@dataclass
class MyDataClass:
    foo: InitVarStr
    bar: str


MyDataClass(foo='foo', bar='bar')


def get_my_custom_validator(field_name: str) -> Any:
    @validator(field_name, allow_reuse=True)
    def my_custom_validator(cls: Any, v: int) -> int:
        return v

    return my_custom_validator


def foo() -> None:
    class MyModel(BaseModel):
        number: int
        custom_validator = get_my_custom_validator('number')  # type: ignore[pydantic-field]

        @model_validator(mode='before')
        @classmethod
        def validate_values(cls, values: Any) -> Any:
            return values

    MyModel(number=2)
