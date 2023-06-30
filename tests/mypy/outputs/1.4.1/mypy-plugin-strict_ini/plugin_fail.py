from typing import Generic, List, Optional, Set, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Extra, Field, field_validator
from pydantic.dataclasses import dataclass


class Model(BaseModel):
    model_config = ConfigDict(alias_generator=None, frozen=True, extra=Extra.forbid)
    x: int
    y: str

    def method(self) -> None:
        pass


model = Model(x=1, y='y', z='z')
# MYPY: error: Unexpected keyword argument "z" for "Model"  [call-arg]
model = Model(x=1)
# MYPY: error: Missing named argument "y" for "Model"  [call-arg]
model.y = 'a'
# MYPY: error: Property "y" defined in "Model" is read-only  [misc]
Model.from_orm({})
# MYPY: error: "Model" does not have from_attributes=True  [pydantic-orm]


class KwargsModel(BaseModel, alias_generator=None, frozen=True, extra=Extra.forbid):
    x: int
    y: str

    def method(self) -> None:
        pass


kwargs_model = KwargsModel(x=1, y='y', z='z')
# MYPY: error: Unexpected keyword argument "z" for "KwargsModel"  [call-arg]
kwargs_model = KwargsModel(x=1)
# MYPY: error: Missing named argument "y" for "KwargsModel"  [call-arg]
kwargs_model.y = 'a'
# MYPY: error: Property "y" defined in "KwargsModel" is read-only  [misc]
KwargsModel.from_orm({})
# MYPY: error: "KwargsModel" does not have from_attributes=True  [pydantic-orm]


class ForbidExtraModel(BaseModel):
    model_config = ConfigDict(extra=Extra.forbid)


ForbidExtraModel(x=1)
# MYPY: error: Unexpected keyword argument "x" for "ForbidExtraModel"  [call-arg]


class KwargsForbidExtraModel(BaseModel, extra='forbid'):
    pass


KwargsForbidExtraModel(x=1)
# MYPY: error: Unexpected keyword argument "x" for "KwargsForbidExtraModel"  [call-arg]


class BadExtraModel(BaseModel):
    model_config = ConfigDict(extra=1)  # type: ignore[typeddict-item]
# MYPY: error: Invalid value for "Config.extra"  [pydantic-config]
# MYPY: note: Error code "pydantic-config" not covered by "type: ignore" comment


class BadExtraButIgnoredModel(BaseModel):
    model_config = ConfigDict(extra=1)  # type: ignore[typeddict-item,pydantic-config]


class KwargsBadExtraModel(BaseModel, extra=1):
# MYPY: error: Invalid value for "Config.extra"  [pydantic-config]
    pass


class BadConfig1(BaseModel):
    model_config = ConfigDict(from_attributes={})  # type: ignore[typeddict-item]
# MYPY: error: Invalid value for "Config.from_attributes"  [pydantic-config]
# MYPY: note: Error code "pydantic-config" not covered by "type: ignore" comment


class KwargsBadConfig1(BaseModel, from_attributes={}):
# MYPY: error: Invalid value for "Config.from_attributes"  [pydantic-config]
    pass


class BadConfig2(BaseModel):
    model_config = ConfigDict(from_attributes=list)  # type: ignore[typeddict-item]
# MYPY: error: Invalid value for "Config.from_attributes"  [pydantic-config]
# MYPY: note: Error code "pydantic-config" not covered by "type: ignore" comment


class KwargsBadConfig2(BaseModel, from_attributes=list):
# MYPY: error: Invalid value for "Config.from_attributes"  [pydantic-config]
    pass


class InheritingModel(Model):
    model_config = ConfigDict(frozen=False)


class KwargsInheritingModel(KwargsModel, frozen=False):
    pass


class DefaultTestingModel(BaseModel):
    # Required
    a: int
    b: int = ...
# MYPY: error: Incompatible types in assignment (expression has type "ellipsis", variable has type "int")  [assignment]
    c: int = Field(...)
    d: Union[int, str]
    e = ...
