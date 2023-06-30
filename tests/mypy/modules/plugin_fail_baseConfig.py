from typing import Any, Generic, List, Optional, Set, TypeVar, Union

from pydantic import BaseModel, Extra, Field, field_validator
from pydantic.dataclasses import dataclass


class Model(BaseModel):
    x: int
    y: str

    def method(self) -> None:
        pass

    class Config:
        alias_generator = None
        frozen = True
        extra = Extra.forbid

        def config_method(self) -> None:
            ...


model = Model(x=1, y='y', z='z')
model = Model(x=1)
model.y = 'a'
Model.from_orm({})


class KwargsModel(BaseModel, alias_generator=None, frozen=True, extra=Extra.forbid):
    x: int
    y: str

    def method(self) -> None:
        pass


kwargs_model = KwargsModel(x=1, y='y', z='z')
kwargs_model = KwargsModel(x=1)
kwargs_model.y = 'a'
KwargsModel.from_orm({})


class ForbidExtraModel(BaseModel):
    class Config:
        extra = 'forbid'


ForbidExtraModel(x=1)


class KwargsForbidExtraModel(BaseModel, extra='forbid'):
    pass


KwargsForbidExtraModel(x=1)


class BadExtraModel(BaseModel):
    class Config:
        extra = 1  # type: ignore[pydantic-config]
        extra = 1


class KwargsBadExtraModel(BaseModel, extra=1):
    pass


class BadConfig1(BaseModel):
    class Config:
        from_attributes: Any = {}  # not sensible, but should still be handled gracefully


class KwargsBadConfig1(BaseModel, from_attributes={}):
    pass


class BadConfig2(BaseModel):
    class Config:
        from_attributes = list  # not sensible, but should still be handled gracefully


class KwargsBadConfig2(BaseModel, from_attributes=list):
    pass


class InheritingModel(Model):
    class Config:
        frozen = False


class KwargsInheritingModel(KwargsModel, frozen=False):
    pass


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


class Response(BaseModel, Generic[T]):
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

    class Config:
        populate_by_name = True


DynamicAliasModel2(y='y', z=1)
DynamicAliasModel2(x='y', z=1)


class KwargsDynamicAliasModel(BaseModel, populate_by_name=True):
    x: str = Field(..., alias=x_alias)
    z: int


KwargsDynamicAliasModel(y='y', z=1)
KwargsDynamicAliasModel(x='y', z=1)


class AliasGeneratorModel(BaseModel):
    x: int

    class Config:
        alias_generator = lambda x: x + '_'  # noqa E731


AliasGeneratorModel(x=1)
AliasGeneratorModel(x_=1)
AliasGeneratorModel(z=1)


class AliasGeneratorModel2(BaseModel):
    x: int = Field(..., alias='y')

    class Config:  # type: ignore[pydantic-alias]
        alias_generator = lambda x: x + '_'  # noqa E731


class UntypedFieldModel(BaseModel):
    x: int = 1
    y = 2
    z = 2  # type: ignore[pydantic-field]


AliasGeneratorModel2(x=1)
AliasGeneratorModel2(y=1, z=1)


class KwargsAliasGeneratorModel(BaseModel, alias_generator=lambda x: x + '_'):
    x: int


KwargsAliasGeneratorModel(x=1)
KwargsAliasGeneratorModel(x_=1)
KwargsAliasGeneratorModel(z=1)


class KwargsAliasGeneratorModel2(BaseModel, alias_generator=lambda x: x + '_'):
    x: int = Field(..., alias='y')


KwargsAliasGeneratorModel2(x=1)
KwargsAliasGeneratorModel2(y=1, z=1)


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

    class Config:
        alias_generator = None
        frozen = True
        extra = Extra.forbid


frozenmodel = FrozenModel(x=1, y='b')
frozenmodel.y = 'a'


class InheritingModel2(FrozenModel):
    class Config:
        frozen = False


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

    @field_validator('name')
    def noop_validator_with_annotations(self, name: str) -> str:
        # This is a mistake: the first argument to a validator is the class itself,
        # like a classmethod.
        self.instance_method()
        return name

    def instance_method(self) -> None:
        ...
