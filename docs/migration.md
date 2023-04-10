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
  `@model_serializer`, and `__pydantic_modify_json_schema__`. You can see an example of this
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

* Raising a `TypeError` inside a validator no longer produces a `ValidationError`, but just raises the `TypeError` directly.
  This was necessary to prevent certain common bugs (such as calling functions with invalid signatures) from
  being unintentionally converted into `ValidationError` and displayed to users.
  If you really want `TypeError` to be converted to a `ValidationError` you should use a `try: except:` block that will catch it and do the conversion.
* `each_item` validators are deprecated and should be replaced with a type annotation using `Annotated` to apply a validator
  or with a validator that operates on all items at the top level.
* Changes to `@validator`-decorated function signatures.
* The `stricturl` type has been removed.
* Root validators can no longer be run with `skip_on_failure=False`.

### Changes to Validation of specific types

* Integers outside the valid range of 64 bit integers will cause `ValidationError`s during parsing.
  To work around this, use an `IsInstance` validator (more details to come).
* Subclasses of built-ins won't validate into their subclass types; you'll need to use an `IsInstance` validator to validate these types.

### Changes to Generic models

* While it does not raise an error at runtime yet, subclass checks for parametrized generics should no longer be used.
  These will result in `TypeError`s and we can't promise they will work forever. However, it will be okay to do subclass checks against _non-parametrized_ generic models

### Other changes

* `GetterDict` has been removed, as it was just an implementation detail for `orm_mode`, which has been removed.

### AnalyzedType

Pydantic V1 didn't have good support for validation or serializing non-`BaseModel`.
To work with them you had to create a "root" model or use the utility functions in `pydantic.tools` (`parse_obj_as` and `schema_of`).
In Pydantic V2 this is _a lot_ easier: the `AnalyzedType` class lets you build an object that behaves almost like a `BaseModel` class which you can use for a lot of the use cases of root models and as a complete replacement for `parse_obj_as` and `schema_of`.

```python
from typing import List
from pydantic import AnalyzedType

validator = AnalyzedType(List[int])
assert validator.validate_python(['1', '2', '3']) == [1, 2, 3]
print(validator.json_schema())
# {'type': 'array', 'items': {'type': 'integer'}}
```

Note that this API is provisional and may change before the final release of Pydantic V2.