# MYPY: error: Untyped fields disallowed  [pydantic-field]

    # Not required
    f: Optional[int]
    g: int = 1
    h: int = Field(1)
    i: int = Field(None)
# MYPY: error: Incompatible types in assignment (expression has type "None", variable has type "int")  [assignment]
    j = 1
# MYPY: error: Untyped fields disallowed  [pydantic-field]


DefaultTestingModel()
# MYPY: error: Missing named argument "a" for "DefaultTestingModel"  [call-arg]
# MYPY: error: Missing named argument "b" for "DefaultTestingModel"  [call-arg]
# MYPY: error: Missing named argument "c" for "DefaultTestingModel"  [call-arg]
# MYPY: error: Missing named argument "d" for "DefaultTestingModel"  [call-arg]
# MYPY: error: Missing named argument "f" for "DefaultTestingModel"  [call-arg]


class UndefinedAnnotationModel(BaseModel):
    undefined: Undefined  # noqa F821
# MYPY: error: Name "Undefined" is not defined  [name-defined]


UndefinedAnnotationModel()
# MYPY: error: Missing named argument "undefined" for "UndefinedAnnotationModel"  [call-arg]


Model.model_construct(x=1)
# MYPY: error: Missing named argument "y" for "model_construct" of "Model"  [call-arg]
Model.model_construct(_fields_set={'x'}, x=1, y='2')
Model.model_construct(x='1', y='2')
# MYPY: error: Argument "x" to "model_construct" of "Model" has incompatible type "str"; expected "int"  [arg-type]

# Strict mode fails
inheriting = InheritingModel(x='1', y='1')
# MYPY: error: Argument "x" to "InheritingModel" has incompatible type "str"; expected "int"  [arg-type]
Model(x='1', y='2')
# MYPY: error: Argument "x" to "Model" has incompatible type "str"; expected "int"  [arg-type]


class Blah(BaseModel):
    fields_set: Optional[Set[str]] = None


# (comment to keep line numbers unchanged)
T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    data: T
    error: Optional[str]


response = Response[Model](data=model, error=None)
response = Response[Model](data=1, error=None)
# MYPY: error: Argument "data" to "Response" has incompatible type "int"; expected "Model"  [arg-type]


class AliasModel(BaseModel):
    x: str = Field(..., alias='y')
    z: int


AliasModel(y=1, z=2)
# MYPY: error: Argument "y" to "AliasModel" has incompatible type "int"; expected "str"  [arg-type]

x_alias = 'y'


class DynamicAliasModel(BaseModel):
    x: str = Field(..., alias=x_alias)
# MYPY: error: Required dynamic aliases disallowed  [pydantic-alias]
    z: int


DynamicAliasModel(y='y', z='1')
# MYPY: error: Argument "z" to "DynamicAliasModel" has incompatible type "str"; expected "int"  [arg-type]


class DynamicAliasModel2(BaseModel):
    x: str = Field(..., alias=x_alias)
    z: int

    model_config = ConfigDict(populate_by_name=True)


DynamicAliasModel2(y='y', z=1)
# MYPY: error: Unexpected keyword argument "y" for "DynamicAliasModel2"  [call-arg]
DynamicAliasModel2(x='y', z=1)


class KwargsDynamicAliasModel(BaseModel, populate_by_name=True):
    x: str = Field(..., alias=x_alias)
    z: int


KwargsDynamicAliasModel(y='y', z=1)
# MYPY: error: Unexpected keyword argument "y" for "KwargsDynamicAliasModel"  [call-arg]
KwargsDynamicAliasModel(x='y', z=1)


class AliasGeneratorModel(BaseModel):
# MYPY: error: Required dynamic aliases disallowed  [pydantic-alias]
    x: int

    model_config = ConfigDict(alias_generator=lambda x: x + '_')
# MYPY: error: Required dynamic aliases disallowed  [pydantic-alias]


AliasGeneratorModel(x=1)
AliasGeneratorModel(x_=1)
AliasGeneratorModel(z=1)


