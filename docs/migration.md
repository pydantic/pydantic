---
description: Migrating from Pydantic V1.
---

## Install Pydantic V2 alpha

Your feedback will be a critical part of ensuring that we have made the right tradeoffs with the API changes in V2.

To get started with the Pydantic V2 alpha, install it from PyPI.
We recommend using a virtual environment to isolate your testing environment:

```bash
pip install --pre -U "pydantic>=2.0a1"
```

!!! warning "Alpha release!"
    Note that there are still some rough edges and incomplete features, and while trying out the Pydantic V2 alpha releases you may experience errors.

    We encourage you to try out the alpha releases in a test environment and not in production.
    Some features are still in development, and we will continue to make changes to the API.

If you do encounter any issues, please [create an issue in GitHub](https://github.com/pydantic/pydantic/issues) using the `bug V2` label.
This will help us to actively monitor and track errors, and to continue to improve the library’s performance.

## Migration notes

**Please note:** this is just the beginning of a migration guide. We'll work hard up to the final release to prepare
a full migration guide, but for now the following pointers should be some help while experimenting with V2.

### Changes to BaseModel

* Various method names have been changed; `BaseModel` methods all start with `model_` now.
  Where possible, we have retained the old method names to help ease migration, but calling them will result in `DeprecationWarning`s.
  * Some of the built-in data loading functionality has been slated for removal.
    In particular, `parse_raw` and `parse_file` are now deprecated. You should load the data and then pass it to `model_validate`.
* The `from_orm` method has been removed; you can now just use `model_validate` (equivalent to `parse_obj` from Pydantic V1) to achieve something similar,
  as long as you've set `from_attributes=True` in the model config.
* The `__eq__` method has changed for models; models are no longer considered equal to the dicts.
* Custom `__init__` overrides won't be called. This should be replaced with a `@root_validator`.
* Due to inconsistency with the rest of the library, we have removed the special behavior of models
  using the `__root__` field, and have disallowed the use of an attribute with this name to prevent confusion.
  However, you can achieve equivalent behavior with a "standard" field name through the use of `@root_validator`,
  `@model_serializer`, and `__get_pydantic_json_schema__`. You can see an example of this
  [here](https://github.com/pydantic/pydantic/blob/2b9459f20d094a46fa3093b43c34444240f03646/tests/test_parse.py#L95-L113).

### Changes to Pydantic Dataclasses

* The `__post_init__` in Pydantic dataclasses will now be called after validation, rather than before.
* We no longer support `extra='allow'` for Pydantic dataclasses, where extra attributes passed to the initializer would be
  stored as extra fields on the dataclass. `extra='ignore'` is still supported for the purposes of allowing extra fields while parsing data; they just aren't stored.
* `__post_init_post_parse__` has been removed.
* Nested dataclasses no longer accept tuples as input, only dict.

### Changes to Config

* To specify config on a model, it is now deprecated to create a class called `Config` in the namespace of the parent `BaseModel` subclass.
  Instead, you just need to set a class attribute called `model_config` to be a dict with the key/value pairs you want to be used as the config.

The following config settings have been removed:

* `allow_mutation`.
* `error_msg_templates`.
* `fields` — this was the source of various bugs, so has been removed. You should be able to use `Annotated` on fields to modify them as desired.
* `getter_dict` — `orm_mode` has been removed, and this implementation detail is no longer necessary.
* `schema_extra` — you should now use the `json_schema_extra` keyword argument to `pydantic.Field`.
* `smart_union`.
* `underscore_attrs_are_private` — the Pydantic V2 behavior is now the same as if this was always set to `True` in Pydantic V1.

The following config settings have been renamed:

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

Pydantic V2 introduces many new features and improvements to validators.
Most of these features are only available by using a new set of decorators:

* `@field_validator`, which replaces `@validator`
* `@model_validator`, which replaces `@root_validator`

The following sections list some general changes and some changes specific to individual decorators.

#### `TypeError` no longer gets converted into a `ValidationError`

Previously raising `TypeError` within a validator function wrapped that error into a `ValidationError` and, in the case of use facing errors like in FastAPI, would display those errors to users.
This lead to a variety of bugs, for example calling a function with the wrong signature:

```python
import pytest

from pydantic import BaseModel, field_validator  # or pydantic.validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    def val_x(cls, v: int) -> int:
        return str.lower(v)  # raises a TypeError


with pytest.raises(TypeError):
    Model(x=1)
```

This applies to all validators.

### Validate without calling the function

Previously, arguments validation was done by directly calling the decorated function with parameters.
When validating them without *actually* calling the function, you could call the `validate` method bound to the
decorated function.

This functionality no longer exists.

### `each_item` is deprecated

For `@validator` the argument is still present and functions.
For `@field_validator` it is not present at all.
As you migrate from `@validator` to `@field_validator` you will have to replace `each_item=True` with [validators in Annotated metadata](usage/validators.md#generic-validated-collections).

### `@root_validator(skip_on_failure=False)` is no longer allowed

Since this was the default value in V1 you will need to explicitly pass `skip_on_failure=False` for `pre=False` (the default) validators.

### `allow_reuse` is deprecated

Previously Pydantic tracked re-used functions in decorators to help you avoid some common mistakes.
We did this by comparing the function's fully qualified name (module name + function name).
That system has been replaced with a system that tracks things at a per-class level, reducing false positives and bringing the behavior more in line with the errors that type checkers and linters give for overriding a method with another in a class definition.

It is highly likely that if you were using `allow_reuse=True` you can simply delete the parameter and things will work as expected.

For `@validator` this argument is still present but does nothing and emits a deprecation warning.
It is not present on `@field_validator`.

### Changes to `@validator`'s allowed signatures

In V1 functions wrapped by `@validator` could receive keyword arguments with metadata about what was being validated.
Some of these arguments have been removed:

* `config`: Pydantic V2's config is now a dictionary instead of a class, which means this argument is no longer backwards compatible. If you need to access the configuration you should migrate to `@field_validator` and use `info.config`.
* `field`: this argument used to be a `ModelField` object, which was a quasi-internal class that no longer exists in Pydantic V2. Most of this information can still be accessed by using the field name from `info.field_name` to index into `cls.model_fields`

```python
from pydantic import BaseModel, FieldValidationInfo
from pydantic.validators import field_validator


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

### Removed validator types

* The `stricturl` type has been removed.

### Changes to Validation of specific types

* Integers outside the valid range of 64 bit integers will cause `ValidationError`s during parsing.
  To work around this, use an `IsInstance` validator (more details to come).
* Subclasses of built-ins won't validate into their subclass types; you'll need to use an `IsInstance` validator to validate these types.

### Changes to Generic models

* While it does not raise an error at runtime yet, subclass checks for parametrized generics should no longer be used.
  These will result in `TypeError`s and we can't promise they will work forever. However, it will be okay to do subclass checks against _non-parametrized_ generic models

### TypeAdapter

Pydantic V1 didn't have good support for validation or serializing non-`BaseModel`.
To work with them you had to create a "root" model or use the utility functions in `pydantic.tools` (`parse_obj_as` and `schema_of`).
In Pydantic V2 this is _a lot_ easier: the `TypeAdapter` class lets you build an object that behaves almost like a `BaseModel` class which you can use for a lot of the use cases of root models and as a complete replacement for `parse_obj_as` and `schema_of`.

```python
from typing import List

from pydantic import TypeAdapter

validator = TypeAdapter(List[int])
assert validator.validate_python(['1', '2', '3']) == [1, 2, 3]
print(validator.json_schema())
#> {'type': 'array', 'items': {'type': 'integer'}}
```

Note that this API is provisional and may change before the final release of Pydantic V2.

### Required, Optional, and Nullable fields

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

## Other changes

* `GetterDict` has been removed, as it was just an implementation detail for `orm_mode`, which has been removed.
