from typing import Any, Generic, List, Optional, Set, TypeVar, Union

from pydantic import BaseModel, Extra, Field, validator, BaseConfig
from pydantic.dataclasses import dataclass
from pydantic.generics import GenericModel


class Model(BaseModel):
    model_config = BaseConfig(alias_generator=None, frozen=True, extra=Extra.forbid)
    x: int
    y: str

    def method(self) -> None:
        pass


model = Model(x=1, y='y', z='z')
model = Model(x=1)
model.y = 'a'
Model.from_orm({})
Model.from_orm({})  # type: ignore[pydantic-orm]  # noqa F821


class ForbidExtraModel(BaseModel):
    model_config = BaseConfig(extra='forbid')  # type: ignore[typeddict-item]


ForbidExtraModel(x=1)


class ForbidExtraModel2(BaseModel):
    model_config = BaseConfig(extra='forbid')  # type: ignore[typeddict-item]


ForbidExtraModel2(x=1)


class BadExtraModel(BaseModel):
    model_config = BaseConfig(
        extra=1,  # type: ignore[pydantic-config]
        extra=1,  # type: ignore[typeddict-item] # noqa E999
    )


class BadConfig1(BaseModel):
    model_config = BaseConfig(from_attributes={})  # type: ignore[typeddict-item]


class BadConfig2(BaseModel):
    model_config = BaseConfig(from_attributes=list)  # type: ignore[typeddict-item]


class InheritingModel(Model):
    model_config = BaseConfig(frozen=False)


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


Model.model_construct(x=1)
Model.model_construct(_fields_set={'x'}, x=1, y='2')
Model.model_construct(x='1', y='2')

# Strict mode fails
inheriting = InheritingModel(x='1', y='1')
Model(x='1', y='2')


class Blah(BaseModel):
    fields_set: Optional[Set[str]] = None


# (comment to keep line numbers unchanged)
T = TypeVar('T')


class Response(GenericModel, Generic[T]):
    data: T
    error: Optional[str]


response = Response[Model](data=model, error=None)
response = Response[Model](data=1, error=None)


class AliasModel(BaseModel):
    x: str = Field(..., alias='y')
    z: int


AliasModel(y=1, z=2)

x_alias = 'y'


class DynamicAliasModel(BaseModel):
    x: str = Field(..., alias=x_alias)
    z: int


DynamicAliasModel(y='y', z='1')


class DynamicAliasModel2(BaseModel):
    x: str = Field(..., alias=x_alias)
    z: int

    model_config = BaseConfig(populate_by_name=True)


DynamicAliasModel2(y='y', z=1)
DynamicAliasModel2(x='y', z=1)


class AliasGeneratorModel(BaseModel):
    x: int

    model_config = BaseConfig(alias_generator=lambda x: x + '_')


AliasGeneratorModel(x=1)
AliasGeneratorModel(x_=1)
AliasGeneratorModel(z=1)


class AliasGeneratorModel2(BaseModel):
    x: int = Field(..., alias='y')

    model_config = BaseConfig(alias_generator=lambda x: x + '_')  # type: ignore[pydantic-alias]


class UntypedFieldModel(BaseModel):
    x: int = 1
    y = 2
    z = 2  # type: ignore[pydantic-field]  # noqa F821


AliasGeneratorModel2(x=1)
AliasGeneratorModel2(y=1, z=1)


class CoverageTester(Missing):  # noqa F821
    def from_orm(self) -> None:
        pass


CoverageTester().from_orm()


@dataclass(config={})
class AddProject:
    name: str
    slug: Optional[str]
    description: Optional[str]


p = AddProject(name='x', slug='y', description='z')


# Same as Model, but with frozen = True
class FrozenModel(BaseModel):
    x: int
    y: str

    model_config = BaseConfig(alias_generator=None, frozen=True, extra=Extra.forbid)


frozenmodel = FrozenModel(x=1, y='b')
frozenmodel.y = 'a'


class InheritingModel2(FrozenModel):
    model_config = BaseConfig(frozen=False)


inheriting2 = InheritingModel2(x=1, y='c')
inheriting2.y = 'd'


def _default_factory() -> str:
    return 'x'


test: List[str] = []


class FieldDefaultTestingModel(BaseModel):
    # Default
    e: int = Field(None)
    f: int = None

    # Default factory
    g: str = Field(default_factory=set)
    h: int = Field(default_factory=_default_factory)
    i: List[int] = Field(default_factory=list)
    l_: str = Field(default_factory=3)

    # Default and default factory
    m: int = Field(default=1, default_factory=list)


class ModelWithAnnotatedValidator(BaseModel):
    name: str

    @validator('name')
    def noop_validator_with_annotations(self, name: str) -> str:
        # This is a mistake: the first argument to a validator is the class itself,
        # like a classmethod.
        self.instance_method()
        return name

    def instance_method(self) -> None:
        ...
