# Pydantic V2 Pre Release

<aside class="blog" markdown>
![Terrence Dorsey](../img/terrencedorsey.jpg)
<div markdown>
  **Terrence Dorsey & Samuel Colvin** &bull;&nbsp;
  [:simple-github:](https://github.com/pydantic) &bull;&nbsp;
  [:material-twitter:](https://twitter.com/pydantic) &bull;&nbsp;
  :octicons-calendar-24: April 3, 2023 &bull;&nbsp;
  :octicons-clock-24: 8 min read
</div>
</aside>

---

We're excited to announce the first alpha release of Pydantic V2!

This first Pydantic V2 alpha is no April Fool's joke &mdash; for a start we missed our April 1st target date :cry:.
After a year's work, we invite you to explore the improvements we've made and give us your feedback.
We look forward to hearing your thoughts and working together to improve the library.

For many of you, Pydantic is already a key part of your Python toolkit and needs no introduction &mdash;
we hope you'll find the improvements and additions in Pydantic V2 useful.

If you're new to Pydantic: Pydantic is an open-source Python library that provides powerful data parsing and validation &mdash;
including type coercion and useful error messages when typing issues arise &mdash; and settings management capabilities.
See [the docs](../index.md) for examples of Pydantic at work.

## Getting started with the Pydantic V2 alpha

Your feedback will be a critical part of ensuring that we have made the right tradeoffs with the API changes in V2.

To get started with the Pydantic V2 alpha, install it from PyPI.
We recommend using a virtual environment to isolate your testing environment:

```bash
pip install --pre -U "pydantic>=2.0a1"
```

Note that there are still some rough edges and incomplete features, and while trying out the Pydantic V2 alpha releases you may experience errors.
We encourage you to try out the alpha releases in a test environment and not in production.
Some features are still in development, and we will continue to make changes to the API.

If you do encounter any issues, please [create an issue in GitHub](https://github.com/pydantic/pydantic/issues) using the `bug V2` label.
This will help us to actively monitor and track errors, and to continue to improve the library’s performance.

This will be the first of several upcoming alpha releases. As you evaluate our changes and enhancements,
we encourage you to share your feedback with us.

Please let us know:

* If you don't like the changes, so we can make sure Pydantic remains a library you enjoy using.
* If this breaks your usage of Pydantic so we can fix it, or at least describe a migration path.

Thank you for your support, and we look forward to your feedback.

---

## Headlines

Here are some of the most interesting new features in the current Pydantic V2 alpha release.
For background on plans behind these features, see the earlier [Pydantic V2 Plan](pydantic-v2.md) blog post.

The biggest change to Pydantic V2 is [`pydantic-core`](https://github.com/pydantic/pydantic-core) &mdash;
all validation logic has been rewritten in Rust and moved to a separate package, `pydantic-core`.
This has a number of big advantages:

* **Performance** - Pydantic V2 is 5-50x faster than Pydantic V1.
* **Safety & maintainability** - We've made changes to the architecture that we think will help us maintain Pydantic V2 with far fewer bugs in the long term.

With the use of `pydantic-core`, the majority of the logic in the Pydantic library is dedicated to generating
"pydantic core schema" &mdash; the schema used define the behaviour of the new, high-performance `pydantic-core` validators and serializers.

### Ready for experimentation

* **BaseModel** - the core of validation in Pydantic V1 remains, albeit with new method names.
* **Dataclasses** - Pydantic dataclasses are improved and ready to test.
* **Serialization** - dumping/serialization/marshalling is significantly more flexible, and ready to test.
* **Strict mode** - one of the biggest additions in Pydantic V2 is strict mode, which is ready to test.
* **JSON Schema** - generation of JSON Schema is much improved and ready to test.
* **Generic Models** - are much improved and ready to test.
* **Recursive Models** - and validation of recursive data structures is much improved and ready to test.
* **Custom Types** - custom types have a new interface and are ready to test.
* **Custom Field Modifiers** - used via `Annotated[]` are working and in use in Pydantic itself.
* **Validation without a BaseModel** - the new `TypeAdapter` class allows validation without the need for a `BaseModel` class, and it's ready to test.
* **TypedDict** - we now have full support for `TypedDict` via `TypeAdapter`, it's ready to test.

### Still under construction

* **Documentation** - we're working hard on full documentation for V2, but it's not ready yet.
* **Conversion Table** - a big addition to the documentation will be a conversion table showing how types are coerced, this is a WIP.
* **BaseSettings** - `BaseSettings` will move to a separate `pydantic-settings` package, it's not yet ready to test.
  **Notice:** since `pydantic-settings` is not yet ready to release, there's no support for `BaseSettings` in the first alpha release.
* **validate_arguments** - the `validate_arguments` decorator remains and is working, but hasn't been updated yet.
* **Hypothesis Plugin** - the Hypothesis plugin is yet to be updated.
* **computed fields** - we know a lot of people are waiting for this, we will include it in Pydantic V2.
* **Error messages** - could use some love, and links to docs in error messages are still to be added.
* **Migration Guide** - we have some pointers below, but this needs completing.

## Migration Guide

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

* `allow_mutation` — this has been removed. You should be able to use [frozen](../api/config.md#pydantic.config.ConfigDict) equivalently (inverse of current use).
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
#> {'items': {'type': 'integer'}, 'type': 'array'}
```

Note that this API is provisional and may change before the final release of Pydantic V2.
