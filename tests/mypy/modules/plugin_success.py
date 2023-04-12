from typing import Any, ClassVar, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, BaseSettings, Field, create_model, validator
from pydantic.dataclasses import dataclass
from pydantic.generics import GenericModel


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


class ModelWithSelfField(BaseModel):
    self: str


class SettingsModel(BaseSettings):
    pass


settings = SettingsModel.construct()


def f(name: str) -> str:
    return name


class ModelWithAllowReuseValidator(BaseModel):
    name: str
    _normalize_name = validator('name', allow_reuse=True)(f)


model_with_allow_reuse_validator = ModelWithAllowReuseValidator(name='xyz')


T = TypeVar('T')


class Response(GenericModel, Generic[T]):
    data: T
    error: Optional[str]


response = Response[Model](data=model, error=None)


class ModelWithAnnotatedValidator(BaseModel):
    name: str

    @validator('name')
    def noop_validator_with_annotations(cls, name: str) -> str:
        return name


def _default_factory_str() -> str:
    ...


def _default_factory_list() -> List[int]:
    ...


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


# Include the import down here to reduce the effect on line numbers
from dataclasses import InitVar  # noqa E402


@dataclass
class MyDataClass:
    foo: InitVar[str]
    bar: str


MyDataClass(foo='foo', bar='bar')


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


class Sample(BaseModel):
    foo: str
    bar: Optional[str] = Field(description='optional')
    zoo: Any


Sample(foo='hello world')


def get_my_custom_validator(field_name: str) -> Any:
    @validator(field_name, allow_reuse=True)
    def my_custom_validator(cls: Any, v: int) -> int:
        return v

    return my_custom_validator


def foo() -> None:
    class MyModel(BaseModel):
        number: int
        custom_validator = get_my_custom_validator('number')

    MyModel(number=2)
