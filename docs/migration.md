---
description: Migrating from Pydantic V1.
---

## Install Pydantic V2 beta

Your feedback will be a critical part of ensuring that we have made the right tradeoffs with the API changes in V2.

To get started with the Pydantic V2 alpha, install it from PyPI.
We recommend using a virtual environment to isolate your testing environment:

```bash
pip install --pre -U "pydantic>=2.0b1"
```

!!! warning "Beta release!"
    Note that there are still some rough edges, and while trying out the Pydantic V2 beta releases you may experience errors.

    We encourage you to try out the beta releases in a test environment and not in production.
    While we do not currently intend to make changes to the API, it's still possible that we
    will discover problems requiring breaking changes.

If you do encounter any issues, please [create an issue in GitHub](https://github.com/pydantic/pydantic/issues) using
the `bug V2` label. This will help us to actively monitor and track errors, and to continue to improve the library's
performance.

## Migration Guide

### Changes to `pydantic.BaseModel`

* Various method names have been changed; all non-deprecated `BaseModel` methods now have names matching either the
  format `model_.*` or `__.*pydantic.*__`. Where possible, we have retained the deprecated methods with their old names
  to help ease migration, but calling them will emit `DeprecationWarning`s.
  * [TODO: Need to add table of method name migrations]
  * Some of the built-in data-loading functionality has been slated for removal. In particular,
    `parse_raw` and `parse_file` are now deprecated. You should load the data and then pass it to `model_validate`.
* The `from_orm` method has been removed; you can now just use `model_validate` (equivalent to `parse_obj` from
  Pydantic V1) to achieve something similar, as long as you've set `from_attributes=True` in the model config.
* The `__eq__` method has changed for models.
  * Models can only be equal to other BaseModel instances.
  * For two model instances to be equal, they must have the same:
    * Type (or, in the case of generic models, non-parametrized generic origin type)
    * Field values
    * Extra values (only relevant when `model_config['extra'] == 'allow'`)
    * Private attribute values
  * In particular:
    * Models are no longer equal to the dicts containing their data.
    * Non-generic models of different types are never equal.
    * Generic models with different origin types are never equal.
      * We don't require *exact* type equality so that, for example,
        instances of `MyGenericModel[Any]` could be equal to instances of `MyGenericModel[int]`.
    * Models with different values of private attributes are no longer equal
* We have replaced the use of the `__root__` field to specify a "custom root model" with a new type called `RootModel`
  which is intended to replace the functionality of using a field called `__root__` in V1.
  * [TODO: Add link to documentation of `RootModel`. For now, you can find example usage in `tests/test_root_model.py`.]
* We have significantly expanded Pydantic's capabilities related to customizing serialization. In particular, we have
  added the `@field_serializer`, `@model_serializer`, and `@computed_field` decorators, which each address various
  shortcomings from Pydantic V1.
  * [TODO: Add link to documentation of serialization decorators. For now, you can find example usage in
      `tests/test_serialize.py` and `tests/test_computed_fields.py`.]
  * Due to performance overhead and implementation complexity, we have now removed support for specifying
    `json_encoders` in the model config. This functionality was originally added for the purpose of achieving custom
    serialization logic, and we think the new serialization decorators are a better choice in most common scenarios.
    However, if your usage of `json_encoders` is not compatible with the new serialization decorators,
    please create a GitHub issue letting us know.

### Changes to `pydantic.generics.GenericModel`
* The `pydantic.generics.GenericModel` class is no longer necessary, and has been removed. Instead, you can now
  create generic BaseModel subclasses by just adding `Generic` as a parent class on a `BaseModel` subclass directly.
  * This looks like `class MyGenericModel(BaseModel, Generic[T]): ...`.
* While it may not raise an error, we strongly advise against using _parametrized_ generics in `isinstance` checks.
  * For example, you should not do `isinstance(my_model, MyGenericModel[int])`.
    However, it is fine to do `isinstance(my_model, MyGenericModel)`.
    * (Note that for standard generics, it would raise an error to do a subclass check with a parameterized generic.)
  * If you need to perform `isinstance` checks against parametrized generics, you can do this by subclassing the
    parametrized generic class.
    * This looks like `class MyIntModel(MyGenericModel[int]): ...` and `isinstance(my_model, MyIntModel)`.
* [TODO: Add link to documentation of generic models. For now, you can find example usage in `tests/test_generics.py`.]


### Changes to `pydantic.Field`
* `Field` no longer supports arbitrary keyword arguments to be added to the JSON schema. Instead, any extra
  data you want to add to the JSON schema should be passed as a dictionary to the `json_schema_extra` keyword argument.
* [TODO: Need to document all other backwards-incompatible changes to pydantic.Field]


### Changes to Dataclasses

* When used as fields, dataclasses (Pydantic or vanilla) no longer accept tuples as validation inputs; dicts should be
  used instead.
* The `__post_init__` in Pydantic dataclasses will now be called _after_ validation, rather than before.
  * As a result, the `__post_init_post_parse__` method would have become redundant, so has been removed.
* We no longer support `extra='allow'` for Pydantic dataclasses, where extra fields passed to the initializer would be
  stored as extra attributes on the dataclass. `extra='ignore'` is still supported for the purpose of ignoring
  unexpected fields while parsing data, they just won't be stored on the instance.
* Pydantic dataclasses no longer have an attribute `__pydantic_model__`, and no longer use an underlying BaseModel
  to perform validation or provide other functionality. To perform validation, generate a JSON schema, or make use of
  any other functionality that may have required `__pydantic_model__` in V1, you should now wrap the dataclass with a
  `TypeAdapter` (discussed more below) and make use of its methods.
  * [TODO: Add link to TypeAdapter documentation. For now, you can find example usage in `tests/test_type_adapter.py`.]
* In V1, if you used a vanilla (i.e., non-Pydantic) dataclass as a field, the config of the parent type would be used
  as though it was the config for the dataclass itself as well. In V2, this is no longer the case.
  * [TODO: Need to specify how to override the config used for vanilla dataclass; possibly need to add functionality?]


### Changes to Config

* To specify config on a model, it is now deprecated to create a class called `Config` in the namespace of the parent
  `BaseModel` subclass. Instead, you should set a class attribute called `model_config` to be a dict with the key/value
  pairs you want to be used as the config.

* The following config settings have been removed:
  * `allow_mutation`.
  * `error_msg_templates`.
  * `fields` — this was the source of various bugs, so has been removed.
    You should be able to use `Annotated` on fields to modify them as desired.
  * `getter_dict` — `orm_mode` has been removed, and this implementation detail is no longer necessary.
  * `schema_extra` — you should now use the `json_schema_extra` keyword argument to `pydantic.Field`.
  * `smart_union`.
  * `underscore_attrs_are_private` — the Pydantic V2 behavior is now the same as if this was always set
    to `True` in Pydantic V1.

* The following config settings have been renamed:
  * `allow_population_by_field_name` → `populate_by_name`
  * `anystr_lower` → `str_to_lower`
  * `anystr_strip_whitespace` → `str_strip_whitespace`
  * `anystr_upper` → `str_to_upper`
  * `keep_untouched` → `ignored_types`
  * `max_anystr_length` → `str_max_length`
  * `min_anystr_length` → `str_min_length`
  * `orm_mode` → `from_attributes`
  * `validate_all` → `validate_default`

### Changes to Validators

#### `@validator` and `@root_validator` are deprecated

* `@validator` has been deprecated, and should be replaced with `@field_validator`, which provides various new features
and improvements.
  * [TODO: Add link to documentation of `@field_validator`]
  * The new `@field_validator` decorator does not have the `each_item` keyword argument; validators you want to
    apply to items within a generic container should be added by annotating the type argument. See
    [validators in Annotated metadata](usage/validators.md#generic-validated-collections) for details.
    * This looks like `List[Annotated[int, Field(ge=0)]]`
  * Even if you keep using the deprecated `@validator` decorator, you can no longer add the `field` or
    `config` arguments to the signature of validator functions. If you need access to these, you'll need
    to migrate to `@field_validator` — see the [next section](#changes-to-validators-allowed-signatures)
    for more details.
  * If you use the `always=True` keyword argument to a validator function, note that standard validators
    for the annotated type will _also_ be applied even to defaults, not just the custom validators. For
    example, despite the fact that the validator below will never error, the following code raises a `ValidationError`:

    ```python
    from pydantic import BaseModel, validator

    class Model(BaseModel):
        x: str = 1

        @validator('x', always=True)
        @classmethod
        def validate_x(cls, v):
            return v

    Model()
    ```

* `@root_validator` has been deprecated, and should be replaced with `@model_validator`, which also provides new
  features and improvements.
  * [TODO: Add link to documentation of `@model_validator`]
  * Under some circumstances (such as assignment when `model_config['validate_assignment'] is True`),
    the `@model_validator` decorator will receive an instance of the model, not a dict of values. You may
    need to be careful to handle this case.
  * Even if you keep using the deprecated `@root_validator` decorator, due to refactors in validation logic,
    you can no longer run with `skip_on_failure=False` (which is the default value of this keyword argument,
    so must be set explicitly to `True`).

#### Changes to `@validator`'s allowed signatures

In V1 functions wrapped by `@validator` could receive keyword arguments with metadata about what was being validated.
Some of these arguments have been removed:

* `config`: Pydantic V2's config is now a dictionary instead of a class, which means this argument is no longer
  backwards compatible. If you need to access the configuration you should migrate to `@field_validator` and use
  `info.config`.
* `field`: this argument used to be a `ModelField` object, which was a quasi-internal class that no longer exists
  in Pydantic V2. Most of this information can still be accessed by using the field name from `info.field_name`
  to index into `cls.model_fields`

```python
from pydantic import BaseModel, FieldValidationInfo, field_validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    def val_x(cls, v: int, info: FieldValidationInfo) -> int:
        assert info.config is not None
        print(info.config.get('title'))
        #> Model
        print(cls.model_fields[info.field_name].is_required())
        #> True
        return v


Model(x=1)
```

#### `TypeError` is no longer converted to `ValidationError` in validators

Previously, when raising a `TypeError` within a validator function, that error would be wrapped into a `ValidationError`
and, in some cases (such as with FastAPI), these errors might be displayed to end users. This led to a variety of
undesirable behavior — for example, calling a function with the wrong signature might produce a user-facing
`ValidationError`.

However, in pydantic V2, when a `TypeError` is raised in a validator it is no longer converted into a `ValidationError`:

```python
import pytest

from pydantic import BaseModel, field_validator  # or validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    def val_x(cls, v: int) -> int:
        return str.lower(v)  # raises a TypeError


with pytest.raises(TypeError):
    Model(x=1)
```

This applies to all validation decorators.

#### The `allow_reuse` keyword argument is no longer necessary

Previously, Pydantic tracked "reused" functions in decorators as this was a common source of mistakes.
We did this by comparing the function's fully qualified name (module name + function name), which could result in false
positives. The `allow_reuse` keyword argument could be used to disable this when it was intentional.

Our approach to detecting repeatedly-defined functions has been overhauled to only error for redefinition within a
single class, reducing false positives and bringing the behavior more in line with the errors that type checkers
and linters would give for defining a method with the same name multiple times in a single class definition.

In nearly all cases, if you were using `allow_reuse=True`, you should be able to simply delete that keyword argument and
have things keep working as expected.

#### `@validate_arguments` has been renamed to `@validate_call`

In V2, the `@validate_arguments` decorator has been renamed to `@validate_call`.

In V1, the decorated function had various attributes added, such as `raw_function`, and `validate` (which could be used
to validate arguments without actually calling the decorated function). Due to limited use of these attributes,
and performance-oriented changes in implementation, we have not preserved this functionality in `@validate_call`.

### Changes to Handling of Standard Types

#### Dict

Iterables of pairs (which include empty iterables) no longer pass validation for fields of type `dict`.

#### Unions
While union types will still attempt validation of each choice from left to right, they now preserve the type of the
input whenever possible, even if the correct type is not the first choice for which the input would pass validation.
As a demonstration, consider the following example:

```python
from pydantic import BaseModel


class Model(BaseModel):
    x: int | str

print(Model(x='1'))
#> x='1'
```

In Pydantic V1, the printed result would have been `x=1`, since the value would pass validation as an `int`.
In V2, we recognize that the value is an instance of one of the cases and short-circuit the standard union validation.

#### Required, Optional, and Nullable fields

Pydantic V1 had a somewhat loose idea about "required" versus "nullable" fields. In Pydantic V2 these concepts are more clearly defined.

Pydantic V2 will move to match `dataclasses`, thus you may explicitly specify a field as `required` or `optional` and whether the field accepts `None` or not.

```py
from typing import Optional

from pydantic import BaseModel, ValidationError


class Foo(BaseModel):
    f1: str  # required, cannot be None
    f2: Optional[str]  # required, can be None - same as Union[str, None] / str | None
    f3: Optional[str] = None  # not required, can be None
    f4: str = 'Foobar'  # not required, but cannot be None


try:
    Foo(f1=None, f2=None, f4='b')
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    f1
      Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
    """
```

### Introduction of TypeAdapter

Pydantic V1 had weak support for validating or serializing non-`BaseModel` types.

To work with them, you had to either create a "root" model or use the utility functions in `pydantic.tools`
(namely, `parse_obj_as` and `schema_of`).

In Pydantic V2 this is _a lot_ easier: the `TypeAdapter` class lets you create an object with methods for validating,
serializing, and producing JSON schemas for arbitrary types. This serves as a complete replacement for `parse_obj_as`
and `schema_of` (which are now deprecated), and also covers some of the use cases of "root" models
(`RootModel`, discussed above, covers the others).

```python
from typing import List

from pydantic import TypeAdapter

adapter = TypeAdapter(List[int])
assert adapter.validate_python(['1', '2', '3']) == [1, 2, 3]
print(adapter.json_schema())
#> {'type': 'array', 'items': {'type': 'integer'}}
```

Due to limitations of inferring generic types with common type checkers, to get proper typing in some scenarios, you
may need to explicitly specify the generic parameter:
```python
from pydantic import TypeAdapter

adapter: TypeAdapter[str | int] = TypeAdapter(str | int)
...
```

[TODO: Add link to TypeAdapter documentation. For now, you can find example usage in `tests/test_type_adapter.py`.]

### Defining Custom Types

We have completely overhauled the way custom types are defined in pydantic.

We have exposed hooks for generating both `pydantic-core` and JSON schemas, allowing you to get all the performance
benefits of Pydantic V2 even when using your own custom types.

We have also introduced ways to use `typing.Annotated` to add custom validation to your own types.

The main changes are:
* `__get_validators__` should be replaced with `__get_pydantic_core_schema__`
  * [TODO: Add link to documentation of `__get_pydantic_core_schema__`]
* `__modify_schema__` becomes `__get_pydantic_json_schema__`
  * [TODO: Add link to documentation of `__get_pydantic_json_schema__`]

Additionally, you can use `typing.Annotated` to modify or provide the `__get_pydantic_core_schema__` and
`__get_pydantic_json_schema__` functions of a type by annotating it, rather than modifying the type itself.
This provides a powerful and flexible mechanism for integrating third party types with Pydantic, and in some cases
may help you remove hacks from v1 introduced to work around the limitations for custom types.

[TODO: Add link to full documentation for custom types, including `__prepare_pydantic_annotations__` etc.]

### Changes to JSON schema generation

We received many requests over the years to make changes to the JSON schemas that pydantic generates.

In V2, we have tried to address many of the common requests:

* The JSON schema for `Optional` fields now indicates that the value `null` is allowed
* The `Decimal` type is now exposed in JSON schema (and serialized) as a string
* The JSON schema we generate by default now targets draft 2020-12 (with some OpenAPI extensions).
* When they differ, you can now specify if you want the JSON schema representing the inputs to validation,
  or the outputs from serialization.

However, there have been many reasonable requests over the years for changes which we have not chosen to implement.

In V1, even if you were willing to implement changes yourself, it was very difficult because the JSON schema
generation process involved various recursive function calls; to override one, you'd have to copy and modify the whole
implementation.

In V2, one of our design goals was to make it easier to customize JSON schema generation. To this end, we have
introduced the class `GenerateJsonSchema` which implements the translation of a type's pydantic-core schema into
a JSON schema. By design, this class breaks the JSON schema generation process into smaller methods that can be
easily overridden in subclasses to modify the "global" approach to generating JSON schema.

The various methods that can be used to produce JSON schema (such as `BaseModel.model_json_schema` or
`TypeAdapter.json_schema`) accept a keyword argument `schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema`,
and you can pass your custom subclass to these methods in order to use your own approach to generating JSON schema.

Hopefully this means that if you disagree with any of the choices we've made, or if you are reliant on behaviors in V1
that have changed in V2, you can use a custom `schema_generator`, modifying the `GenerateJsonSchema` class as necessary
for your application.

[TODO: Add link to documentation of `GenerateJsonSchema`]