class AliasGeneratorModel2(BaseModel):
# MYPY: error: Required dynamic aliases disallowed  [pydantic-alias]
    x: int = Field(..., alias='y')

    model_config = ConfigDict(alias_generator=lambda x: x + '_')  # type: ignore[pydantic-alias]


class UntypedFieldModel(BaseModel):
    x: int = 1
    y = 2
# MYPY: error: Untyped fields disallowed  [pydantic-field]
    z = 2  # type: ignore[pydantic-field]


AliasGeneratorModel2(x=1)
# MYPY: error: Unexpected keyword argument "x" for "AliasGeneratorModel2"  [call-arg]
AliasGeneratorModel2(y=1, z=1)
# MYPY: error: Unexpected keyword argument "z" for "AliasGeneratorModel2"  [call-arg]


class KwargsAliasGeneratorModel(BaseModel, alias_generator=lambda x: x + '_'):
# MYPY: error: Required dynamic aliases disallowed  [pydantic-alias]
    x: int
# MYPY: error: Required dynamic aliases disallowed  [pydantic-alias]


KwargsAliasGeneratorModel(x=1)
KwargsAliasGeneratorModel(x_=1)
KwargsAliasGeneratorModel(z=1)


class KwargsAliasGeneratorModel2(BaseModel, alias_generator=lambda x: x + '_'):
# MYPY: error: Required dynamic aliases disallowed  [pydantic-alias]
    x: int = Field(..., alias='y')
# MYPY: error: Required dynamic aliases disallowed  [pydantic-alias]


KwargsAliasGeneratorModel2(x=1)
# MYPY: error: Unexpected keyword argument "x" for "KwargsAliasGeneratorModel2"  [call-arg]
KwargsAliasGeneratorModel2(y=1, z=1)
# MYPY: error: Unexpected keyword argument "z" for "KwargsAliasGeneratorModel2"  [call-arg]


class CoverageTester(Missing):  # noqa F821
# MYPY: error: Name "Missing" is not defined  [name-defined]
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

    model_config = ConfigDict(alias_generator=None, frozen=True, extra=Extra.forbid)


frozenmodel = FrozenModel(x=1, y='b')
frozenmodel.y = 'a'
# MYPY: error: Property "y" defined in "FrozenModel" is read-only  [misc]


class InheritingModel2(FrozenModel):
    model_config = ConfigDict(frozen=False)


inheriting2 = InheritingModel2(x=1, y='c')
inheriting2.y = 'd'


def _default_factory() -> str:
    return 'x'


test: List[str] = []


class FieldDefaultTestingModel(BaseModel):
    # Default
    e: int = Field(None)
# MYPY: error: Incompatible types in assignment (expression has type "None", variable has type "int")  [assignment]
    f: int = None
# MYPY: error: Incompatible types in assignment (expression has type "None", variable has type "int")  [assignment]

    # Default factory
    g: str = Field(default_factory=set)
# MYPY: error: Incompatible types in assignment (expression has type "set[Any]", variable has type "str")  [assignment]
    h: int = Field(default_factory=_default_factory)
# MYPY: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]
    i: List[int] = Field(default_factory=list)
    l_: str = Field(default_factory=3)
# MYPY: error: Argument "default_factory" to "Field" has incompatible type "int"; expected "Callable[[], Any] | None"  [arg-type]

    # Default and default factory
    m: int = Field(default=1, default_factory=list)
# MYPY: error: Field default and default_factory cannot be specified together  [pydantic-field]


class ModelWithAnnotatedValidator(BaseModel):
    name: str

    @field_validator('name')
    def noop_validator_with_annotations(self, name: str) -> str:
        # This is a mistake: the first argument to a validator is the class itself,
        # like a classmethod.
        self.instance_method()
# MYPY: error: Missing positional argument "self" in call to "instance_method" of "ModelWithAnnotatedValidator"  [call-arg]
        return name

    def instance_method(self) -> None:
        ...
